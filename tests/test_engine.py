"""Unit tests for the intermittent demand lens."""

from __future__ import annotations

import unittest

from demand_lens import DemandLens, EngineKernelException


class DemandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.lens = DemandLens()

    async def test_steady_demand_stays_level(self) -> None:
        report = await self.lens.run(
            [
                {"sku": "steady", "day": 1, "units": 10, "stockout": False},
                {"sku": "steady", "day": 2, "units": 10, "stockout": False},
                {"sku": "steady", "day": 3, "units": 10, "stockout": False},
            ]
        )
        row = report["forecasts"][0]
        self.assertEqual(row["per_period"], 10.0)
        self.assertFalse(row["intermittent"])

    async def test_stockout_does_not_stretch_the_gap(self) -> None:
        report = await self.lens.run(
            [
                {"sku": "a", "day": 1, "units": 9, "stockout": False},
                {"sku": "a", "day": 2, "units": 0, "stockout": True},
                {"sku": "a", "day": 3, "units": 9, "stockout": False},
            ]
        )
        row = report["forecasts"][0]
        self.assertEqual(row["interval"], 1.0)
        self.assertEqual(row["censored_days"], 1)
        self.assertEqual(row["per_period"], 9.0)

    async def test_long_gap_is_intermittent(self) -> None:
        report = await self.lens.run(
            [
                {
                    "sku": "b",
                    "day": day,
                    "units": 9 if day in (1, 5) else 0,
                    "stockout": False,
                }
                for day in range(1, 6)
            ]
        )
        row = report["forecasts"][0]
        self.assertEqual(row["interval"], 1.6)
        self.assertEqual(row["per_period"], 5.625)
        self.assertTrue(row["intermittent"])

    async def test_negative_units_raise(self) -> None:
        with self.assertRaises(EngineKernelException):
            await self.lens.run(
                [{"sku": "c", "day": 1, "units": -1, "stockout": False}]
            )


if __name__ == "__main__":
    unittest.main()
