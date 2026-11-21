"""
Unit tests for the build script's parsing and metric calculations, checked
against hand-computed values. Run with: python -m pytest tests/ -v
(or: python tests/test_metrics.py -- it also runs stand-alone)
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from build_data import index_series_to_yoy, latest_and_change, parse_country_meta, parse_world_bank_indicator


class TestYoYFromIndex(unittest.TestCase):
    def test_simple_yoy(self):
        # Index goes from 100 in Jan 2024 to 105 in Jan 2025 -> +5.0% YoY
        points = [
            {"month": "2024-01", "index": 100.0},
            {"month": "2025-01", "index": 105.0},
        ]
        out = index_series_to_yoy(points)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0]["yoy_pct"], 5.0, places=2)
        self.assertEqual(out[0]["month"], "2025-01")

    def test_no_prior_year_is_skipped(self):
        points = [{"month": "2024-06", "index": 100.0}]
        out = index_series_to_yoy(points)
        self.assertEqual(out, [])

    def test_negative_inflation(self):
        points = [
            {"month": "2024-03", "index": 110.0},
            {"month": "2025-03", "index": 108.9},
        ]
        out = index_series_to_yoy(points)
        self.assertAlmostEqual(out[0]["yoy_pct"], -1.0, places=1)

    def test_multiple_months_only_pairs_with_match(self):
        points = [
            {"month": "2023-05", "index": 100.0},
            {"month": "2024-05", "index": 102.0},
            {"month": "2024-06", "index": 103.0},  # no 2023-06 -> skipped
            {"month": "2025-05", "index": 104.04},
        ]
        out = index_series_to_yoy(points)
        months = {o["month"] for o in out}
        self.assertIn("2024-05", months)
        self.assertNotIn("2024-06", months)
        self.assertIn("2025-05", months)


class TestLatestAndChange(unittest.TestCase):
    def test_empty_series(self):
        self.assertEqual(latest_and_change([]), (None, None))

    def test_single_point_has_no_change(self):
        latest, change = latest_and_change([{"year": 2024, "value": 5.0}])
        self.assertEqual(latest["value"], 5.0)
        self.assertIsNone(change)

    def test_change_is_latest_minus_prev(self):
        series = [{"year": 2023, "value": 4.0}, {"year": 2024, "value": 5.5}]
        latest, change = latest_and_change(series)
        self.assertEqual(latest["year"], 2024)
        self.assertAlmostEqual(change, 1.5, places=2)


class TestParseCountryMeta(unittest.TestCase):
    def _write(self, payload):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(payload, f)
        f.close()
        return Path(f.name)

    def test_aggregates_are_dropped(self):
        payload = [
            {"page": 1},
            [
                {
                    "id": "IND", "name": "India",
                    "region": {"id": "SAS", "value": "South Asia"},
                    "incomeLevel": {"value": "Lower middle income"},
                    "longitude": "77.2", "latitude": "28.6",
                },
                {
                    "id": "WLD", "name": "World",
                    "region": {"id": "NA", "value": "Aggregates"},
                    "incomeLevel": {"value": "Aggregates"},
                    "longitude": "", "latitude": "",
                },
            ],
        ]
        path = self._write(payload)
        meta = parse_country_meta(path)
        self.assertIn("IND", meta)
        self.assertNotIn("WLD", meta)
        self.assertEqual(meta["IND"]["region"], "Asia-Pacific")  # South Asia -> Asia-Pacific
        self.assertAlmostEqual(meta["IND"]["lat"], 28.6)

    def test_missing_lat_lon_is_none_not_error(self):
        payload = [
            {"page": 1},
            [{
                "id": "XYZ", "name": "Nowhere",
                "region": {"id": "ECS", "value": "Europe & Central Asia"},
                "incomeLevel": {"value": "High income"},
                "longitude": "", "latitude": "",
            }],
        ]
        path = self._write(payload)
        meta = parse_country_meta(path)
        self.assertIsNone(meta["XYZ"]["lat"])
        self.assertIsNone(meta["XYZ"]["lon"])


class TestParseWorldBankIndicator(unittest.TestCase):
    def test_sorts_by_year_and_drops_nulls(self):
        payload = [
            {"page": 1},
            [
                {"countryiso3code": "IND", "date": "2023", "value": 5.6},
                {"countryiso3code": "IND", "date": "2021", "value": 6.2},
                {"countryiso3code": "IND", "date": "2022", "value": None},  # should be dropped
            ],
        ]
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(payload, f)
        f.close()
        series = parse_world_bank_indicator(Path(f.name))
        self.assertEqual([p["year"] for p in series["IND"]], [2021, 2023])


if __name__ == "__main__":
    unittest.main()
