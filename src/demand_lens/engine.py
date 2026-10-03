"""Forecast intermittent demand without treating a stockout as a zero sale.

Positive sizes and the gaps between them are smoothed separately. A stockout
day is censored: it is counted, and it does not advance the gap. The
published rate is smoothed size divided by smoothed gap.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping

from .exceptions import EngineKernelException

ALPHA = 0.2
INTERMITTENT_GAP = 1.5


class DemandLens:
    """Publish a per-period forecast for each SKU in the batch."""

    def __init__(self, alpha: float = ALPHA) -> None:
        if not 0.0 < alpha <= 1.0:
            raise EngineKernelException("alpha must be in (0, 1]")
        self.alpha = alpha

    async def run(self, records: Iterable[Mapping[str, object]]) -> dict[str, object]:
        rows = list(records)
        if not rows:
            raise EngineKernelException("empty batch")
        grouped: dict[str, list[tuple[int, float, bool]]] = {}
        for row in rows:
            sku = str(row.get("sku", "")).strip()
            if not sku:
                raise EngineKernelException("sku is empty")
            day = row.get("day")
            units = row.get("units")
            stockout = row.get("stockout", False)
            if isinstance(day, bool) or not isinstance(day, int) or day < 1:
                raise EngineKernelException("day must be a positive integer")
            if isinstance(units, bool) or not isinstance(units, (int, float)):
                raise EngineKernelException("units are not finite")
            units_f = float(units)
            if math.isnan(units_f) or math.isinf(units_f) or units_f < 0:
                raise EngineKernelException("units are not finite")
            if not isinstance(stockout, bool):
                raise EngineKernelException("stockout must be boolean")
            if stockout and units_f > 0:
                raise EngineKernelException("a stockout day cannot also record sales")
            grouped.setdefault(sku, []).append((day, units_f, stockout))
        forecasts = [self._sku(sku, grouped[sku]) for sku in sorted(grouped)]
        return {"skus": len(forecasts), "forecasts": forecasts}

    def _sku(self, sku: str, rows: list[tuple[int, float, bool]]) -> dict[str, object]:
        ordered = sorted(rows, key=lambda item: item[0])
        seen: set[int] = set()
        for day, _units, _stockout in ordered:
            if day in seen:
                raise EngineKernelException("duplicate day for sku")
            seen.add(day)
        size_hat = 0.0
        interval_hat = 0.0
        started = False
        gap = 0
        censored = 0
        for _day, units, stockout in ordered:
            if stockout:
                censored += 1
                continue
            gap += 1
            if units <= 0:
                continue
            if not started:
                size_hat = units
                interval_hat = float(gap)
                started = True
            else:
                size_hat = self.alpha * units + (1 - self.alpha) * size_hat
                interval_hat = self.alpha * gap + (1 - self.alpha) * interval_hat
            gap = 0
        if not started:
            return {
                "sku": sku,
                "per_period": 0.0,
                "size": 0.0,
                "interval": None,
                "intermittent": True,
                "censored_days": censored,
            }
        per_period = size_hat / interval_hat
        return {
            "sku": sku,
            "per_period": round(per_period, 3),
            "size": round(size_hat, 3),
            "interval": round(interval_hat, 3),
            "intermittent": interval_hat > INTERMITTENT_GAP,
            "censored_days": censored,
        }
