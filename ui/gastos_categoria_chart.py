from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolTip
from PySide6.QtCharts import (
    QChart, QChartView,
    QHorizontalBarSeries, QBarSet,
    QBarCategoryAxis, QValueAxis
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QFont, QCursor

from repositories.lancamento_repository import LancamentoRepository
from domain.lancamento import EntryType
from collections import defaultdict

BAR_COLORS = [
    "#c62828", "#e53935", "#ef5350", "#f44336",
    "#e57373", "#ef9a9a", "#ffcdd2", "#b71c1c",
]


class GastosCategoriaChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.chart = QChart()
        self.chart.setTitle("Top Gastos por Categoria")
        self.chart.setTitleFont(QFont("Arial", 11, QFont.Bold))
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundRoundness(12)
        self.chart.legend().hide()

        self.axis_y = QBarCategoryAxis()
        self.axis_x = QValueAxis()
        self.axis_x.setLabelFormat("R$ %.0f")

        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view)

        self.refresh()

    def refresh(self, mes=None, ano=None):
        lancamentos = LancamentoRepository().list_all()

        gastos: dict[str, float] = defaultdict(float)
        for l in lancamentos:
            if l.entry_type != EntryType.EXPENSE:
                continue
            if mes and l.entry_date.month != mes:
                continue
            if ano and l.entry_date.year != ano:
                continue
            gastos[l.category] += l.amount

        if not gastos:
            return

        # top 8 categorias
        top = sorted(gastos.items(), key=lambda x: x[1], reverse=True)[:8]
        top = list(reversed(top))  # menor para maior (horizontal bar de baixo pra cima)

        # remove séries antigas
        self.chart.removeAllSeries()

        for i, (cat, val) in enumerate(top):
            bar_set = QBarSet(cat)
            bar_set.setColor(QColor(BAR_COLORS[i % len(BAR_COLORS)]))
            bar_set.append(val)
            bar_set.hovered.connect(
                lambda state, v=val, c=cat: self._on_hover(state, c, v)
            )

            series = QHorizontalBarSeries()
            series.append(bar_set)
            self.chart.addSeries(series)
            series.attachAxis(self.axis_y)
            series.attachAxis(self.axis_x)

        categories = [cat for cat, _ in top]
        self.axis_y.clear()
        self.axis_y.append(categories)

        mx = max(v for _, v in top)
        self.axis_x.setRange(0, mx * 1.2)

    def _on_hover(self, state, cat, val):
        if not state:
            QToolTip.hideText()
            return
        val_str = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        QToolTip.showText(QCursor.pos(), f"{cat}\n{val_str}")
