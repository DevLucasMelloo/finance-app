from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QTableView, QPushButton,
    QComboBox, QDateEdit,
    QLabel, QTabWidget,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import QDate, Qt
from ui.lancamentos_table import LancamentosTableModel
from ui.novo_lancamento_dialog import NovoLancamentoDialog
from core.finance_app_service import FinanceAppService
from domain.lancamento import NatureType, EntryType
from repositories.lancamento_repository import LancamentoRepository
from repositories.transferencia_repository import TransferenciaRepository
from ui.import_preview_dialog import ImportPreviewDialog
from ui.transferencia_dialog import TransferenciaDialog
from ui.distribuicao_chart import DistribuicaoChart
from ui.evolucao_chart import EvolucaoChart
from datetime import date

def format_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Finance App")
        self.resize(1000, 600)
        self.mes_filtro = date.today().month
        self.ano_filtro = date.today().year

        self.tabs = QTabWidget()

        self.tabs.addTab(self._resumo_tab(), "Resumo")
        self.tabs.addTab(self._lancamentos_tab(), "Lançamentos")
        self.tabs.addTab(self._investimentos_tab(), "Investimentos")

        self.setCentralWidget(self.tabs)
        self._update_resumo()

    # ----------------------------
    # ABA RESUMO
    # ----------------------------
    def _resumo_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==========================
        # 🔘 FILTROS MÊS / ANO
        # ==========================
        filtros = QHBoxLayout()

        self.cmb_mes = QComboBox()
        self.cmb_ano = QComboBox()

        self.cmb_mes.addItem("Todos", None)
        for m in range(1, 13):
            self.cmb_mes.addItem(f"{m:02d}", m)

        ano_atual = date.today().year
        self.cmb_ano.addItem("Todos", None)
        for a in range(ano_atual - 5, ano_atual + 1):
            self.cmb_ano.addItem(str(a), a)

        filtros.addWidget(QLabel("Mês:"))
        filtros.addWidget(self.cmb_mes)
        filtros.addWidget(QLabel("Ano:"))
        filtros.addWidget(self.cmb_ano)
        filtros.addStretch()

        layout.addLayout(filtros)

        # 🔗 CONECTA FILTROS
        self.cmb_mes.currentIndexChanged.connect(self._update_resumo)
        self.cmb_ano.currentIndexChanged.connect(self._update_resumo)

        # ==========================
        # 📊 CARDS
        # ==========================
        grid = QHBoxLayout()

        self.lbl_saldo = QLabel("R$ 0,00")
        self.lbl_proventos = QLabel("R$ 0,00")
        self.lbl_despesas = QLabel("R$ 0,00")
        self.lbl_caixa = QLabel("R$ 0,00")
        self.lbl_investimentos = QLabel("R$ 0,00")
        self.lbl_reserva = QLabel("R$ 0,00")

        grid.addWidget(self._total_card("Saldo Total", self.lbl_saldo, "#1565c0"))
        grid.addWidget(self._total_card("Proventos", self.lbl_proventos, "#2e7d32"))
        grid.addWidget(self._total_card("Despesas", self.lbl_despesas, "#c62828"))
        grid.addWidget(self._total_card("Caixa", self.lbl_caixa, "#150358"))
        grid.addWidget(self._total_card("Investimentos", self.lbl_investimentos, "#ef6c00"))
        grid.addWidget(self._total_card("Reserva", self.lbl_reserva, "#6a1b9a"))

        layout.addLayout(grid)

        # 🔒 GRÁFICOS NÃO MEXEMOS
        layout.addWidget(DistribuicaoChart())
        layout.addWidget(EvolucaoChart())

        self._update_resumo()
        return widget

    # =====================================================
    # 🔄 ATUALIZA RESUMO (COM FILTRO)
    # =====================================================
    def _update_resumo(self):
        mes = self.cmb_mes.currentData()
        ano = self.cmb_ano.currentData()

        lancamentos = LancamentoRepository().list_all()
        transferencias = TransferenciaRepository().list_all()

        def match_data(d):
            if ano and d.year != ano:
                return False
            if mes and d.month != mes:
                return False
            return True

        caixa = investimento = reserva = 0.0
        proventos = despesas = 0.0

        for l in lancamentos:
            if not match_data(l.entry_date):
                continue

            valor = l.amount if l.entry_type == EntryType.INCOME else -l.amount

            if l.nature == NatureType.CASH:
                caixa += valor
            elif l.nature == NatureType.INVESTMENT:
                investimento += valor
            elif l.nature == NatureType.RESERVE:
                reserva += valor

            if l.entry_type == EntryType.INCOME:
                proventos += l.amount
            else:
                despesas += l.amount

        for t in transferencias:
            if not match_data(t.transfer_date):
                continue

            if t.origin == NatureType.CASH:
                caixa -= t.amount
            if t.destination == NatureType.CASH:
                caixa += t.amount

            if t.origin == NatureType.INVESTMENT:
                investimento -= t.amount
            if t.destination == NatureType.INVESTMENT:
                investimento += t.amount

            if t.origin == NatureType.RESERVE:
                reserva -= t.amount
            if t.destination == NatureType.RESERVE:
                reserva += t.amount

        saldo_total = caixa + investimento + reserva

        self.lbl_caixa.setText(format_brl(caixa))
        self.lbl_investimentos.setText(format_brl(investimento))
        self.lbl_reserva.setText(format_brl(reserva))
        self.lbl_saldo.setText(format_brl(saldo_total))
        self.lbl_proventos.setText(format_brl(proventos))
        self.lbl_despesas.setText(format_brl(despesas))

    def on_period_changed(self, mes: int, ano: int):
        self.mes_filtro = mes
        self.ano_filtro = ano
        self._update_resumo()

    # ----------------------------
    # ABA LANÇAMENTOS
    # ----------------------------
    def _lancamentos_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==========================
        # 📋 TABELA + MODEL (ÚNICO)
        # ==========================
        table = QTableView()
        model = LancamentosTableModel()
        table.setModel(model)

        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectRows)
        table.setSelectionMode(QTableView.SingleSelection)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(36)
        table.horizontalHeader().setStretchLastSection(True)

        # ==========================
        # 🔍 BUSCA
        # ==========================
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 Buscar por descrição, categoria ou pagamento...")
        search_input.textChanged.connect(model.set_search)

        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)

        # ==========================
        # 🎛 FILTROS
        # ==========================
        filters_layout = QHBoxLayout()

        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate().addMonths(-1))

        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDate(QDate.currentDate())

        entry_type = QComboBox()
        entry_type.addItem("Todos", None)
        entry_type.addItem("PROVENTO", "PROVENTO")
        entry_type.addItem("DESPESA", "DESPESA")

        nature = QComboBox()
        nature.addItem("Todas", None)
        nature.addItem("CAIXA", "CAIXA")
        nature.addItem("INVESTIMENTO", "INVESTIMENTO")
        nature.addItem("RESERVA", "RESERVA")

        filter_btn = QPushButton("Filtrar")

        filters_layout.addWidget(QLabel("De:"))
        filters_layout.addWidget(start_date)
        filters_layout.addWidget(QLabel("Até:"))
        filters_layout.addWidget(end_date)
        filters_layout.addWidget(QLabel("Tipo:"))
        filters_layout.addWidget(entry_type)
        filters_layout.addWidget(QLabel("Natureza:"))
        filters_layout.addWidget(nature)
        filters_layout.addWidget(filter_btn)

        layout.addLayout(filters_layout)

        # ==========================
        # ➕ AÇÕES
        # ==========================
        actions = QHBoxLayout()

        new_btn = QPushButton("+ Novo")
        edit_btn = QPushButton("✏️ Editar")
        delete_btn = QPushButton("🗑️ Excluir")
        import_btn = QPushButton("📥 Importar")
        export_btn = QPushButton("📤 Exportar Backup")
        transfer_btn = QPushButton("🔁 Transferir")

        actions.addStretch()
        actions.addWidget(new_btn)
        actions.addWidget(edit_btn)
        actions.addWidget(delete_btn)
        actions.addWidget(import_btn)
        actions.addWidget(export_btn)
        actions.addWidget(transfer_btn)

        layout.addLayout(actions)

        # ==========================
        # 📄 PAGINAÇÃO
        # ==========================
        pagination = QHBoxLayout()

        prev_btn = QPushButton("⏮ Anterior")
        next_btn = QPushButton("Próxima ⏭")

        page_label = QLabel()
        page_label.setAlignment(Qt.AlignCenter)

        page_size = QComboBox()
        page_size.addItems(["10", "20", "50"])
        page_size.setCurrentText("10")

        pagination.addWidget(prev_btn)
        pagination.addWidget(page_label)
        pagination.addWidget(next_btn)
        pagination.addStretch()
        pagination.addWidget(QLabel("Por página:"))
        pagination.addWidget(page_size)

        layout.addLayout(pagination)

        # ==========================
        # 📋 TABELA
        # ==========================
        layout.addWidget(table)

        # ==========================
        # 🔁 HELPERS
        # ==========================
        def update_page_label():
            total_pages = max(1, (model.total_rows + model.page_size - 1) // model.page_size)
            page_label.setText(f"Página {model.page} de {total_pages}")

            prev_btn.setEnabled(model.page > 1)
            next_btn.setEnabled(model.page < total_pages)

        def reload_table():
            model._load_and_reset()
            update_page_label()

        # ==========================
        # 🔘 PAGINAÇÃO AÇÕES
        # ==========================
        prev_btn.clicked.connect(lambda: (
            model.set_page(model.page - 1),
            update_page_label()
        ))

        next_btn.clicked.connect(lambda: (
            model.set_page(model.page + 1),
            update_page_label()
        ))

        page_size.currentTextChanged.connect(
            lambda v: (
                model.set_page_size(int(v)),
                update_page_label()
            )
        )

        # ==========================
        # 🔘 FILTRAR
        # ==========================
        def apply_filters():
            model.set_filters({
                "start_date": start_date.date().toString("yyyy-MM-dd"),
                "end_date": end_date.date().toString("yyyy-MM-dd"),
                "entry_type": entry_type.currentData(),
                "nature": nature.currentData(),
            })
            update_page_label()

        filter_btn.clicked.connect(apply_filters)

        # ==========================
        # 🔘 CRUD
        # ==========================

        def open_transfer():
            dialog = TransferenciaDialog()
            if dialog.exec():
                reload_table()
                self._update_resumo()

        def open_new():
            dialog = NovoLancamentoDialog()
            if dialog.exec():
                reload_table()
                self._update_resumo()

        def edit_item():
            index = table.currentIndex()
            if not index.isValid():
                QMessageBox.warning(self, "Atenção", "Selecione um item.")
                return

            row = model.get_row(index.row())
            tipo = row[-1]

            # 🔁 TRANSFERÊNCIA
            if tipo == "TRANSFERENCIA":
                from repositories.transferencia_repository import TransferenciaRepository
                repo = TransferenciaRepository()
                transferencia = repo.get_by_id(row[0])

                if not transferencia:
                    QMessageBox.warning(self, "Erro", "Transferência não encontrada.")
                    return

                dialog = TransferenciaDialog(transferencia)
                if dialog.exec():
                    reload_table()
                    self._update_resumo()
                return

            # 📄 LANÇAMENTO
            dialog = NovoLancamentoDialog(row)
            if dialog.exec():
                reload_table()
                self._update_resumo()


        def delete_item():
            index = table.currentIndex()
            if not index.isValid():
                QMessageBox.warning(self, "Atenção", "Selecione um item.")
                return

            row = model.get_row(index.row())
            tipo = row[-1]

            if QMessageBox.question(
                self, "Confirmar", "Deseja excluir?",
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return

            if tipo == "TRANSFERENCIA":
                from repositories.transferencia_repository import TransferenciaRepository
                TransferenciaRepository().delete(row[0])
            else:
                LancamentoRepository().delete(row[0])

            reload_table()
            self._update_resumo()

        # 🔗 CONEXÕES
        new_btn.clicked.connect(open_new)
        edit_btn.clicked.connect(edit_item)
        delete_btn.clicked.connect(delete_item)
        transfer_btn.clicked.connect(open_transfer)
        import_btn.clicked.connect(lambda: self.import_backup())
        export_btn.clicked.connect(lambda: self.export_backup())

        table.doubleClicked.connect(edit_item)


        update_page_label()
        return widget

    # ----------------------------
    # ABA INVESTIMENTOS
    # ----------------------------
    def _investimentos_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Área de investimentos"))

        return widget
    
    # ----------------------------
    # CARDS
    # ----------------------------
    def _total_card(self, title, value_label: QLabel, color):
        card = QWidget()
        card.setMinimumHeight(90)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666;")

        value_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {color};"
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card
    
    # ==========================
    # 📤 EXPORTAR BACKUP
    # ==========================
    def export_backup(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import csv
        from infrastructure.database import get_connection

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Backup",
            "finance_backup.csv",
            "CSV (*.csv)"
        )

        if not path:
            return

        with get_connection() as conn:
            # 🔹 LANÇAMENTOS
            lancamentos = conn.execute("""
                SELECT
                    'LANCAMENTO' as tipo_registro,
                    entry_date as data,
                    description as descricao,
                    amount as valor,
                    entry_type as tipo,
                    payment_method as pagamento,
                    nature as natureza,
                    category as categoria,
                    NULL as origem,
                    NULL as destino
                FROM lancamentos
            """).fetchall()

            # 🔹 TRANSFERÊNCIAS
            transferencias = conn.execute("""
                SELECT
                    'TRANSFERENCIA' as tipo_registro,
                    transfer_date as data,
                    description as descricao,
                    amount as valor,
                    'TRANSFERENCIA' as tipo,
                    NULL as pagamento,
                    NULL as natureza,
                    'Transferência' as categoria,
                    origin as origem,
                    destination as destino
                FROM transferencias
            """).fetchall()

        rows = list(lancamentos) + list(transferencias)

        # ✅ UTF-8 COM BOM (corrige acentuação no Excel)
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")

            writer.writerow([
                "tipo_registro",
                "data",
                "descricao",
                "valor",
                "tipo",
                "pagamento",
                "natureza",
                "categoria",
                "origem",
                "destino",
            ])

            writer.writerows(rows)

        QMessageBox.information(
            self,
            "Exportação concluída",
            "Backup exportado com sucesso!\n\nCompatível com Excel."
        )

    # ==========================
    # 📤 IMPORT BACKUP
    # ==========================
    def import_backup(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import csv
        from infrastructure.database import get_connection
        from repositories.transferencia_repository import TransferenciaRepository
        from domain.transferencia import Transferencia
        from datetime import date
        from domain.lancamento import NatureType

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar backup",
            "",
            "CSV (*.csv)"
        )

        if not path:
            return

        # ==========================
        # 📥 LEITURA ROBUSTA DO CSV
        # ==========================
        try:
            try:
                with open(path, newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f, delimiter=";")
                    raw_rows = list(reader)
            except UnicodeDecodeError:
                with open(path, newline="", encoding="latin-1") as f:
                    reader = csv.DictReader(f, delimiter=";")
                    raw_rows = list(reader)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return

        if not raw_rows:
            QMessageBox.warning(self, "Arquivo vazio", "O CSV não contém dados.")
            return

        # ==========================
        # 🧼 NORMALIZAÇÃO
        # ==========================
        def parse_amount(raw):
            if not raw:
                return 0.0

            raw = raw.replace("R$", "").strip()

            # remove espaços
            raw = raw.replace(" ", "")

            # caso 1: formato brasileiro 1.234,56
            if "," in raw and raw.count(",") == 1:
                raw = raw.replace(".", "").replace(",", ".")
                return float(raw)

            # caso 2: formato americano 1234.56
            if raw.count(".") == 1:
                return float(raw)

            # caso 3: formato bugado do Excel 1.000.00
            if raw.count(".") > 1:
                parts = raw.split(".")
                raw = "".join(parts[:-1]) + "." + parts[-1]
                return float(raw)

            return float(raw)

        rows = []
        for r in raw_rows:
            rows.append({
                "tipo_registro": (r.get("tipo_registro") or "").strip(),
                "entry_date": (r.get("entry_date") or r.get("data") or "").strip(),
                "description": (r.get("description") or r.get("descricao") or "").strip(),
                "amount": parse_amount(r.get("amount") or r.get("valor")),
                "entry_type": (r.get("entry_type") or r.get("tipo") or "").strip(),
                "payment_method": (r.get("payment_method") or r.get("pagamento") or "").strip(),
                "nature": (r.get("nature") or r.get("natureza") or "").strip(),
                "category": (r.get("category") or r.get("categoria") or "").strip(),
                "origem": (r.get("origem") or "").strip(),
                "destino": (r.get("destino") or "").strip(),
            })

        # ==========================
        # 🔍 PREVIEW
        # ==========================
        preview = ImportPreviewDialog(rows)
        if not preview.exec():
            return

        with get_connection() as conn:
            cursor = conn.cursor()

            if preview.mode == "overwrite":
                cursor.execute("DELETE FROM lancamentos")
                cursor.execute("DELETE FROM transferencias")

            # ==========================
            # 📥 IMPORTAÇÃO
            # ==========================
            for row in rows:
                # 🔁 TRANSFERÊNCIA
                if row["tipo_registro"] == "TRANSFERENCIA":
                    transferencia = Transferencia(
                        id=None,
                        transfer_date=date.fromisoformat(row["entry_date"]),
                        amount=row["amount"],
                        origin=NatureType(row["origem"]),
                        destination=NatureType(row["destino"]),
                        description=row["description"],
                    )
                    TransferenciaRepository().add(transferencia)
                    continue

                # 📄 LANÇAMENTO
                cursor.execute("""
                    INSERT INTO lancamentos (
                        entry_date,
                        description,
                        amount,
                        entry_type,
                        payment_method,
                        nature,
                        category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["entry_date"],
                    row["description"],
                    row["amount"],
                    row["entry_type"],
                    row["payment_method"],
                    row["nature"],
                    row["category"]
                ))

            conn.commit()

        QMessageBox.information(
            self,
            "Importação concluída",
            "Lançamentos e transferências importados com sucesso!"
        )

        self._update_resumo()
