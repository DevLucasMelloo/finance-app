from datetime import date
from domain.lancamento import Lancamento, LancamentoType, NatureType
from domain.transferencia import Transferencia
from domain.variacao_investimento import VariacaoInvestimento

from repositories.lancamento_repository import LancamentoRepository
from repositories.transferencia_repository import TransferenciaRepository
from repositories.variacao_repository import VariacaoInvestimentoRepository


def test_repositories_flow():
    lanc_repo = LancamentoRepository()
    transf_repo = TransferenciaRepository()
    var_repo = VariacaoInvestimentoRepository()

    lanc_repo.add(
        Lancamento(
            date=date.today(),
            description="Salário",
            amount=5000,
            type=LancamentoType.INCOME,
            nature=NatureType.CASH,
            payment_method="PIX",
        )
    )

    transf_repo.add(
        Transferencia(
            transfer_date=date.today(),
            amount=1000,
            origin=NatureType.CASH,
            destination=NatureType.INVESTMENT,
            description="Aporte",
        )
    )

    var_repo.add(
        VariacaoInvestimento(
            reference_date=date.today(),
            value_change=200,
            description="Rendimento",
        )
    )

    assert len(lanc_repo.list_all()) > 0
    assert len(transf_repo.list_all()) > 0
    assert len(var_repo.list_all()) > 0
