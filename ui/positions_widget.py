from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt

from repositories.investment_repository import InvestmentRepository
from services.price_service import PriceService

class PositionsWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.repo = InvestmentRepository()
        self.price_service = PriceService()
        self.layout = QVBoxLayout(self)
        self.load_positions()

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_positions(self):
        self.clear()

        positions = self.repo.get_open_positions()

        if not positions:
            self.layout.addWidget(QLabel("Nenhuma posição aberta"))
            return

        for p in positions:
            card = self.create_position_card(p)
            self.layout.addWidget(card)

    def create_position_card(self, position):
        container = QFrame()
        container.setStyleSheet("border: 1px solid #ccc; padding: 8px; border-radius: 8px;")

        layout = QVBoxLayout(container)

        # ==========================
        # 📊 HEADER
        # ==========================
        header = QLabel(
            f"{position['asset']} | "
            f"Qtd: {position['total_quantity']:.6f} | "
            f"Médio: {position['avg_price']:.2f}"
        )
        header.setStyleSheet("font-weight: bold;")

        layout.addWidget(header)

        # ==========================
        # 💰 LUCRO EM TEMPO REAL
        # ==========================
        prices = self.price_service.get_prices()

        current_price = prices.get(position["asset"], {}).get("brl", 0)
        avg_price = position["avg_price"]
        qty = position["total_quantity"]

        lucro = (current_price - avg_price) * qty

        percent = 0
        if avg_price > 0:
            percent = (current_price / avg_price - 1) * 100

        cor = "#2e7d32" if lucro >= 0 else "#c62828"

        label_lucro = QLabel(
            f"{percent:.2f}% | R$ {lucro:,.2f}"
        )
        label_lucro.setStyleSheet(f"color: {cor}; font-weight: bold;")

        layout.addWidget(label_lucro)

        # ==========================
        # 🔽 BOTÃO
        # ==========================
        btn_toggle = QPushButton("▼ Ver operações")
        btn_toggle.setCheckable(True)

        details = QVBoxLayout()
        details_widget = QWidget()
        details_widget.setLayout(details)
        details_widget.setVisible(False)

        def toggle():
            details_widget.setVisible(btn_toggle.isChecked())
            btn_toggle.setText("▲ Ocultar" if btn_toggle.isChecked() else "▼ Ver operações")

        btn_toggle.clicked.connect(toggle)

        # ==========================
        # 📄 COMPRAS
        # ==========================
        buys = self.repo.get_buys(position["id"])
        for b in buys:
            details.addWidget(QLabel(
                f"🟢 Compra: {b['quantity']} @ {b['price']}"
            ))

        # ==========================
        # 📄 VENDAS
        # ==========================
        sells = self.repo.get_sells(position["id"])
        for s in sells:
            details.addWidget(QLabel(
                f"🔴 Venda: {s['quantity']} @ {s['price']} | Lucro: {s['profit']:.2f}"
            ))

        layout.addWidget(btn_toggle)
        layout.addWidget(details_widget)

        return container