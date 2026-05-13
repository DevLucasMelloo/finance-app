from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QToolTip, QLabel
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PySide6.QtCore import Qt, QDateTime, QDate, QTime
from PySide6.QtGui import QColor, QCursor, QPainter, QFont, QPen

from core.finance_app_service import FinanceAppService
from domain.lancamento import NatureType
from datetime import datetime, timedelta, date as date_type


def _fmt_short(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"R$ {v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"R$ {v/1_000:.0f}k"
    return f"R$ {v:.0f}"


def _to_ms(d) -> int:
    return QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0)).toMSecsSinceEpoch()


SERIES_CONFIG = [
    ("Patrimônio Total", "#1565c0", 2.5, True),
    ("Caixa",           "#150358", 1.5, True),
    ("Investimento",    "#ef6c00", 1.5, True),
    ("Reserva",         "#6a1b9a", 1.5, True),
]

NATURE_MAP = {
    "Caixa": NatureType.CASH,
    "Investimento": NatureType.INVESTMENT,
    "Reserva": NatureType.RESERVE,
}


class EvolucaoChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)

        self.service = FinanceAppService()
        self._days = None  # None = Todos

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ==========================
        # FILTROS DE PERÍODO
        # ==========================
        filter_row = QHBoxLayout()
        filter_row.setSpacing(0)

        self._period_btns: dict[str, QPushButton] = {}
        periods = [("Todos", None), ("30d", 30), ("90d", 90), ("180d", 180), ("1 ano", 365)]

        for label, days in periods:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ddd; border-radius: 0px;
                    padding: 2px 12px; background: #f5f5f5; color: #555;
                    font-size: 11px;
                }
                QPushButton:checked {
                    background: #1565c0; color: white; border-color: #1565c0;
                }
                QPushButton:hover:!checked { background: #e8f0fe; }
            """)
            btn.clicked.connect(lambda _, d=days: self._set_period(d))
            self._period_btns[label] = btn
            filter_row.addWidget(btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # ==========================
        # SÉRIES
        # ==========================
        self._series: dict[str, QLineSeries] = {}

        self.chart = QChart()
        self.chart.setTitle("Evolução do Patrimônio")
        self.chart.setTitleFont(QFont("Arial", 11, QFont.Bold))
        self.chart.legend().setAlignment(Qt.AlignBottom)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundRoundness(12)

        for name, color, width, _ in SERIES_CONFIG:
            s = QLineSeries()
            s.setName(name)
            pen = QPen(QColor(color))
            pen.setWidthF(width)
            s.setPen(pen)
            s.hovered.connect(lambda pt, state, n=name: self._on_hover(pt, state, n))
            self._series[name] = s
            self.chart.addSeries(s)

        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("MMM/yy")
        self.axis_x.setTitleText("Data")
        self.axis_x.setLabelsAngle(-30)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Patrimônio")
        self.axis_y.setLabelFormat("%.0f")

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        for s in self._series.values():
            s.attachAxis(self.axis_x)
            s.attachAxis(self.axis_y)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view)

        self._no_data_label = QLabel("Sem dados no período selecionado")
        self._no_data_label.setAlignment(Qt.AlignCenter)
        self._no_data_label.setStyleSheet("color: #999; font-size: 13px;")
        self._no_data_label.setVisible(False)
        layout.addWidget(self._no_data_label)

        self._set_period(None)  # Todos por padrão

    def _set_period(self, days):
        self._days = days
        for label, btn in self._period_btns.items():
            period_days = {"Todos": None, "30d": 30, "90d": 90, "180d": 180, "1 ano": 365}
            btn.setChecked(period_days[label] == days)
        self.refresh()

    def refresh(self, mes=None, ano=None):
        history = self.service.evolution_by_date()

        if not history:
            return

        for s in self._series.values():
            s.clear()

        all_dates = sorted(history.keys())
        end_date = date_type.today()

        if self._days:
            start_date = end_date - timedelta(days=self._days)
            dates = [d for d in all_dates if start_date <= d <= end_date]
        else:
            dates = all_dates

        if not dates:
            for s in self._series.values():
                s.clear()
            self._no_data_label.setVisible(True)
            self.chart_view.setVisible(False)
            return

        self._no_data_label.setVisible(False)
        self.chart_view.setVisible(True)

        all_totals = []

        for d in dates:
            snap = history[d]
            caixa = snap.get(NatureType.CASH, 0)
            invest = snap.get(NatureType.INVESTMENT, 0)
            reserva = snap.get(NatureType.RESERVE, 0)
            total = caixa + invest + reserva

            ts = _to_ms(d)
            self._series["Patrimônio Total"].append(ts, total)
            self._series["Caixa"].append(ts, caixa)
            self._series["Investimento"].append(ts, invest)
            self._series["Reserva"].append(ts, reserva)
            all_totals.append(total)

        if not all_totals:
            return

        # Ajusta eixos
        start = dates[0]
        end = dates[-1]

        # margem de 1 dia em cada lado
        dt_start = QDateTime(QDate(start.year, start.month, start.day), QTime(0, 0))
        dt_end = QDateTime(QDate(end.year, end.month, end.day), QTime(23, 59))
        self.axis_x.setRange(dt_start, dt_end)

        mn = min(all_totals)
        mx = max(all_totals)
        margem = max((mx - mn) * 0.15, 100)
        self.axis_y.setRange(max(0, mn - margem), mx + margem)

    def _on_hover(self, point, state, series_name):
        if not state:
            QToolTip.hideText()
            return
        dt = QDateTime.fromMSecsSinceEpoch(int(point.x()))
        val = f"R$ {point.y():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        QToolTip.showText(QCursor.pos(), f"{series_name}\n{dt.toString('dd/MM/yyyy')}\n{val}")
