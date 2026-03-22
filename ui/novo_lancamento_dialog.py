from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QDateEdit, QMessageBox
)
from PySide6.QtCore import QDate

from domain.lancamento import Lancamento, EntryType, PaymentMethod, NatureType
from repositories.lancamento_repository import LancamentoRepository


class NovoLancamentoDialog(QDialog):
    def __init__(self, row=None):
        super().__init__()

        self.setWindowTitle("Lançamento")
        self.setFixedWidth(400)

        # ==========================
        # 🔒 CONTROLE DE EDIÇÃO
        # ==========================
        self.lancamento_id = None
        self.row = row

        if row:
            self.lancamento_id = row[0]  # 👈 SEMPRE PEGA O ID

        layout = QVBoxLayout(self)

        # ==========================
        # 📅 DATA
        # ==========================
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        # 💰 VALOR
        self.amount = QLineEdit()

        # 🔄 TIPO
        self.entry_type = QComboBox()
        self.entry_type.addItem("PROVENTO", EntryType.INCOME)
        self.entry_type.addItem("DESPESA", EntryType.EXPENSE)

        # 💳 PAGAMENTO
        self.payment = QComboBox()
        for p in PaymentMethod:
            self.payment.addItem(p.value, p)

        # 🧭 NATUREZA
        self.nature = QComboBox()
        for n in NatureType:
            self.nature.addItem(n.value, n)

        # 🏷 CATEGORIA
        self.category = QLineEdit()

        # 📝 DESCRIÇÃO
        self.description = QLineEdit()

        # ==========================
        # 📐 LAYOUT
        # ==========================
        for label, widget in [
            ("Data", self.date),
            ("Valor", self.amount),
            ("Tipo", self.entry_type),
            ("Forma de Pagamento", self.payment),
            ("Natureza", self.nature),
            ("Categoria", self.category),
            ("Descrição", self.description),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        # ==========================
        # 🔘 BOTÕES
        # ==========================
        btns = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")

        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)

        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        # ==========================
        # 🔁 PREENCHER FORM (EDIÇÃO)
        # ==========================
        if self.lancamento_id:
            self._fill_form()

    # ==========================
    # 💾 SALVAR
    # ==========================
    def save(self):
        try:
            valor = float(
                self.amount.text()
                .replace("R$", "")
                .replace(" ", "")
                .replace(",", ".")
            )

            lanc = Lancamento(
                entry_date=self.date.date().toPython(),
                amount=valor,
                entry_type=self.entry_type.currentData(),
                payment_method=self.payment.currentData(),
                category=self.category.text(),
                nature=self.nature.currentData(),
                description=self.description.text(),
            )

            repo = LancamentoRepository()

            if self.lancamento_id:
                # 🔁 UPDATE REAL
                repo.update(self.lancamento_id, lanc)
            else:
                # ➕ INSERT
                repo.add(lanc)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    # ==========================
    # 📝 PREENCHER FORM
    # ==========================
    def _fill_form(self):
        (
            _id,
            entry_date,
            description,
            amount,
            entry_type,
            payment_method,
            nature,
            category,
            *_  # 👈 ignora __tipo__ e extras
        ) = self.row

        self.date.setDate(QDate.fromString(entry_date, "yyyy-MM-dd"))
        self.amount.setText(str(amount))
        self.description.setText(description)
        self.category.setText(category)

        self.entry_type.setCurrentText(entry_type)
        self.payment.setCurrentText(payment_method)
        self.nature.setCurrentText(nature)
