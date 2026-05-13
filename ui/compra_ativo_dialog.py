from datetime import date as date_type

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox,
    QMessageBox, QDateEdit, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QDate

from services.investment_service import InvestmentService
from services.price_service import PriceService, COINGECKO_IDS
from domain.lancamento import NatureType

BROKERS = ["Binance", "Mercado Bitcoin", "Outro"]


class CompraAtivoDialog(QDialog):
    def __init__(self, asset: str = "", position=None, current_prices: dict | None = None):
        super().__init__()
        self.setWindowTitle("Registrar Compra")
        self.setMinimumWidth(380)

        self.service = InvestmentService()
        self.price_service = PriceService()
        self._position = position
        self._current_prices = current_prices or {}

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ==========================
        # ATIVO
        # ==========================
        layout.addWidget(self._section("Ativo"))

        row_asset = QHBoxLayout()
        self.asset_input = QLineEdit()
        self.asset_input.setPlaceholderText("Ex: BTC, ETH, PETR4, MXRF11...")
        self.asset_input.textChanged.connect(self._on_asset_changed)

        self.btn_fetch_price = QPushButton("Buscar preço")
        self.btn_fetch_price.setFixedWidth(110)
        self.btn_fetch_price.clicked.connect(self._fetch_current_price)
        self.btn_fetch_price.setVisible(False)

        row_asset.addWidget(self.asset_input)
        row_asset.addWidget(self.btn_fetch_price)
        layout.addLayout(row_asset)

        if asset:
            self.asset_input.setText(asset)
            self.asset_input.setReadOnly(True)

        # ==========================
        # CORRETORA
        # ==========================
        layout.addWidget(self._section("Corretora"))

        broker_row = QHBoxLayout()
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(BROKERS)
        self.broker_combo.currentTextChanged.connect(self._on_broker_changed)

        self.broker_custom = QLineEdit()
        self.broker_custom.setPlaceholderText("Nome da corretora...")
        self.broker_custom.setVisible(False)

        broker_row.addWidget(self.broker_combo)
        broker_row.addWidget(self.broker_custom)
        layout.addLayout(broker_row)

        # ==========================
        # QUANTIDADE E PREÇO
        # ==========================
        layout.addWidget(self._section("Operação"))

        form = QHBoxLayout()

        qty_col = QVBoxLayout()
        qty_col.addWidget(QLabel("Quantidade"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("0,00000000")
        self.quantity_input.textChanged.connect(self._update_total)
        qty_col.addWidget(self.quantity_input)

        price_col = QVBoxLayout()
        price_col.addWidget(QLabel("Preço unitário (R$)"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("0,00")
        self.price_input.textChanged.connect(self._update_total)
        price_col.addWidget(self.price_input)

        form.addLayout(qty_col)
        form.addLayout(price_col)
        layout.addLayout(form)

        # Total calculado
        self.lbl_total = QLabel("Total: R$ 0,00")
        self.lbl_total.setStyleSheet("font-weight: bold; color: #1565c0;")
        layout.addWidget(self.lbl_total)

        # ==========================
        # DATA
        # ==========================
        layout.addWidget(self._section("Data da operação"))

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input)

        # ==========================
        # CONTA ORIGEM
        # ==========================
        layout.addWidget(self._section("Conta de origem"))

        self.account_combo = QComboBox()
        self.account_combo.addItem("CAIXA", NatureType.CASH)
        self.account_combo.addItem("INVESTIMENTO", NatureType.INVESTMENT)
        self.account_combo.addItem("RESERVA", NatureType.RESERVE)
        layout.addWidget(self.account_combo)

        # ==========================
        # BOTÕES
        # ==========================
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #ddd;")
        layout.addWidget(sep)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Confirmar Compra")
        btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 16px;")
        btn_save.clicked.connect(self._confirm)

        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: bold; margin-top: 4px;")
        return lbl

    def _on_asset_changed(self, text: str):
        is_crypto = text.upper() in COINGECKO_IDS
        self.btn_fetch_price.setVisible(is_crypto)

    def _on_broker_changed(self, text: str):
        self.broker_custom.setVisible(text == "Outro")

    def _fetch_current_price(self):
        ticker = self.asset_input.text().strip().upper()
        try:
            # usa preços já carregados da view se disponíveis
            price = self._current_prices.get(ticker, {}).get("brl", 0.0)

            # se não tiver no cache, busca da API
            if price <= 0:
                prices = self.price_service.get_prices()
                price = prices.get(ticker, {}).get("brl", 0.0)

            if price > 0:
                self.price_input.setText(f"{price:.2f}")
            else:
                QMessageBox.warning(self, "Preço", "Não foi possível obter o preço atual.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _update_total(self):
        try:
            qty = float(self.quantity_input.text().replace(",", "."))
            price = float(self.price_input.text().replace(",", "."))
            total = qty * price
            self.lbl_total.setText(f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        except ValueError:
            self.lbl_total.setText("Total: R$ 0,00")

    def _get_broker(self) -> str:
        if self.broker_combo.currentText() == "Outro":
            return self.broker_custom.text().strip()
        return self.broker_combo.currentText()

    def _confirm(self):
        try:
            asset = self.asset_input.text().strip().upper()
            if not asset:
                raise ValueError("Informe o ativo.")

            qty_text = self.quantity_input.text().replace(",", ".")
            price_text = self.price_input.text().replace(",", ".")

            quantity = float(qty_text)
            price = float(price_text)

            if quantity <= 0 or price <= 0:
                raise ValueError("Quantidade e preço devem ser maiores que zero.")

            broker = self._get_broker()
            account = self.account_combo.currentData()

            qdate = self.date_input.date()
            op_date = date_type(qdate.year(), qdate.month(), qdate.day())

            self.service.buy(
                asset=asset,
                quantity=quantity,
                price=price,
                origin_account=account,
                broker=broker,
                operation_date=op_date,
            )

            QMessageBox.information(self, "Sucesso", f"Compra de {asset} registrada com sucesso!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
