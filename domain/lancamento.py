from dataclasses import dataclass #reduz código boilerplate(código repetitivo)
from datetime import date
from enum import Enum #evitar erros de digitação e inconsistências


class EntryType(Enum):
    """
    Represents the type of a financial entry.
    """
    INCOME = "PROVENTO"
    EXPENSE = "DESPESA"
    TRANSFER = "TRANSFERENCIA"


class PaymentMethod(Enum):
    """
    Represents the payment method used.
    """
    CASH = "DINHEIRO"
    PIX = "PIX"
    BOLETO = "BOLETO"
    DEBIT_CARD = "CARTÃO DE DÉBITO"
    CREDIT_CARD = "CARTÃO DE CRÉDITO"


class NatureType(Enum):
    """
    Represents where the money is allocated.
    """
    CASH = "CAIXA"
    INVESTMENT = "INVESTIMENTO"
    RESERVE = "RESERVA"


@dataclass
class Lancamento:
    """
    Domain entity representing a financial transaction.
    """
    entry_date: date
    amount: float
    entry_type: EntryType
    payment_method: PaymentMethod
    category: str
    nature: NatureType
    description: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """
        Validates business rules for a financial entry.
        """
        if self.amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        if not isinstance(self.entry_date, date):
            raise TypeError("entry_date must be a date object.")

        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty.")
