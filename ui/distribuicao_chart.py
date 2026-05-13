from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolTip, QFrame
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QColor, QCursor, QPainter, QFont
from PySide6.QtCore import Qt

from repositories.lancamento_repository import LancamentoRepository
from repositories.transferencia_repository import TransferenciaRepository
from domain.lancamento import NatureType, EntryType


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


COLORS = {
    NatureType.CASH: "#1565c0",
    NatureType.INVESTMENT: "#ef6c00",
    NatureType.RESERVE: "#6a1b9a",
}
LABELS = {
    NatureType.CASH: "Caixa",
    NatureType.INVESTMENT: "Investimentos",
    NatureType.RESERVE: "Reserva",
}


class DistribuicaoChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.series = QPieSeries()
        self.series.setHoleSize(0.5)
        self.series.setPieSize(0.75)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Distribuição do Patrimônio")
        self.chart.setTitleFont(QFont("Arial", 11, QFont.Bold))
        self.chart.legend().setAlignment(Qt.AlignBottom)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundRoundness(12)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        # Label central (patrimônio positivo no furo)
        self.lbl_center = QLabel()
        self.lbl_center.setAlignment(Qt.AlignCenter)
        self.lbl_center.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #333; background: transparent;"
        )

        layout.addWidget(self.chart_view, 1)

        # Faixa de alertas para saldos negativos (oculta por padrão)
        self.negative_bar = QWidget()
        neg_layout = QHBoxLayout(self.negative_bar)
        neg_layout.setContentsMargins(12, 4, 12, 4)
        neg_layout.setSpacing(16)
        self._neg_labels: dict[NatureType, QLabel] = {}

        for nature in NatureType:
            lbl = QLabel()
            lbl.setStyleSheet(
                f"color: #c62828; font-size: 11px; font-weight: bold; "
                f"background: #ffebee; border: 1px solid #ef9a9a; "
                f"border-radius: 4px; padding: 2px 8px;"
            )
            lbl.setVisible(False)
            self._neg_labels[nature] = lbl
            neg_layout.addWidget(lbl)

        neg_layout.addStretch()
        self.negative_bar.setVisible(False)
        layout.addWidget(self.negative_bar)

        self.refresh()

    def refresh(self, mes=None, ano=None):
        lancamentos = LancamentoRepository().list_all()
        transferencias = TransferenciaRepository().list_all()

        saldos = {n: 0.0 for n in NatureType}

        for l in lancamentos:
            if mes and l.entry_date.month != mes:
                continue
            if ano and l.entry_date.year != ano:
                continue
            v = l.amount if l.entry_type == EntryType.INCOME else -l.amount
            saldos[l.nature] += v

        for t in transferencias:
            if mes and t.transfer_date.month != mes:
                continue
            if ano and t.transfer_date.year != ano:
                continue
            saldos[t.origin] -= t.amount
            saldos[t.destination] += t.amount

        # Reconstrói o donut apenas com positivos
        self.series.clear()
        positivo_total = sum(v for v in saldos.values() if v > 0)

        for nature in NatureType:
            val = saldos[nature]
            if val > 0:
                sl = self.series.append(LABELS[nature], val)
                sl.setBrush(QColor(COLORS[nature]))
                sl.hovered.connect(
                    lambda state, s=sl, t=positivo_total: self._on_hover(s, state, t)
                )

        # Total real (inclui negativos) no centro
        total_real = sum(saldos.values())
        color = "#2e7d32" if total_real >= 0 else "#c62828"
        self.lbl_center.setText(f"Total\n{_fmt(total_real)}")
        self.lbl_center.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {color}; background: transparent;"
        )

        # Exibe avisos de saldo negativo
        has_negative = False
        for nature in NatureType:
            val = saldos[nature]
            lbl = self._neg_labels[nature]
            if val < 0:
                lbl.setText(f"⚠ {LABELS[nature]}: {_fmt(val)}")
                lbl.setVisible(True)
                has_negative = True
            else:
                lbl.setVisible(False)

        self.negative_bar.setVisible(has_negative)
        self._update_center_label()

    def _update_center_label(self):
        rect = self.chart_view.geometry()
        if rect.width() == 0:
            return
        cx = rect.width() // 2
        cy = rect.height() // 2
        w, h = 130, 42
        self.lbl_center.setParent(self.chart_view)
        self.lbl_center.setGeometry(cx - w // 2, cy - h // 2, w, h)
        self.lbl_center.show()
        self.lbl_center.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_center_label()

    def _on_hover(self, slice_, state, total):
        if not state:
            slice_.setExploded(False)
            slice_.setLabelVisible(False)
            QToolTip.hideText()
            return
        percent = (slice_.value() / total * 100) if total > 0 else 0
        slice_.setExploded(True)
        slice_.setLabelVisible(True)
        QToolTip.showText(
            QCursor.pos(),
            f"{slice_.label()}\n{_fmt(slice_.value())}\n{percent:.1f}%"
        )
