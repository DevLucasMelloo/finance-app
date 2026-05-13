from datetime import date as date_type

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox,
    QMessageBox, QDateEdit, QFrame
)
from PySide6.QtCore import QDate

from services.investment_service import InvestmentService
from services.price_service import PriceService, COINGECKO_IDS
from repositories.investment_repository import InvestmentRepository


class VendaAtivoDialog(QDialog):
    def __init__(self, position=None):
        super().__init__()
        self.setWindowTitle("Registrar Venda")
        self.setMinimumWidth(380)

        self.service = InvestmentService()
        self.price_service = PriceService()
        self.repo = InvestmentRepository()

        self._positions = self.repo.get_open_positions()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ==========================
        # SELECIONAR POSIÇÃO
        # ==========================
        layout.addWidget(self._section("Ativo / Posição"))

        self.position_combo = QComboBox()
        for p in self._positions:
            broker = f" - {p['broker']}" if p["broker"] else ""
            self.position_combo.addItem(
                f"{p['asset']}{broker} | Qtd: {p['total_quantity']:.8f} | Médio: R$ {p['avg_price']:.2f}",
                p["id"]
            )
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        layout.addWidget(self.position_combo)

        # Posição pré-selecionada
        if position:
            for i, p in enumerate(self._positions):
                if p["id"] == position["id"]:
                    self.position_combo.setCurrentIndex(i)
                    break

        # ==========================
        # INFO DA POSIÇÃO SELECIONADA
        # ==========================
        self.lbl_position_info = QLabel()
        self.lbl_position_info.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(self.lbl_position_info)

        # ==========================
        # QUANTIDADE E PREÇO
        # ==========================
        layout.addWidget(self._section("Operação"))

        form = QHBoxLayout()

        qty_col = QVBoxLayout()
        qty_col.addWidget(QLabel("Quantidade a vender"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("0,00000000")
        self.quantity_input.textChanged.connect(self._update_total)
        qty_col.addWidget(self.quantity_input)

        price_col = QVBoxLayout()
        price_col.addWidget(QLabel("Preço de venda (R$)"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("0,00")
        self.price_input.textChanged.connect(self._update_total)
        price_col.addWidget(self.price_input)

        form.addLayout(qty_col)
        form.addLayout(price_col)
        layout.addLayout(form)

        self.btn_fetch_price = QPushButton("Buscar preço atual")
        self.btn_fetch_price.clicked.connect(self._fetch_price)
        layout.addWidget(self.btn_fetch_price)

        # ==========================
        # RESUMO
        # ==========================
        self.lbl_total = QLabel("Receita: R$ 0,00")
        self.lbl_total.setStyleSheet("font-weight: bold; color: #1565c0;")
        self.lbl_profit = QLabel("Resultado: —")
        self.lbl_profit.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_total)
        layout.addWidget(self.lbl_profit)

        # ==========================
        # DATA
        # ==========================
        layout.addWidget(self._section("Data da operação"))

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input)

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

        btn_save = QPushButton("Confirmar Venda")
        btn_save.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; padding: 6px 16px;")
        btn_save.clicked.connect(self._confirm)

        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(btn_save)
        layout.addLayout(btns)

        self._on_position_changed()

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: bold; margin-top: 4px;")
        return lbl

    def _current_position(self):
        idx = self.position_combo.currentIndex()
        if idx < 0 or idx >= len(self._positions):
            return None
        return self._positions[idx]

    def _on_position_changed(self):
        p = self._current_position()
        if not p:
            return
        broker = p["broker"] or "—"
        self.lbl_position_info.setText(
            f"Corretora: {broker} | Preço médio: R$ {p['avg_price']:,.2f} | "
            f"Total investido: R$ {p['total_invested']:,.2f}"
        )
        ticker = p["asset"].upper()
        self.btn_fetch_price.setVisible(ticker in COINGECKO_IDS)
        self._update_total()

    def _fetch_price(self):
        p = self._current_position()
        if not p:
            return
        ticker = p["asset"].upper()
        try:
            prices = self.price_service.get_prices()
            price = prices.get(ticker, {}).get("brl", 0.0)
            if price > 0:
                self.price_input.setText(f"{price:.2f}")
            else:
                QMessageBox.warning(self, "Preço", "Não foi possível obter o preço atual.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _update_total(self):
        p = self._current_position()
        try:
            qty = float(self.quantity_input.text().replace(",", "."))
            price = float(self.price_input.text().replace(",", "."))
            total = qty * price

            def fmt(v):
                return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            self.lbl_total.setText(f"Receita: {fmt(total)}")

            if p:
                profit = (price - p["avg_price"]) * qty
                color = "#2e7d32" if profit >= 0 else "#c62828"
                sign = "+" if profit >= 0 else ""
                self.lbl_profit.setText(f"Resultado: {sign}{fmt(profit)}")
                self.lbl_profit.setStyleSheet(f"font-weight: bold; color: {color};")
        except ValueError:
            self.lbl_total.setText("Receita: R$ 0,00")
            self.lbl_profit.setText("Resultado: —")
            self.lbl_profit.setStyleSheet("font-weight: bold;")

    def _confirm(self):
        try:
            p = self._current_position()
            if not p:
                raise ValueError("Selecione uma posição.")

            qty_text = self.quantity_input.text().replace(",", ".")
            price_text = self.price_input.text().replace(",", ".")

            quantity = float(qty_text)
            price = float(price_text)

            if quantity <= 0 or price <= 0:
                raise ValueError("Quantidade e preço devem ser maiores que zero.")

            qdate = self.date_input.date()
            op_date = date_type(qdate.year(), qdate.month(), qdate.day())

            self.service.sell(
                asset=p["asset"],
                quantity=quantity,
                price=price,
                operation_date=op_date,
            )

            profit = (price - p["avg_price"]) * quantity
            sign = "+" if profit >= 0 else ""

            def fmt(v):
                return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            QMessageBox.information(
                self, "Venda realizada",
                f"Venda de {p['asset']} registrada!\nResultado: {sign}{fmt(profit)}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
