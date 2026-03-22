from collections import defaultdict
from typing import Iterable
from domain.lancamento import Lancamento, NatureType, EntryType
from domain.transferencia import Transferencia
from domain.variacao_investimento import VariacaoInvestimento
from collections import defaultdict
from datetime import date


class FinanceService:
    """
    Application service responsible for financial calculations
    and business rules.
    """

    def __init__(self, lancamentos, transferencias, variacoes):
        self._lancamentos = list(lancamentos)
        self._transferencias = list(transferencias)
        self._variacoes = list(variacoes)

    # --------------------------------------------------
    # SALDOS
    # --------------------------------------------------

    def calculate_balances(self) -> dict[NatureType, float]:
        balances = defaultdict(float)

        # Lançamentos (entradas / despesas)
        for l in self._lancamentos:
            if l.entry_type == EntryType.INCOME:
                balances[l.nature] += l.amount
            else:
                balances[l.nature] -= l.amount

        # Transferências internas
        for t in self._transferencias:
            balances[t.origin] -= t.amount
            balances[t.destination] += t.amount

        # Variações de investimento
        for v in self._variacoes:
            balances[NatureType.INVESTMENT] += v.value_change

        return dict(balances)

    # --------------------------------------------------
    # CONSULTAS
    # --------------------------------------------------
    def balance_of(
        self,
        nature: NatureType,
        mes: int | None = None,
        ano: int | None = None
    ) -> float:
        saldo = 0.0

        # 🔹 Lançamentos
        for l in self._lancamentos:
            if l.nature != nature:
                continue
            if mes and l.entry_date.month != mes:
                continue
            if ano and l.entry_date.year != ano:
                continue

            if l.entry_type == EntryType.INCOME:
                saldo += l.amount
            else:
                saldo -= l.amount

        # 🔁 Transferências
        for t in self._transferencias:
            if mes and t.transfer_date.month != mes:
                continue
            if ano and t.transfer_date.year != ano:
                continue

            if t.origin == nature:
                saldo -= t.amount
            if t.destination == nature:
                saldo += t.amount

        return saldo

    def total_patrimony(self) -> float:
        balances = self.calculate_balances()
        return (
            balances.get(NatureType.CASH, 0)
            + balances.get(NatureType.INVESTMENT, 0)
            + balances.get(NatureType.RESERVE, 0)
    )
    
    def can_transfer(self, origin: NatureType, amount: float) -> bool:
        saldo = self.balance_of(origin)
        return saldo >= amount
    
    def register_transfer(self, transferencia: Transferencia):
        if not self.can_transfer(transferencia.origin, transferencia.amount):
            raise ValueError("Saldo insuficiente para realizar a transferência.")
        
    def transfer(
        self,
        amount: float,
        origin: NatureType,
        destination: NatureType,
        description: str | None = None,
    ):
        if amount <= 0:
            raise ValueError("O valor da transferência deve ser maior que zero.")

        # 🔒 VALIDA SALDO DA ORIGEM
        saldo_origem = self.balance_of(origin)

        if saldo_origem < amount:
            raise ValueError(
                f"Saldo insuficiente em {origin.value}. "
                f"Saldo atual: R$ {saldo_origem:.2f}"
            )

        from domain.transferencia import Transferencia
        from datetime import date

        transferencia = Transferencia(
            transfer_date=date.today(),
            amount=amount,
            origin=origin,
            destination=destination,
            description=description or "Transferência interna",
        )

        return transferencia
    
    def evolution_by_date(self):
        """
        Retorna evolução diária:
        {
            date: {
                NatureType.CASH: valor,
                NatureType.INVESTMENT: valor,
                NatureType.RESERVE: valor
            }
        }
        """
        events = []

        # 🔹 Lançamentos
        for l in self._lancamentos:
            events.append((
                l.entry_date,
                l.nature,
                l.amount if l.entry_type.value == "PROVENTO" else -l.amount
            ))

        # 🔹 Transferências
        for t in self._transferencias:
            events.append((t.transfer_date, t.origin, -t.amount))
            events.append((t.transfer_date, t.destination, t.amount))

        # 🔹 Ordenar por data
        events.sort(key=lambda x: x[0])

        saldo = defaultdict(float)
        history = {}

        for d, nature, value in events:
            saldo[nature] += value
            history[d] = saldo.copy()

        return history