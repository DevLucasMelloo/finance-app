from dataclasses import dataclass
from datetime import date


@dataclass
class VariacaoInvestimento:
    """
    Represents a change in the investment value
    without money movement.
    """
    reference_date: date
    value_change: float
    description: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.value_change == 0:
            raise ValueError("Investment variation cannot be zero.")

        if not isinstance(self.reference_date, date):
            raise TypeError("reference_date must be a date object.")
