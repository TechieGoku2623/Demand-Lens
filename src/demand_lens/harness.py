"""Checks for censored stockouts and intermittent gaps."""

from __future__ import annotations

import asyncio
import sys

from .engine import DemandLens
from .exceptions import EngineKernelException


async def _checks() -> list[str]:
    failures: list[str] = []
    lens = DemandLens()
    steady = await lens.run(
        [
            {"sku": "steady", "day": 1, "units": 10, "stockout": False},
            {"sku": "steady", "day": 2, "units": 10, "stockout": False},
            {"sku": "steady", "day": 3, "units": 10, "stockout": False},
        ]
    )
    row = steady["forecasts"][0]
    if row["per_period"] != 10.0 or row["intermittent"]:
        failures.append(f"steady {row}")
    censored = await lens.run(
        [
            {"sku": "a", "day": 1, "units": 9, "stockout": False},
            {"sku": "a", "day": 2, "units": 0, "stockout": True},
            {"sku": "a", "day": 3, "units": 9, "stockout": False},
        ]
    )
    cens = censored["forecasts"][0]
    if cens["interval"] != 1.0 or cens["censored_days"] != 1:
        failures.append(f"censored {cens}")
    lumpy = await lens.run(
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
    lump = lumpy["forecasts"][0]
    if (
        lump["interval"] != 1.6
        or not lump["intermittent"]
        or lump["per_period"] != 5.625
    ):
        failures.append(f"lumpy {lump}")
    try:
        await lens.run([{"sku": "c", "day": 1, "units": -1, "stockout": False}])
    except EngineKernelException:
        pass
    else:
        failures.append("negative units did not raise")
    try:
        await lens.run([{"sku": "c", "day": 1, "units": 2, "stockout": True}])
    except EngineKernelException:
        pass
    else:
        failures.append("stockout with sales did not raise")
    return failures


def main() -> int:
    failures = asyncio.run(_checks())
    if failures:
        print("\n".join(failures))
        return 1
    print("demand-lens checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
