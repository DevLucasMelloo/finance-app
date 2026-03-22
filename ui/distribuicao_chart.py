from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolTip
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QColor, QCursor
from PySide6.QtCore import Qt

from core.finance_app_service import FinanceAppService
from domain.lancamento import NatureType


class DistribuicaoChart(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        service = FinanceAppService()

        caixa = service.balance_of(NatureType.CASH)
        investimento = service.balance_of(NatureType.INVESTMENT)
        reserva = service.balance_of(NatureType.RESERVE)

        total = caixa + investimento + reserva

        series = QPieSeries()

        if caixa > 0:
            slice_caixa = series.append("Caixa", caixa)
            slice_caixa.setBrush(QColor("#1565c0"))

        if investimento > 0:
            slice_inv = series.append("Investimentos", investimento)
            slice_inv.setBrush(QColor("#ef6c00"))

        if reserva > 0:
            slice_res = series.append("Reserva", reserva)
            slice_res.setBrush(QColor("#6a1b9a"))

        # ==========================
        # 🖱 INTERAÇÃO (HOVER)
        # ==========================
        for s in series.slices():
            s.hovered.connect(lambda state, sl=s: self._on_hover(sl, state, total))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Distribuição do Patrimônio")
        chart.legend().setAlignment(Qt.AlignBottom)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(chart_view.renderHints())

        layout.addWidget(chart_view)

    # ==========================
    # 🖱 TOOLTIP + DESTAQUE
    # ==========================
    def _on_hover(self, slice_, state, total):
        if not state:
            slice_.setExploded(False)
            slice_.setLabelVisible(False)
            slice_.setPen(Qt.NoPen)
            QToolTip.hideText()
            return

        percent = (slice_.value() / total) * 100 if total > 0 else 0

        value_str = (
            f"R$ {slice_.value():,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        tooltip = (
            f"{slice_.label()}\n"
            f"{value_str}\n"
            f"{percent:.1f}%"
        )

        slice_.setExploded(True)
        slice_.setLabelVisible(True)
        slice_.setPen(QColor("#333333"))

        QToolTip.showText(QCursor.pos(), tooltip)
