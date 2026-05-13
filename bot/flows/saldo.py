from domain.lancamento import NatureType
from core.finance_app_service import FinanceAppService


def get_saldo() -> str:
    svc = FinanceAppService()
    caixa = svc.balance_of(NatureType.CASH)
    invest = svc.balance_of(NatureType.INVESTMENT)
    reserva = svc.balance_of(NatureType.RESERVE)
    total = caixa + invest + reserva

    def fmt(v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    status = "✅" if total >= 0 else "⚠️"
    return (
        f"💰 *Saldo atual* {status}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💵 Caixa:         {fmt(caixa)}\n"
        f"📈 Investimento:  {fmt(invest)}\n"
        f"🏦 Reserva:       {fmt(reserva)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"Total: *{fmt(total)}*"
    )
