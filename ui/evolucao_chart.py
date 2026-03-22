from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QToolTip
)
from PySide6.QtCharts import (
    QChart, QChartView,
    QLineSeries, QValueAxis,
    QDateTimeAxis, QScatterSeries
)
from PySide6.QtCore import (
    Qt, QDateTime, QDate, QTime
)
from PySide6.QtGui import QColor, QCursor

from core.finance_app_service import FinanceAppService
from domain.lancamento import NatureType
from datetime import datetime, timedelta


class EvolucaoChart(QWidget):
    def __init__(self):
        super().__init__()

        self.service = FinanceAppService()
        self.history = self.service.evolution_by_date()

        layout = QVBoxLayout(self)

        # ==========================
        # 🔘 FILTROS
        # ==========================
        filter_layout = QHBoxLayout()

        self.btn_30 = QPushButton("30 dias")
        self.btn_90 = QPushButton("90 dias")
        self.btn_180 = QPushButton("180 dias")
        self.btn_365 = QPushButton("365 dias")

        for btn in [self.btn_30, self.btn_90, self.btn_180, self.btn_365]:
            btn.setCheckable(True)
            filter_layout.addWidget(btn)

        self.btn_30.clicked.connect(lambda: self.update_chart(30))
        self.btn_90.clicked.connect(lambda: self.update_chart(90))
        self.btn_180.clicked.connect(lambda: self.update_chart(180))
        self.btn_365.clicked.connect(lambda: self.update_chart(365))

        layout.addLayout(filter_layout)

        # ==========================
        # 📈 SÉRIES
        # ==========================
        self.series = QLineSeries()
        self.series.setName("Patrimônio Total")
        self.series.setColor(QColor("#1565c0"))
        self.series.setPointsVisible(True)
        self.series.hovered.connect(self._on_hover)

        self.series_media = QLineSeries()
        self.series_media.setName("Média móvel (7 dias)")
        self.series_media.setColor(QColor("#90caf9"))
        self.series_media.setPointsVisible(False)

        self.series_max = QScatterSeries()
        self.series_max.setName("Máximo")
        self.series_max.setColor(QColor("#c62828"))
        self.series_max.setMarkerSize(10)

        self.series_min = QScatterSeries()
        self.series_min.setName("Mínimo")
        self.series_min.setColor(QColor("#2e7d32"))
        self.series_min.setMarkerSize(10)

        # ==========================
        # 📊 CHART
        # ==========================
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.addSeries(self.series_media)
        self.chart.addSeries(self.series_max)
        self.chart.addSeries(self.series_min)
        self.chart.setTitle("Evolução do Patrimônio Total")
        self.chart.legend().setAlignment(Qt.AlignBottom)

        # ==========================
        # 🧭 EIXOS
        # ==========================
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("dd/MM")
        self.axis_x.setTitleText("Data")

        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("R$ %.2f")
        self.axis_y.setTitleText("Patrimônio")

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        for s in [self.series, self.series_media, self.series_max, self.series_min]:
            s.attachAxis(self.axis_x)
            s.attachAxis(self.axis_y)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(self.chart_view.renderHints())
        layout.addWidget(self.chart_view)

        self.btn_90.setChecked(True)
        self.update_chart(90)

    # ==========================
    # 🔄 ATUALIZAR
    # ==========================
    def update_chart(self, days: int):
        self._uncheck_buttons()
        self._check_button(days)

        self.series.clear()
        self.series_media.clear()
        self.series_max.clear()
        self.series_min.clear()

        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=days)

        pontos = []

        for d, saldo in sorted(self.history.items()):
            if not (start_date <= d <= end_date):
                continue

            total = (
                saldo.get(NatureType.CASH, 0)
                + saldo.get(NatureType.INVESTMENT, 0)
                + saldo.get(NatureType.RESERVE, 0)
            )

            dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
            ts = dt.toMSecsSinceEpoch()

            self.series.append(ts, total)
            pontos.append((ts, total))

        if not pontos:
            self.axis_y.setRange(0, 1)
            return

        # 📉 MÉDIA MÓVEL (7 dias)
        janela = 7
        for i in range(len(pontos)):
            if i + 1 < janela:
                continue
            media = sum(v for _, v in pontos[i + 1 - janela:i + 1]) / janela
            self.series_media.append(pontos[i][0], media)

        # 🔴🟢 MÁX / MIN
        ts_max, val_max = max(pontos, key=lambda x: x[1])
        ts_min, val_min = min(pontos, key=lambda x: x[1])

        self.series_max.append(ts_max, val_max)
        self.series_min.append(ts_min, val_min)

        # 📐 EIXO Y (CORREÇÃO DEFINITIVA)
        valores = [v for _, v in pontos]
        min_val = min(valores)
        max_val = max(valores)

        margem = max((max_val - min_val) * 0.1, 100)

        self.axis_y.setRange(
            min_val - margem,
            max_val + margem
        )

        # 📅 EIXO X (corrige último dia)
        self.axis_x.setRange(
            QDateTime(QDate(start_date.year, start_date.month, start_date.day), QTime(0, 0)),
            QDateTime(QDate(end_date.year, end_date.month, end_date.day), QTime(23, 59)),
        )

    # ==========================
    # 🖱 TOOLTIP
    # ==========================
    def _on_hover(self, point, state):
        if not state:
            QToolTip.hideText()
            return

        dt = QDateTime.fromMSecsSinceEpoch(int(point.x()))
        date_str = dt.toString("dd/MM/yyyy")

        value_str = (
            f"R$ {point.y():,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        QToolTip.showText(QCursor.pos(), f"{date_str}\n{value_str}")

    def _uncheck_buttons(self):
        for btn in [self.btn_30, self.btn_90, self.btn_180, self.btn_365]:
            btn.setChecked(False)

    def _check_button(self, days):
        {
            30: self.btn_30,
            90: self.btn_90,
            180: self.btn_180,
            365: self.btn_365,
        }[days].setChecked(True)