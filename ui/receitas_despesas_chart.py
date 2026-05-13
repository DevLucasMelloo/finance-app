from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QToolTip
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet,
    QBarCategoryAxis, QValueAxis
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QFont, QCursor

from repositories.lancamento_repository import LancamentoRepository
from domain.lancamento import EntryType
from datetime import date as date_type
from collections import defaultdict


MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


class ReceitasDespesasChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(260)
        self._ano_filter = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ==========================
        # FILTROS ANO
        # ==========================
        filter_row = QHBoxLayout()
        filter_row.setSpacing(0)

        self._year_btns: dict[str, QPushButton] = {}
        ano_atual = date_type.today().year
        anos = [("Todos", None)] + [(str(a), a) for a in range(ano_atual - 2, ano_atual + 1)]

        for label, ano in anos:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ddd; border-radius: 0px;
                    padding: 2px 12px; background: #f5f5f5; color: #555; font-size: 11px;
                }
                QPushButton:checked { background: #2e7d32; color: white; border-color: #2e7d32; }
                QPushButton:hover:!checked { background: #e8f5e9; }
            """)
            btn.clicked.connect(lambda _, a=ano: self._set_ano(a))
            self._year_btns[label] = btn
            filter_row.addWidget(btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # ==========================
        # CHART
        # ==========================
        self.set_proventos = QBarSet("Proventos")
        self.set_proventos.setColor(QColor("#2e7d32"))

        self.set_despesas = QBarSet("Despesas")
        self.set_despesas.setColor(QColor("#c62828"))

        self.bar_series = QBarSeries()
        self.bar_series.append(self.set_proventos)
        self.bar_series.append(self.set_despesas)
        self.bar_series.hovered.connect(self._on_hover)

        self.chart = QChart()
        self.chart.addSeries(self.bar_series)
        self.chart.setTitle("Receitas vs Despesas por Mês")
        self.chart.setTitleFont(QFont("Arial", 11, QFont.Bold))
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundRoundness(12)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.axis_x = QBarCategoryAxis()
        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("R$ %.0f")

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.bar_series.attachAxis(self.axis_x)
        self.bar_series.attachAxis(self.axis_y)

        view = QChartView(self.chart)
        view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(view)

        self._set_ano(ano_atual)

    def _set_ano(self, ano):
        self._ano_filter = ano
        for label, btn in self._year_btns.items():
            yr = {"Todos": None}.get(label, int(label) if label != "Todos" else None)
            btn.setChecked(yr == ano)
        self.refresh()

    def refresh(self, mes=None, ano=None):
        # usa filtro interno do botão de ano se não vier parâmetro
        ano_ref = self._ano_filter

        lancamentos = LancamentoRepository().list_all()

        proventos_mes: dict[tuple, float] = defaultdict(float)
        despesas_mes: dict[tuple, float] = defaultdict(float)

        for l in lancamentos:
            if ano_ref and l.entry_date.year != ano_ref:
                continue
            key = (l.entry_date.year, l.entry_date.month)
            if l.entry_type == EntryType.INCOME:
                proventos_mes[key] += l.amount
            else:
                despesas_mes[key] += l.amount

        all_keys = sorted(set(proventos_mes) | set(despesas_mes))
        if not all_keys:
            return

        labels = [f"{MESES[k[1]-1]}/{str(k[0])[2:]}" for k in all_keys]

        self.set_proventos.remove(0, self.set_proventos.count())
        self.set_despesas.remove(0, self.set_despesas.count())

        for k in all_keys:
            self.set_proventos.append(proventos_mes.get(k, 0))
            self.set_despesas.append(despesas_mes.get(k, 0))

        self.axis_x.clear()
        self.axis_x.append(labels)

        mx = max(
            max((proventos_mes.get(k, 0) for k in all_keys), default=0),
            max((despesas_mes.get(k, 0) for k in all_keys), default=0),
        )
        self.axis_y.setRange(0, mx * 1.15)

    def _on_hover(self, state, index, barset):
        if not state:
            QToolTip.hideText()
            return
        val = barset.at(index)
        label = barset.label()
        val_str = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        QToolTip.showText(QCursor.pos(), f"{label}\n{val_str}")
