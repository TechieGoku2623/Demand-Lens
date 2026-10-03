"""Faults for a demand history that cannot be forecast."""

from __future__ import annotations


class EngineKernelException(Exception):
    """Raised when a demand row breaks the forecast contract."""

    def __init__(self, message: str, *, fatal: bool = True) -> None:
        super().__init__(message)
        self.fatal = fatal
