from datetime import date
from domain.lancamento import Lancamento, EntryType, PaymentMethod, NatureType
from domain.transferencia import Transferencia
from domain.variacao_investimento import VariacaoInvestimento
from repositories.lancamento_repository import LancamentoRepository
from repositories.transferencia_repository import TransferenciaRepository
from repositories.variacao_repository import VariacaoInvestimentoRepository


def seed():
    lanc_repo = LancamentoRepository()
    trans_repo = TransferenciaRepository()
    var_repo = VariacaoInvestimentoRepository()

    # Entradas
    lanc_repo.add(
        Lancamento(
            entry_date=date(2026, 1, 1),
            amount=5000,
            entry_type=EntryType.INCOME,
            payment_method=PaymentMethod.PIX,
            category="Salário",
            nature=NatureType.CASH,
            description="Salário mensal",
        )
    )

    # Despesas
    lanc_repo.add(
        Lancamento(
            entry_date=date(2026, 1, 5),
            amount=1200,
            entry_type=EntryType.EXPENSE,
            payment_method=PaymentMethod.CREDIT_CARD,
            category="Aluguel",
            nature=NatureType.CASH,
            description="Aluguel",
        )
    )

    # Transferência para investimento
    trans_repo.add(
        Transferencia(
            transfer_date=date(2026, 1, 10),
            amount=2000,
            origin=NatureType.CASH,
            destination=NatureType.INVESTMENT,
            description="Aplicação mensal",
        )
    )

    # Variação de investimento
    var_repo.add(
        VariacaoInvestimento(
            reference_date=date(2026, 1, 31),
            value_change=150,
            description="Rendimento do mês",
        )
    )

    print("Dados de teste inseridos com sucesso.")


if __name__ == "__main__":
    seed()
