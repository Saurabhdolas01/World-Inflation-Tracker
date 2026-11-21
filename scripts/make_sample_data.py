#!/usr/bin/env python3
"""
Generate fixture data shaped exactly like the real World Bank / IMF API
responses, so build_data.py (and the front end) can be developed and tested
without live network access. This is NOT real inflation data -- it's
pseudo-random but stable (seeded), spanning a representative set of
countries across every region so the Map, Rankings, Compare, and Country
Detail views all have something realistic to render.

Run this, then `python build_data.py`, to get a working data/processed/
without touching the live APIs. The GitHub Action replaces this with
scripts/fetch_data.py against the real endpoints.
"""
import json
import random
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
SAMPLE_DATE = "2026-11-21"

# (iso3, name, World Bank region, lat, lon, income level) -- a representative
# ~70-country spread across every region World Bank reports on. The real
# fetch pulls the full ~190; this is a development fixture, not the full list.
COUNTRIES = [
    ("USA", "United States", "North America", 38.9, -77.0, "High income"),
    ("CAN", "Canada", "North America", 45.4, -75.7, "High income"),
    ("MEX", "Mexico", "Latin America & Caribbean", 19.4, -99.1, "Upper middle income"),
    ("BRA", "Brazil", "Latin America & Caribbean", -15.8, -47.9, "Upper middle income"),
    ("ARG", "Argentina", "Latin America & Caribbean", -34.6, -58.4, "Upper middle income"),
    ("CHL", "Chile", "Latin America & Caribbean", -33.4, -70.6, "High income"),
    ("COL", "Colombia", "Latin America & Caribbean", 4.6, -74.1, "Upper middle income"),
    ("PER", "Peru", "Latin America & Caribbean", -12.0, -77.0, "Upper middle income"),
    ("VEN", "Venezuela, RB", "Latin America & Caribbean", 10.5, -66.9, "Upper middle income"),
    ("ECU", "Ecuador", "Latin America & Caribbean", -0.2, -78.5, "Upper middle income"),
    ("BOL", "Bolivia", "Latin America & Caribbean", -16.5, -68.1, "Lower middle income"),
    ("CUB", "Cuba", "Latin America & Caribbean", 23.1, -82.4, "Upper middle income"),
    ("GBR", "United Kingdom", "Europe & Central Asia", 51.5, -0.1, "High income"),
    ("DEU", "Germany", "Europe & Central Asia", 52.5, 13.4, "High income"),
    ("FRA", "France", "Europe & Central Asia", 48.9, 2.3, "High income"),
    ("ITA", "Italy", "Europe & Central Asia", 41.9, 12.5, "High income"),
    ("ESP", "Spain", "Europe & Central Asia", 40.4, -3.7, "High income"),
    ("NLD", "Netherlands", "Europe & Central Asia", 52.1, 4.3, "High income"),
    ("CHE", "Switzerland", "Europe & Central Asia", 46.9, 7.4, "High income"),
    ("SWE", "Sweden", "Europe & Central Asia", 59.3, 18.1, "High income"),
    ("NOR", "Norway", "Europe & Central Asia", 59.9, 10.8, "High income"),
    ("POL", "Poland", "Europe & Central Asia", 52.2, 21.0, "High income"),
    ("UKR", "Ukraine", "Europe & Central Asia", 50.5, 30.5, "Lower middle income"),
    ("RUS", "Russian Federation", "Europe & Central Asia", 55.8, 37.6, "Upper middle income"),
    ("TUR", "Turkiye", "Europe & Central Asia", 39.9, 32.9, "Upper middle income"),
    ("GRC", "Greece", "Europe & Central Asia", 38.0, 23.7, "High income"),
    ("PRT", "Portugal", "Europe & Central Asia", 38.7, -9.1, "High income"),
    ("ROU", "Romania", "Europe & Central Asia", 44.4, 26.1, "High income"),
    ("CZE", "Czechia", "Europe & Central Asia", 50.1, 14.4, "High income"),
    ("KAZ", "Kazakhstan", "Europe & Central Asia", 51.2, 71.4, "Upper middle income"),
    ("CHN", "China", "East Asia & Pacific", 39.9, 116.4, "Upper middle income"),
    ("JPN", "Japan", "East Asia & Pacific", 35.7, 139.7, "High income"),
    ("KOR", "Korea, Rep.", "East Asia & Pacific", 37.6, 127.0, "High income"),
    ("IDN", "Indonesia", "East Asia & Pacific", -6.2, 106.8, "Upper middle income"),
    ("VNM", "Vietnam", "East Asia & Pacific", 21.0, 105.8, "Lower middle income"),
    ("PHL", "Philippines", "East Asia & Pacific", 14.6, 121.0, "Lower middle income"),
    ("THA", "Thailand", "East Asia & Pacific", 13.8, 100.5, "Upper middle income"),
    ("MYS", "Malaysia", "East Asia & Pacific", 3.1, 101.7, "Upper middle income"),
    ("SGP", "Singapore", "East Asia & Pacific", 1.35, 103.8, "High income"),
    ("AUS", "Australia", "East Asia & Pacific", -35.3, 149.1, "High income"),
    ("NZL", "New Zealand", "East Asia & Pacific", -41.3, 174.8, "High income"),
    ("MMM", "Myanmar", "East Asia & Pacific", 19.8, 96.1, "Lower middle income"),
    ("KHM", "Cambodia", "East Asia & Pacific", 11.6, 104.9, "Lower middle income"),
    ("IND", "India", "South Asia", 28.6, 77.2, "Lower middle income"),
    ("PAK", "Pakistan", "South Asia", 33.7, 73.1, "Lower middle income"),
    ("BGD", "Bangladesh", "South Asia", 23.8, 90.4, "Lower middle income"),
    ("LKA", "Sri Lanka", "South Asia", 6.9, 79.9, "Lower middle income"),
    ("NPL", "Nepal", "South Asia", 27.7, 85.3, "Lower middle income"),
    ("AFG", "Afghanistan", "South Asia", 34.5, 69.2, "Low income"),
    ("SAU", "Saudi Arabia", "Middle East & North Africa", 24.7, 46.7, "High income"),
    ("ARE", "United Arab Emirates", "Middle East & North Africa", 24.5, 54.4, "High income"),
    ("EGY", "Egypt, Arab Rep.", "Middle East & North Africa", 30.0, 31.2, "Lower middle income"),
    ("IRN", "Iran, Islamic Rep.", "Middle East & North Africa", 35.7, 51.4, "Lower middle income"),
    ("IRQ", "Iraq", "Middle East & North Africa", 33.3, 44.4, "Upper middle income"),
    ("ISR", "Israel", "Middle East & North Africa", 31.8, 35.2, "High income"),
    ("JOR", "Jordan", "Middle East & North Africa", 31.9, 35.9, "Upper middle income"),
    ("LBN", "Lebanon", "Middle East & North Africa", 33.9, 35.5, "Upper middle income"),
    ("MAR", "Morocco", "Middle East & North Africa", 34.0, -6.8, "Lower middle income"),
    ("TUN", "Tunisia", "Middle East & North Africa", 36.8, 10.2, "Lower middle income"),
    ("NGA", "Nigeria", "Sub-Saharan Africa", 9.1, 7.4, "Lower middle income"),
    ("ZAF", "South Africa", "Sub-Saharan Africa", -25.7, 28.2, "Upper middle income"),
    ("KEN", "Kenya", "Sub-Saharan Africa", -1.3, 36.8, "Lower middle income"),
    ("ETH", "Ethiopia", "Sub-Saharan Africa", 9.0, 38.7, "Low income"),
    ("GHA", "Ghana", "Sub-Saharan Africa", 5.6, -0.2, "Lower middle income"),
    ("TZA", "Tanzania", "Sub-Saharan Africa", -6.8, 39.3, "Lower middle income"),
    ("UGA", "Uganda", "Sub-Saharan Africa", 0.3, 32.6, "Low income"),
    ("SDN", "Sudan", "Sub-Saharan Africa", 15.6, 32.5, "Low income"),
    ("AGO", "Angola", "Sub-Saharan Africa", -8.8, 13.2, "Lower middle income"),
    ("ZWE", "Zimbabwe", "Sub-Saharan Africa", -17.8, 31.0, "Lower middle income"),
    ("SEN", "Senegal", "Sub-Saharan Africa", 14.7, -17.5, "Lower middle income"),
    ("CMR", "Cameroon", "Sub-Saharan Africa", 3.9, 11.5, "Lower middle income"),
    ("CIV", "Cote d'Ivoire", "Sub-Saharan Africa", 5.3, -4.0, "Lower middle income"),
]

# A few World Bank aggregate "region" entries that should get filtered out
# by build_data.py's parse_country_meta -- included here specifically to
# exercise that filtering logic.
AGGREGATES = [
    ("WLD", "World"), ("EUU", "European Union"), ("HIC", "High income"),
    ("OED", "OECD members"), ("ECS", "Europe & Central Asia"),
]

MAJOR_ECONOMIES = [
    "ARG", "AUS", "BRA", "CAN", "CHN", "FRA", "DEU", "IND", "IDN", "ITA",
    "JPN", "MEX", "SAU", "ZAF", "KOR", "TUR", "GBR", "USA", "PAK", "SGP",
    "CHE", "NGA", "EGY", "VNM", "THA", "POL",
]

INDICATOR_RANGES = {
    # key: (floor, ceiling, year-to-year noise)
    "cpi_inflation": (-1.0, 50.0, 0.9),
    "gdp_growth": (-6.0, 9.0, 1.1),
    "unemployment": (2.0, 32.0, 0.5),
    "fx_rate": (0.9, 1800.0, 0.0),  # fx handled specially: slow drift, not mean-reverting
    "current_account": (-10.0, 10.0, 0.8),
}

# A handful of countries with persistently/visibly higher inflation, so the
# fixture has a believable spread of outliers (matching what the real data
# will look like) instead of every country drifting to the same place.
HIGH_INFLATION_COUNTRIES = {
    "ARG": 85, "VEN": 70, "ZWE": 55, "TUR": 42, "LBN": 60, "SDN": 50,
    "IRN": 35, "EGY": 22, "NGA": 20, "GHA": 18, "ETH": 17, "PAK": 16,
}


def make_country_meta():
    records = []
    for iso3, name, region, lat, lon, income in COUNTRIES:
        records.append({
            "id": iso3,
            "iso2Code": iso3[:2],
            "name": name,
            "region": {"id": region[:3].upper(), "iso2code": "", "value": region},
            "adminregion": {"id": "", "iso2code": "", "value": ""},
            "incomeLevel": {"id": "", "iso2code": "", "value": income},
            "lendingType": {"id": "", "iso2code": "", "value": ""},
            "capitalCity": "",
            "longitude": str(lon),
            "latitude": str(lat),
        })
    for iso3, name in AGGREGATES:
        records.append({
            "id": iso3,
            "iso2Code": iso3[:2],
            "name": name,
            "region": {"id": "NA", "iso2code": "NA", "value": "Aggregates"},
            "adminregion": {"id": "", "iso2code": "", "value": ""},
            "incomeLevel": {"id": "NA", "iso2code": "NA", "value": "Aggregates"},
            "lendingType": {"id": "", "iso2code": "", "value": ""},
            "capitalCity": "",
            "longitude": "",
            "latitude": "",
        })
    meta = {"page": 1, "pages": 1, "per_page": 400, "total": len(records)}
    return [meta, records]


def make_indicator(key, start_year=2000, end_year=2026, seed_offset=0):
    floor, ceiling, noise = INDICATOR_RANGES[key]
    records = []
    for iso3, name, region, *_rest in COUNTRIES:
        rng = random.Random(f"{key}-{iso3}-{seed_offset}")

        if key == "fx_rate":
            value = rng.uniform(0.9, 1800.0)
        elif key == "cpi_inflation":
            # mean-reverting around a per-country baseline, so 26 years of
            # noise doesn't drift to nonsense -- this is what makes the
            # fixture map/rankings look like plausible data during review.
            baseline = HIGH_INFLATION_COUNTRIES.get(iso3, rng.uniform(1.0, 7.0))
        elif key == "gdp_growth":
            baseline = rng.uniform(0.5, 5.0)
        elif key == "unemployment":
            baseline = rng.uniform(3.0, 14.0)
        else:  # current_account
            baseline = rng.uniform(-4.0, 4.0)

        value = baseline if key != "fx_rate" else value
        for year in range(start_year, end_year + 1):
            if key == "fx_rate":
                value *= 1 + rng.uniform(-0.01, 0.02)
            else:
                # pull back toward baseline each step, then add noise
                value += (baseline - value) * 0.25 + rng.uniform(-noise, noise)
                value = max(floor, min(ceiling, value))
            # skip some recent years for a few countries, to exercise "latest data may lag" handling
            if year > end_year - 1 and rng.random() < 0.08:
                continue
            records.append({
                "indicator": {"id": "X", "value": key},
                "country": {"id": iso3[:2], "value": name},
                "countryiso3code": iso3,
                "date": str(year),
                "value": round(value, 3),
                "unit": "", "obs_status": "", "decimal": 1,
            })
    meta = {"page": 1, "pages": 1, "per_page": 20000, "total": len(records)}
    return [meta, records]


def make_imf_monthly(start_year=2023, end_year=2026):
    out = {}
    for iso3 in MAJOR_ECONOMIES:
        rng = random.Random(f"imf-{iso3}")
        index = rng.uniform(90, 140)
        obs = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                if year == end_year and month > 10:
                    break
                index *= 1 + rng.uniform(-0.015, 0.03)
                obs.append({"@TIME_PERIOD": f"{year}-{month:02d}", "@OBS_VALUE": f"{index:.3f}"})
        out[iso3] = {
            "CompactData": {
                "DataSet": {
                    "Series": {
                        "@FREQ": "M", "@REF_AREA": iso3, "@INDICATOR": "PCPI_IX",
                        "Obs": obs,
                    }
                }
            }
        }
    return out


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    (RAW_DIR / f"worldbank_country_meta_{SAMPLE_DATE}.json").write_text(
        json.dumps(make_country_meta(), indent=2)
    )

    for key in INDICATOR_RANGES:
        (RAW_DIR / f"worldbank_{key}_{SAMPLE_DATE}.json").write_text(
            json.dumps(make_indicator(key), indent=2)
        )

    (RAW_DIR / f"imf_cpi_monthly_{SAMPLE_DATE}.json").write_text(
        json.dumps(make_imf_monthly(), indent=2)
    )

    print(f"[sample] wrote fixture data for {len(COUNTRIES)} countries + {len(AGGREGATES)} aggregates to {RAW_DIR}")
    print("Next: python build_data.py")


if __name__ == "__main__":
    main()
