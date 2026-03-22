from domain.lancamento import NatureType
from repositories.lancamento_repository import LancamentoRepository
from repositories.transferencia_repository import TransferenciaRepository
from repositories.variacao_repository import VariacaoInvestimentoRepository
from services.finance_service import FinanceService
from domain.transferencia import Transferencia
from datetime import date


class FinanceAppService:
    """
    Application service that integrates repositories
    with domain services.
    """

    def __init__(self) -> None:
        self._lancamento_repo = LancamentoRepository()
        self._transferencia_repo = TransferenciaRepository()
        self._variacao_repo = VariacaoInvestimentoRepository()

    def get_finance_service(self) -> FinanceService:
        lancamentos = self._lancamento_repo.list_all()
        transferencias = self._transferencia_repo.list_all()
        variacoes = self._variacao_repo.list_all()

        return FinanceService(
            lancamentos=lancamentos,
            transferencias=transferencias,
            variacoes=variacoes,
        )

    # -----------------------------
    # CONSULTAS DE ALTO NÍVEL
    # -----------------------------

    def balance_of(self, nature: NatureType, mes=None, ano=None) -> float:
        service = self.get_finance_service()
        return service.balance_of(nature, mes, ano)

    def total_patrimony(self) -> float:
        service = self.get_finance_service()
        return service.total_patrimony()
    
    def total_proventos(self, mes=None, ano=None) -> float:
        return sum(
            l.amount
            for l in self._lancamento_repo.list_all()
            if l.entry_type.value == "PROVENTO"
            and (mes is None or l.entry_date.month == mes)
            and (ano is None or l.entry_date.year == ano)
        )

    def total_despesas(self, mes=None, ano=None) -> float:
        return sum(
            l.amount
            for l in self._lancamento_repo.list_all()
            if l.entry_type.value == "DESPESA"
            and (mes is None or l.entry_date.month == mes)
            and (ano is None or l.entry_date.year == ano)
        )

    def total_por_natureza(self, natureza: NatureType) -> float:
        service = self.get_finance_service()
        return service.balance_of(natureza)

    def saldo_total(self) -> float:
        return (
            self.balance_of(NatureType.CASH)
            + self.balance_of(NatureType.INVESTMENT)
            + self.balance_of(NatureType.RESERVE)
        )
    
    def transferir(
        self,
        amount: float,
        origin: NatureType,
        destination: NatureType,
        description: str | None = None,
    ):
        service = self.get_finance_service()

        transferencia = service.transfer(
            amount=amount,
            origin=origin,
            destination=destination,
            description=description,
        )

        self._transferencia_repo.add(transferencia)

    # -----------------------------
    # ✏️ EDITAR TRANSFERÊNCIA
    # -----------------------------
    def update_transferencia(
        self,
        transferencia_id: int,
        transfer_date: date,
        amount: float,
        origin: NatureType,
        destination: NatureType,
        description: str = ""
    ):
        # 🚫 Origem e destino iguais
        if origin == destination:
            raise ValueError("Origem e destino não podem ser iguais.")

        # 🔎 Saldo atual da origem (ANTES da edição)
        saldo_origem = self.balance_of(origin)

        # 🔒 Bloqueia se saldo insuficiente
        if saldo_origem < amount:
            raise ValueError(
                f"Saldo insuficiente em {origin.value}. "
                f"Saldo atual: R$ {saldo_origem:.2f}"
            )

        transferencia = Transferencia(
            id=transferencia_id,
            transfer_date=transfer_date,
            amount=amount,
            origin=origin,
            destination=destination,
            description=description,
        )

        self._transferencia_repo.update(transferencia_id, transferencia)
    
    def evolution_by_date(self):
        service = self.get_finance_service()
        return service.evolution_by_date()