"""Forecast a steady SKU and a lumpy SKU."""

from __future__ import annotations

import asyncio
import logging

from .engine import DemandLens


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = [
        {"sku": "steady", "day": 1, "units": 10, "stockout": False},
        {"sku": "steady", "day": 2, "units": 10, "stockout": False},
        {"sku": "steady", "day": 3, "units": 10, "stockout": False},
        {"sku": "lumpy", "day": 1, "units": 9, "stockout": False},
        {"sku": "lumpy", "day": 2, "units": 0, "stockout": False},
        {"sku": "lumpy", "day": 3, "units": 0, "stockout": False},
        {"sku": "lumpy", "day": 4, "units": 0, "stockout": False},
        {"sku": "lumpy", "day": 5, "units": 9, "stockout": False},
    ]
    report = asyncio.run(DemandLens().run(records))
    logging.getLogger(__name__).info("%s", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
