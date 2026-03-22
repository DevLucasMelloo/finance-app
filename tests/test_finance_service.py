from datetime import date
from domain.lancamento import Lancamento, LancamentoType, NatureType
from domain.transferencia import Transferencia
from domain.variacao_investimento import VariacaoInvestimento
from services.finance_service import FinanceService


def test_finance_service_complete_flow():
    lancamentos = [
        Lancamento(
            date=date(2025, 1, 5),
            description="Salário",
            amount=8000,
            type=LancamentoType.INCOME,
            nature=NatureType.CASH,
            payment_method="PIX",
        ),
        Lancamento(
            date=date(2025, 1, 10),
            description="Conta de luz",
            amount=400,
            type=LancamentoType.EXPENSE,
            nature=NatureType.CASH,
            payment_method="BOLETO",
        ),
    ]

    transferencias = [
        Transferencia(
            transfer_date=date(2025, 1, 15),
            amount=3000,
            origin=NatureType.CASH,
            destination=NatureType.INVESTMENT,
            description="Aporte",
        )
    ]

    variacoes = [
        VariacaoInvestimento(
            reference_date=date(2025, 1, 31),
            value_change=500,
            description="Rendimento mensal",
        )
    ]

    service = FinanceService(lancamentos, transferencias, variacoes)

    assert service.balance_of(NatureType.CASH) == 4600
    assert service.balance_of(NatureType.INVESTMENT) == 3500
    assert service.total_patrimony() == 8100
