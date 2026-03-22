from domain.lancamento import NatureType
from core.finance_app_service import FinanceAppService


def test_finance_app_service_balances():
    app_service = FinanceAppService()

    cash = app_service.balance_of(NatureType.CASH)
    investment = app_service.balance_of(NatureType.INVESTMENT)
    reserve = app_service.balance_of(NatureType.RESERVE)

    total = app_service.total_patrimony()

    assert isinstance(cash, float)
    assert isinstance(investment, float)
    assert isinstance(reserve, float)
    assert isinstance(total, float)
