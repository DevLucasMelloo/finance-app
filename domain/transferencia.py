from dataclasses import dataclass
from datetime import date
from enum import Enum
from domain.lancamento import NatureType


@dataclass
class Transferencia:
    """
    Domain entity representing an internal money transfer
    between different allocations (cash, investment, reserve).
    """
    id: int | None
    transfer_date: date
    amount: float
    origin: NatureType
    destination: NatureType
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.transfer_date, date):
            raise TypeError("transfer_date must be a date object.")

        if self.amount <= 0:
            raise ValueError("amount must be greater than zero.")

        if self.origin == self.destination:
            raise ValueError("origin and destination cannot be the same.")

    def _validate(self) -> None:
        if self.amount <= 0:
            raise ValueError("Transfer amount must be greater than zero.")

        if self.origin == self.destination:
            raise ValueError("Origin and destination must be different.")

        if not isinstance(self.transfer_date, date):
            raise TypeError("transfer_date must be a date object.")
