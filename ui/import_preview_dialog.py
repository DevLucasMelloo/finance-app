from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt


class ImportPreviewDialog(QDialog):
    def __init__(self, rows: list[dict]):
        super().__init__()

        self.setWindowTitle("Pré-visualização da Importação")
        self.resize(900, 400)

        self.rows = rows
        self.mode = None  # "ignore" | "overwrite"

        layout = QVBoxLayout(self)

        info = QLabel(
            "Revise os dados abaixo antes de importar.\n"
            "Escolha como deseja proceder:"
        )
        layout.addWidget(info)

        # 📋 Tabela
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Data", "Descrição", "Valor",
            "Tipo", "Pagamento", "Natureza", "Categoria"
        ])
        table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(row["entry_date"]))
            table.setItem(r, 1, QTableWidgetItem(row["description"]))
            table.setItem(r, 2, QTableWidgetItem(row["amount"]))
            table.setItem(r, 3, QTableWidgetItem(row["entry_type"]))
            table.setItem(r, 4, QTableWidgetItem(row["payment_method"]))
            table.setItem(r, 5, QTableWidgetItem(row["nature"]))
            table.setItem(r, 6, QTableWidgetItem(row["category"]))

        table.resizeColumnsToContents()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)

        # 🔘 Botões
        buttons = QHBoxLayout()

        ignore_btn = QPushButton("Ignorar duplicados")
        overwrite_btn = QPushButton("Sobrescrever tudo")
        cancel_btn = QPushButton("Cancelar")

        buttons.addStretch()
        buttons.addWidget(ignore_btn)
        buttons.addWidget(overwrite_btn)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        ignore_btn.clicked.connect(self._ignore)
        overwrite_btn.clicked.connect(self._overwrite)
        cancel_btn.clicked.connect(self.reject)

    def _ignore(self):
        self.mode = "ignore"
        self.accept()

    def _overwrite(self):
        confirm = QMessageBox.question(
            self,
            "Confirmar sobrescrita",
            "⚠️ Isso apagará TODOS os lançamentos atuais.\nDeseja continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.mode = "overwrite"
            self.accept()
