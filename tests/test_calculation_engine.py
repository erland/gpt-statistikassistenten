import unittest

from scripts.calculation_engine import (
    CalculationError,
    absolute_change,
    index_series,
    per_capita,
    percent_change,
    share,
)


def result(title, measure_id, unit, statistic_type, rows, frequency="annual", geo_id="geo", time_id="time"):
    geos = sorted({r[geo_id] for r in rows})
    times = sorted({r[time_id] for r in rows})
    return {
        "dataset": {"title": title, "publisher": "Test", "subject": "test", "frequency": frequency},
        "dimensions": [
            {"id": time_id, "kind": "time", "label": "Tid", "values": [{"key": t, "label": t} for t in times]},
            {"id": geo_id, "kind": "geography", "label": "Geografi", "values": [{"key": g, "label": g} for g in geos]},
        ],
        "measures": [{"id": measure_id, "label": measure_id, "statistic_type": statistic_type, "unit": unit}],
        "observations": [
            {"dimensions": {time_id: r[time_id], geo_id: r[geo_id]}, "measure": measure_id, "value": r["value"], "status": r.get("status", "observed")}
            for r in rows
        ],
        "provenance": {"source": {"organization": "Test", "dataset": title}, "retrieval": {"verified": True}}
    }


class CalculationEngineTests(unittest.TestCase):
    def setUp(self):
        self.population = result(
            "Population", "population", "persons", "count",
            [{"time": "2024", "geo": "Sundsvall", "value": 100000}, {"time": "2025", "geo": "Sundsvall", "value": 101000}],
        )
        self.crimes = result(
            "Reported crimes", "crimes", "cases", "count",
            [{"time": "2024", "geo": "Sundsvall", "value": 500}, {"time": "2025", "geo": "Sundsvall", "value": 505}],
        )

    def test_absolute_change(self):
        out = absolute_change(self.population, "population", "2024", "2025")
        self.assertEqual(out["observations"][0]["value"], 1000)
        self.assertEqual(out["calculation"]["unit"], "persons")

    def test_percent_change(self):
        out = percent_change(self.population, "population", "2024", "2025")
        self.assertAlmostEqual(out["observations"][0]["value"], 1.0)

    def test_percent_change_rejects_zero_base(self):
        r = result("X", "x", "count", "count", [{"time": "2024", "geo": "A", "value": 0}, {"time": "2025", "geo": "A", "value": 1}])
        with self.assertRaises(CalculationError):
            percent_change(r, "x", "2024", "2025")

    def test_index_series(self):
        out = index_series(self.population, "population", "2024")
        by_period = {o["dimensions"]["time"]: o["value"] for o in out["observations"]}
        self.assertEqual(by_period["2024"], 100.0)
        self.assertEqual(by_period["2025"], 101.0)

    def test_per_capita_matches_period_and_geography(self):
        out = per_capita(self.crimes, "crimes", self.population, "population", scale=100000)
        by_period = {o["dimensions"]["time"]: o["value"] for o in out["observations"]}
        self.assertEqual(by_period["2024"], 500.0)
        self.assertEqual(by_period["2025"], 500.0)

    def test_per_capita_propagates_provisional_status(self):
        pop = result("Population", "population", "persons", "count", [{"time": "2025", "geo": "Sundsvall", "value": 101000, "status": "provisional"}])
        crime = result("Reported crimes", "crimes", "cases", "count", [{"time": "2025", "geo": "Sundsvall", "value": 505}])
        out = per_capita(crime, "crimes", pop, "population")
        self.assertEqual(out["observations"][0]["status"], "provisional")

    def test_per_capita_rejects_period_mismatch(self):
        pop = result("Population", "population", "persons", "count", [{"time": "2024", "geo": "Sundsvall", "value": 100000}])
        crime = result("Reported crimes", "crimes", "cases", "count", [{"time": "2025", "geo": "Sundsvall", "value": 500}])
        with self.assertRaises(CalculationError):
            per_capita(crime, "crimes", pop, "population")

    def test_per_capita_rejects_frequency_mismatch(self):
        monthly = result("Crime", "crimes", "cases", "count", [{"time": "2025-01", "geo": "Sundsvall", "value": 40}], frequency="monthly")
        annual = result("Population", "population", "persons", "count", [{"time": "2025-01", "geo": "Sundsvall", "value": 101000}], frequency="annual")
        with self.assertRaises(CalculationError):
            per_capita(monthly, "crimes", annual, "population")

    def test_share_requires_same_units(self):
        with self.assertRaises(CalculationError):
            share(self.crimes, "crimes", self.population, "population")

    def test_share(self):
        part = result("Part", "value", "SEK", "amount", [{"time": "2025", "geo": "SE", "value": 25}])
        total = result("Total", "value", "SEK", "amount", [{"time": "2025", "geo": "SE", "value": 100}])
        out = share(part, "value", total, "value")
        self.assertEqual(out["observations"][0]["value"], 25.0)

    def test_missing_value_is_not_zero(self):
        r = result("X", "x", "count", "count", [{"time": "2024", "geo": "A", "value": None, "status": "missing"}, {"time": "2025", "geo": "A", "value": 4}])
        with self.assertRaises(CalculationError):
            absolute_change(r, "x", "2024", "2025")


if __name__ == "__main__":
    unittest.main()
