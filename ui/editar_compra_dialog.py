from datetime import date as date_type

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox,
    QMessageBox, QDateEdit, QFrame
)
from PySide6.QtCore import QDate

from repositories.investment_repository import InvestmentRepository

BROKERS = ["Binance", "Mercado Bitcoin", "Outro"]


class EditarCompraDialog(QDialog):
    def __init__(self, buy_row, position_row):
        super().__init__()
        self.setWindowTitle("Editar Compra")
        self.setMinimumWidth(360)

        self.repo = InvestmentRepository()
        self._buy_id = buy_row["id"]
        self._position_id = buy_row["position_id"]

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(self._section(f"Ativo: {position_row['asset']}"))

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

        current_broker = buy_row["broker"] or ""
        if current_broker in BROKERS:
            self.broker_combo.setCurrentText(current_broker)
        elif current_broker:
            self.broker_combo.setCurrentText("Outro")
            self.broker_custom.setText(current_broker)
            self.broker_custom.setVisible(True)

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
        self.quantity_input = QLineEdit(str(buy_row["quantity"]))
        self.quantity_input.textChanged.connect(self._update_total)
        qty_col.addWidget(self.quantity_input)

        price_col = QVBoxLayout()
        price_col.addWidget(QLabel("Preço unitário (R$)"))
        self.price_input = QLineEdit(f"{buy_row['price']:.2f}")
        self.price_input.textChanged.connect(self._update_total)
        price_col.addWidget(self.price_input)

        form.addLayout(qty_col)
        form.addLayout(price_col)
        layout.addLayout(form)

        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet("font-weight: bold; color: #1565c0;")
        layout.addWidget(self.lbl_total)
        self._update_total()

        # ==========================
        # DATA
        # ==========================
        layout.addWidget(self._section("Data da operação"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        try:
            y, m, d = buy_row["date"].split("-")
            self.date_input.setDate(QDate(int(y), int(m), int(d)))
        except Exception:
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

        btn_save = QPushButton("Salvar Alterações")
        btn_save.setStyleSheet(
            "background-color: #1565c0; color: white; font-weight: bold; padding: 6px 16px;"
        )
        btn_save.clicked.connect(self._save)

        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: bold; margin-top: 4px;")
        return lbl

    def _on_broker_changed(self, text: str):
        self.broker_custom.setVisible(text == "Outro")

    def _update_total(self):
        try:
            qty = float(self.quantity_input.text().replace(",", "."))
            price = float(self.price_input.text().replace(",", "."))
            total = qty * price
            self.lbl_total.setText(
                f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        except ValueError:
            self.lbl_total.setText("Total: R$ 0,00")

    def _get_broker(self) -> str:
        if self.broker_combo.currentText() == "Outro":
            return self.broker_custom.text().strip()
        return self.broker_combo.currentText()

    def _save(self):
        try:
            qty = float(self.quantity_input.text().replace(",", "."))
            price = float(self.price_input.text().replace(",", "."))
            if qty <= 0 or price <= 0:
                raise ValueError("Quantidade e preço devem ser maiores que zero.")

            broker = self._get_broker()
            qdate = self.date_input.date()
            op_date = f"{qdate.year()}-{qdate.month():02d}-{qdate.day():02d}"

            self.repo.update_buy(
                self._buy_id,
                quantity=qty,
                price=price,
                total=qty * price,
                broker=broker,
                date=op_date,
            )
            self.repo.recalculate_position(self._position_id)

            QMessageBox.information(self, "Sucesso", "Compra atualizada com sucesso!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
