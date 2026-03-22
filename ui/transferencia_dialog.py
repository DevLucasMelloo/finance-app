from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox,
    QLineEdit, QMessageBox
)
from domain.lancamento import NatureType
from core.finance_app_service import FinanceAppService


class TransferenciaDialog(QDialog):
    def __init__(self, transferencia=None):
        super().__init__()
        self.setWindowTitle("Transferência")
        self.setFixedWidth(350)

        self.transferencia = transferencia
        self.service = FinanceAppService()

        layout = QVBoxLayout(self)

        # -------------------------
        # ORIGEM / DESTINO
        # -------------------------
        self.origin = QComboBox()
        self.destination = QComboBox()

        for n in NatureType:
            self.origin.addItem(n.value, n)
            self.destination.addItem(n.value, n)

        # -------------------------
        # VALOR
        # -------------------------
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Valor (ex: 1000.00)")

        # -------------------------
        # DESCRIÇÃO
        # -------------------------
        self.description = QLineEdit()
        self.description.setPlaceholderText("Descrição (opcional)")

        # -------------------------
        # BOTÕES
        # -------------------------
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")

        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)

        # -------------------------
        # LAYOUT
        # -------------------------
        layout.addWidget(QLabel("De:"))
        layout.addWidget(self.origin)

        layout.addWidget(QLabel("Para:"))
        layout.addWidget(self.destination)

        layout.addWidget(QLabel("Valor"))
        layout.addWidget(self.amount)

        layout.addWidget(QLabel("Descrição"))
        layout.addWidget(self.description)

        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        # ✏️ MODO EDIÇÃO
        if self.transferencia:
            self._fill_form()

    # ---------------------------------
    # ✏️ PREENCHER FORMULÁRIO
    # ---------------------------------
    def _fill_form(self):
        self.origin.setCurrentIndex(
            self.origin.findData(self.transferencia.origin)
        )
        self.destination.setCurrentIndex(
            self.destination.findData(self.transferencia.destination)
        )

        self.amount.setText(f"{self.transferencia.amount:.2f}")
        self.description.setText(self.transferencia.description or "")

    # ---------------------------------
    # 💾 SALVAR
    # ---------------------------------
    def save(self):
        origin = self.origin.currentData()
        destination = self.destination.currentData()

        if origin == destination:
            QMessageBox.warning(
                self,
                "Erro",
                "Origem e destino não podem ser iguais."
            )
            return

        try:
            amount = float(self.amount.text().replace(",", "."))
            description = self.description.text()

            # ✏️ EDIÇÃO
            if self.transferencia:
                self.service.update_transferencia(
                    transferencia_id=self.transferencia.id,
                    transfer_date=self.transferencia.transfer_date,  # ✅ DATA ORIGINAL
                    amount=amount,
                    origin=origin,
                    destination=destination,
                    description=description,
                )

            # ➕ NOVA TRANSFERÊNCIA
            else:
                self.service.transferir(
                    amount=amount,
                    origin=origin,
                    destination=destination,
                    description=description,
                )

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))

        except Exception as e:
            QMessageBox.critical(self, "Erro inesperado", str(e))
