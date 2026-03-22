from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox,
    QMessageBox, QHBoxLayout
)

from services.investment_service import InvestmentService
from domain.lancamento import NatureType


class CompraAtivoDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Comprar Ativo")
        self.setFixedWidth(300)

        self.service = InvestmentService()

        layout = QVBoxLayout(self)

        # Ativo
        self.asset = QComboBox()
        self.asset.addItems(["BTC", "ETH", "XRP"])

        # Quantidade
        self.quantity = QLineEdit()
        self.quantity.setPlaceholderText("Quantidade")

        # Preço
        self.price = QLineEdit()
        self.price.setPlaceholderText("Preço")

        # Conta
        self.account = QComboBox()
        self.account.addItem("CAIXA", NatureType.CASH)
        self.account.addItem("INVESTIMENTO", NatureType.INVESTMENT)
        self.account.addItem("RESERVA", NatureType.RESERVE)

        # Botões
        btn_save = QPushButton("Comprar")
        btn_cancel = QPushButton("Cancelar")

        btn_save.clicked.connect(self.buy)
        btn_cancel.clicked.connect(self.reject)

        # Layout
        for label, widget in [
            ("Ativo", self.asset),
            ("Quantidade", self.quantity),
            ("Preço", self.price),
            ("Conta origem", self.account),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        btns = QHBoxLayout()
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def buy(self):
        try:
            asset = self.asset.currentText()
            quantity = float(self.quantity.text())
            price = float(self.price.text())
            account = self.account.currentData()

            self.service.buy(
                asset=asset,
                quantity=quantity,
                price=price,
                origin_account=account
            )

            QMessageBox.information(self, "Sucesso", "Compra realizada!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))