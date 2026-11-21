#!/usr/bin/env python3
"""
Turn the raw API dumps in data/raw/ into the processed JSON the site reads:
data/processed/metrics.json

Assumes World Bank's documented response shapes:
  /v2/country              -> [ {page,...}, [ {id, name, region:{id,value},
                                 incomeLevel:{id,value}, longitude,
                                 latitude, ...}, ... ] ]
  /v2/country/all/indicator/{code} -> [ {page,...}, [ {indicator, country,
                                 countryiso3code, date, value, ...}, ... ] ]

Assumes IMF SDMX-JSON CompactData shape:
  {"CompactData": {"DataSet": {"Series": {"Obs": [ {"@TIME_PERIOD":...,
     "@OBS_VALUE":...}, ... ] } } } }
  "Obs" may be a single dict instead of a list when there's only one point,
  and "Series" may be missing entirely if the country/series has no data --
  both are handled below. If the live API shape differs, this is the first
  place to fix.
"""
import json
import sys
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

# World Bank's 7 lending/region buckets collapsed down to the 4 shown in the
# UI. Revisit this if the Rankings stage wants finer regional breakdowns.
REGION_MAP = {
    "North America": "Americas",
    "Latin America & Caribbean": "Americas",
    "Europe & Central Asia": "Europe",
    "East Asia & Pacific": "Asia-Pacific",
    "South Asia": "Asia-Pacific",
    "Middle East & North Africa": "Middle East & Africa",
    "Sub-Saharan Africa": "Middle East & Africa",
}

INDICATOR_KEYS = ["cpi_inflation", "gdp_growth", "unemployment", "fx_rate", "current_account"]


def latest_file(pattern):
    files = sorted(RAW_DIR.glob(pattern))
    if not files:
        return None
    return files[-1]


def parse_country_meta(raw_path):
    """Returns {iso3: {name, region, lat, lon, income_level}}, aggregates dropped."""
    raw = json.loads(raw_path.read_text())
    if not isinstance(raw, list) or len(raw) < 2 or raw[1] is None:
        raise ValueError(f"Unexpected World Bank country response shape in {raw_path}")
    out = {}
    for rec in raw[1]:
        region = (rec.get("region") or {}).get("value", "")
        if region in ("", "Aggregates"):
            continue  # drop World Bank's aggregate "regions" (World, EU, income groups, ...)
        iso3 = rec.get("id")
        try:
            lat = float(rec["latitude"]) if rec.get("latitude") else None
            lon = float(rec["longitude"]) if rec.get("longitude") else None
        except (TypeError, ValueError):
            lat = lon = None
        out[iso3] = {
            "name": rec.get("name"),
            "region": REGION_MAP.get(region, region or "Other"),
            "lat": lat,
            "lon": lon,
            "income_level": (rec.get("incomeLevel") or {}).get("value"),
        }
    return out


def parse_world_bank_indicator(raw_path):
    """Returns {iso3: [{"year": int, "value": float}, ...]} sorted by year."""
    raw = json.loads(raw_path.read_text())
    if not isinstance(raw, list) or len(raw) < 2 or raw[1] is None:
        raise ValueError(f"Unexpected World Bank indicator response shape in {raw_path}")
    by_country = {}
    for rec in raw[1]:
        iso3 = rec.get("countryiso3code")
        value = rec.get("value")
        date = rec.get("date")
        if not iso3 or value is None or not date:
            continue
        by_country.setdefault(iso3, []).append({"year": int(date), "value": round(float(value), 2)})
    for iso3 in by_country:
        by_country[iso3].sort(key=lambda r: r["year"])
    return by_country


def parse_imf_monthly(raw_path):
    """Returns {iso3: [{"month": "YYYY-MM", "index": float}, ...]} sorted."""
    raw = json.loads(raw_path.read_text())
    by_country = {}
    for iso3, payload in raw.items():
        if not payload:
            continue
        try:
            dataset = payload["CompactData"]["DataSet"]
            series = dataset.get("Series")
            if series is None:
                continue
            obs = series.get("Obs", [])
            if isinstance(obs, dict):
                obs = [obs]
            points = []
            for o in obs:
                period = o.get("@TIME_PERIOD")
                value = o.get("@OBS_VALUE")
                if period and value not in (None, ""):
                    points.append({"month": period, "index": float(value)})
            points.sort(key=lambda p: p["month"])
            if points:
                by_country[iso3] = points
        except (KeyError, TypeError, ValueError) as e:
            print(f"[build] WARNING: could not parse IMF data for {iso3}: {e}")
    return by_country


def index_series_to_yoy(points):
    """[{"month","index"}, ...] (monthly, consecutive) -> [{"month","yoy_pct"}, ...]"""
    by_month = {p["month"]: p["index"] for p in points}
    out = []
    for p in points:
        y, m = p["month"].split("-")
        prev_month = f"{int(y) - 1}-{m}"
        if prev_month in by_month and by_month[prev_month]:
            yoy = (p["index"] / by_month[prev_month] - 1) * 100
            out.append({"month": p["month"], "yoy_pct": round(yoy, 2)})
    return out


def latest_and_change(series):
    """series: [{"year","value"}, ...] sorted ascending -> (latest_point, change_vs_prev)."""
    if not series:
        return None, None
    latest = series[-1]
    prev = series[-2] if len(series) > 1 else None
    change = round(latest["value"] - prev["value"], 2) if prev else None
    return latest, change


def build():
    meta_path = latest_file("worldbank_country_meta_*.json")
    if not meta_path:
        print("No World Bank country metadata found. Run scripts/fetch_data.py first.")
        sys.exit(1)
    meta = parse_country_meta(meta_path)

    indicator_series = {}
    indicator_source_files = {}
    for key in INDICATOR_KEYS:
        path = latest_file(f"worldbank_{key}_*.json")
        indicator_source_files[key] = path.name if path else None
        if not path:
            print(f"[build] WARNING: no raw data for indicator '{key}', skipping it")
            indicator_series[key] = {}
            continue
        indicator_series[key] = parse_world_bank_indicator(path)

    imf_path = latest_file("imf_cpi_monthly_*.json")
    monthly_index = parse_imf_monthly(imf_path) if imf_path else {}
    monthly_yoy = {iso3: index_series_to_yoy(pts) for iso3, pts in monthly_index.items()}

    countries_out = []
    inflation_values = []  # (iso3, value) for ranking + world summary
    regional_values = {}   # region -> [value, ...]

    for iso3, info in meta.items():
        cpi_series = indicator_series.get("cpi_inflation", {}).get(iso3, [])
        if not cpi_series:
            continue  # no inflation data at all -> not worth listing

        latest_cpi, change_cpi = latest_and_change(cpi_series)

        indicators_out = {}
        for key in INDICATOR_KEYS:
            series = indicator_series.get(key, {}).get(iso3, [])
            latest, _ = latest_and_change(series)
            indicators_out[key] = latest["value"] if latest else None

        entry = {
            "name": info["name"],
            "iso3": iso3,
            "region": info["region"],
            "lat": info["lat"],
            "lon": info["lon"],
            "income_level": info["income_level"],
            "inflation_history": cpi_series,
            "monthly_yoy": monthly_yoy.get(iso3, []),
            "latest_inflation": latest_cpi["value"] if latest_cpi else None,
            "latest_year": latest_cpi["year"] if latest_cpi else None,
            "change_vs_prev_year": change_cpi,
            "indicators": indicators_out,
        }
        countries_out.append(entry)

        inflation_values.append((iso3, latest_cpi["value"]))
        regional_values.setdefault(info["region"], []).append(latest_cpi["value"])

    countries_out.sort(key=lambda c: (c["latest_inflation"] is None, c["latest_inflation"]), reverse=True)
    for i, c in enumerate(countries_out, start=1):
        c["rank"] = i

    values = [v for _, v in inflation_values]
    ranked = sorted(inflation_values, key=lambda t: t[1])
    name_by_iso3 = {c["iso3"]: c["name"] for c in countries_out}

    world_summary = {
        "average_pct": round(sum(values) / len(values), 2) if values else None,
        "median_pct": round(sorted(values)[len(values) // 2], 2) if values else None,
        "lowest": (
            {"iso3": ranked[0][0], "name": name_by_iso3[ranked[0][0]], "value": ranked[0][1]}
            if ranked else None
        ),
        "highest": (
            {"iso3": ranked[-1][0], "name": name_by_iso3[ranked[-1][0]], "value": ranked[-1][1]}
            if ranked else None
        ),
        "above_10_pct_count": sum(1 for v in values if v > 10),
        "countries_with_data": len(values),
        "regional_average_pct": {
            region: round(sum(vals) / len(vals), 2) for region, vals in regional_values.items()
        },
    }

    output = {
        "generated_from": {
            "country_meta": meta_path.name,
            **{f"{key}_raw": indicator_source_files.get(key) for key in INDICATOR_KEYS},
            "imf_raw": imf_path.name if imf_path else None,
        },
        "world_summary": world_summary,
        "countries": countries_out,
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "metrics.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"[build] wrote {out_path} ({len(countries_out)} countries)")


if __name__ == "__main__":
    build()
