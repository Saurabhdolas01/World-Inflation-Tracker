#!/usr/bin/env python3
"""
Fetch raw data for the tracker:
  1. World Bank API -- country metadata (name, region, lat/lon) for every
     reporting country, used to drop aggregates ("World", "Euro area", ...)
     from the per-country list and to place markers on the globe.
  2. World Bank API -- five annual indicators for every country: CPI
     inflation, GDP growth, unemployment, FX rate vs USD, current account.
  3. IMF IFS API -- monthly CPI index, for the curated MAJOR_ECONOMIES list
     only (IMF doesn't cover every country), used for the Compare view's
     monthly trend chart.

Every response is saved verbatim under data/raw/ with the fetch date, so
numbers can always be traced back to source and re-derived later.

This script was written against each API's publicly documented, stable
structure. It has NOT been run against the live endpoints from the
environment that authored it (sandboxed, no general internet access). Run it
for real (locally, or via the GitHub Action) and check data/raw/*.json
before trusting build_data.py's output. If a response shape differs from
what's assumed here, the --debug flag dumps the first raw payload so the
parsing can be adjusted.
"""
import argparse
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from countries import MAJOR_ECONOMIES

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
TODAY = datetime.date.today().isoformat()

# Annual indicators pulled for every country. Keys are also used as the
# output filename stem (worldbank_<key>_<date>.json).
INDICATORS = {
    "cpi_inflation": "FP.CPI.TOTL.ZG",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "fx_rate": "PA.NUS.FCRF",
    "current_account": "BN.CAB.XOKA.GD.ZS",
}

COUNTRY_META_URL = "https://api.worldbank.org/v2/country?format=json&per_page=400"

WORLD_BANK_INDICATOR_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/{indicator}"
    "?format=json&date={start}:{end}&per_page=20000"
)

# IMF International Financial Statistics, monthly CPI index (not seasonally
# adjusted). Series code PCPI_IX. SDMX JSON, no API key required.
IMF_URL = (
    "https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/"
    "M.{country}.PCPI_IX?startPeriod={start}&endPeriod={end}"
)


def fetch_json(url, retries=3, timeout=45):
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "world-inflation-tracker/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last_err}")


def fetch_country_meta(debug=False):
    print(f"[world bank] GET {COUNTRY_META_URL}")
    data = fetch_json(COUNTRY_META_URL)
    if debug:
        print(json.dumps(data, indent=2)[:2000])
    out_path = RAW_DIR / f"worldbank_country_meta_{TODAY}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"[world bank] saved -> {out_path}")
    return out_path


def fetch_world_bank_indicator(key, code, start_year, end_year, debug=False):
    url = WORLD_BANK_INDICATOR_URL.format(indicator=code, start=start_year, end=end_year)
    print(f"[world bank] GET {url}")
    data = fetch_json(url)
    if debug:
        print(json.dumps(data, indent=2)[:2000])
    out_path = RAW_DIR / f"worldbank_{key}_{TODAY}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"[world bank] saved -> {out_path}")
    return out_path


def fetch_imf_monthly(start_year, end_year, debug=False):
    results = {}
    for code in MAJOR_ECONOMIES:
        url = IMF_URL.format(country=code, start=start_year, end=end_year)
        print(f"[imf] GET {url}")
        try:
            data = fetch_json(url)
            results[code] = data
            if debug:
                print(json.dumps(data, indent=2)[:1000])
        except RuntimeError as e:
            print(f"[imf] WARNING: could not fetch {code}: {e}")
            results[code] = None
        time.sleep(0.5)  # be polite to the API
    out_path = RAW_DIR / f"imf_cpi_monthly_{TODAY}.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"[imf] saved -> {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=datetime.date.today().year)
    parser.add_argument("--skip-monthly", action="store_true", help="Skip the IMF monthly fetch")
    parser.add_argument("--only", help="Comma-separated indicator keys to fetch (default: all)")
    parser.add_argument("--debug", action="store_true", help="Print a snippet of each raw response")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    fetch_country_meta(debug=args.debug)

    keys = args.only.split(",") if args.only else list(INDICATORS.keys())
    for key in keys:
        if key not in INDICATORS:
            print(f"Unknown indicator key: {key} (known: {list(INDICATORS)})")
            sys.exit(1)
        fetch_world_bank_indicator(key, INDICATORS[key], args.start_year, args.end_year, debug=args.debug)

    if not args.skip_monthly:
        fetch_imf_monthly(args.start_year, args.end_year, debug=args.debug)

    print("Done. Next: python scripts/build_data.py")


if __name__ == "__main__":
    main()
