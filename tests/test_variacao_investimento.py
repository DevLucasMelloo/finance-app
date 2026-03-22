from datetime import date
from domain.variacao_investimento import VariacaoInvestimento


def test_variacao_positiva():
    v = VariacaoInvestimento(
        reference_date=date.today(),
        value_change=1500,
        description="Rendimento mensal"
    )

    assert v.value_change == 1500
