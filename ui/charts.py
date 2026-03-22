from core.finance_app_service import FinanceAppService
from domain.lancamento import NatureType
import plotly.graph_objects as go
import plotly.io as pio

# força abrir no navegador
pio.renderers.default = "browser"


def plot_current_balances() -> None:
    app_service = FinanceAppService()

    balances = {
        "Caixa": app_service.balance_of(NatureType.CASH),
        "Investimentos": app_service.balance_of(NatureType.INVESTMENT),
        "Reserva": app_service.balance_of(NatureType.RESERVE),
    }

    total = sum(balances.values())

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(balances.keys()),
                y=list(balances.values()),
                text=[f"R$ {v:,.2f}" for v in balances.values()],
                textposition="auto",
                marker=dict(
                    color=["#2ecc71", "#3498db", "#f1c40f"]
                ),
            )
        ]
    )

    fig.update_layout(
        title={
            "text": f"Patrimônio Atual — Total: R$ {total:,.2f}",
            "x": 0.5,
            "xanchor": "center",
        },
        yaxis_title="Valor (R$)",
        xaxis_title="Tipo",
        template="plotly_white",
        font=dict(size=14),
    )

    fig.show()
