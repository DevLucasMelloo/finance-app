from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QTabWidget, QComboBox,
    QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QColor

from repositories.investment_repository import InvestmentRepository
from services.price_service import PriceService, TICKER_CARDS, COINGECKO_IDS
from ui.compra_ativo_dialog import CompraAtivoDialog
from ui.venda_ativo_dialog import VendaAtivoDialog
from ui.editar_compra_dialog import EditarCompraDialog


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_qty(v: float) -> str:
    if v >= 1:
        return f"{v:,.4f}"
    return f"{v:.8f}"


# ==========================
# WORKER THREAD — busca preços sem travar a UI
# ==========================
class PriceFetchWorker(QThread):
    prices_ready = Signal(dict)

    def __init__(self, price_service: PriceService):
        super().__init__()
        self.price_service = price_service

    def run(self):
        prices = self.price_service.get_prices()
        self.prices_ready.emit(prices)


class InvestimentosView(QWidget):
    data_changed = Signal()  # emitido após qualquer operação que altera saldo

    def __init__(self):
        super().__init__()
        self.repo = InvestmentRepository()
        self.price_service = PriceService()
        self._currency = "usd"
        self._prices = {}
        self._worker: PriceFetchWorker | None = None
        self._history_data: list = []
        self._positions_data: list = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        layout.addWidget(self._build_ticker_bar())
        layout.addWidget(self._build_performance_bar())

        self.inner_tabs = QTabWidget()
        self.inner_tabs.addTab(self._build_positions_tab(), "Posições Abertas")
        self.inner_tabs.addTab(self._build_history_tab(), "Histórico de Operações")
        layout.addWidget(self.inner_tabs)

        # Timer 30s — dispara fetch em background
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._fetch_prices_async)
        self._timer.start(30_000)

        # Carrega dados locais imediatamente
        self._refresh_positions()
        self._refresh_history()

        # Busca preços em background (não bloqueia janela)
        self._fetch_prices_async()

    # ==========================
    # FETCH ASSÍNCRONO
    # ==========================
    def _fetch_prices_async(self):
        if self._worker and self._worker.isRunning():
            return
        self.lbl_last_update.setText("Buscando preços...")
        self._worker = PriceFetchWorker(self.price_service)
        self._worker.prices_ready.connect(self._on_prices_ready)
        self._worker.start()

    def _on_prices_ready(self, prices: dict):
        from datetime import datetime
        self._prices = prices
        currency = self._currency

        any_nonzero = False
        for ticker, lbl in self._ticker_labels.items():
            val = prices.get(ticker, {}).get(currency, 0.0)
            if val > 0:
                any_nonzero = True
            symbol = "$ " if currency == "usd" else "R$ "
            text = f"{symbol}{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            lbl.setText(text)
            lbl.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #e65100; border: none;"
                if val > 0 else
                "font-size: 15px; font-weight: bold; color: #bbb; border: none;"
            )

        if any_nonzero:
            now = datetime.now().strftime("%H:%M:%S")
            self.lbl_last_update.setText(f"Atualizado {now}")
        else:
            self.lbl_last_update.setText("Sem conexão — exibindo última leitura")

        self._refresh_positions()

    # ==========================
    # TICKER BAR — estilo clean (igual ao Resumo)
    # ==========================
    def _build_ticker_bar(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        self._ticker_labels: dict[str, QLabel] = {}

        for ticker in TICKER_CARDS:
            price_lbl = QLabel("—")
            price_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #bbb; border: none;")
            price_lbl.setAlignment(Qt.AlignCenter)
            self._ticker_labels[ticker] = price_lbl

            card = self._ticker_card(ticker, price_lbl)
            row.addWidget(card)

        row.addStretch()

        # Toggle moeda
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("USDT", "usd")
        self.currency_combo.addItem("BRL", "brl")
        self.currency_combo.setFixedWidth(80)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        row.addWidget(self.currency_combo)

        self.lbl_last_update = QLabel("Buscando preços...")
        self.lbl_last_update.setStyleSheet("color: #aaa; font-size: 10px;")
        row.addWidget(self.lbl_last_update)

        return container

    def _ticker_card(self, ticker: str, price_lbl: QLabel) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px solid #e0e0e0; border-radius: 8px; background: #ffffff; }"
        )
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(72)
        card.setMaximumWidth(180)

        col = QVBoxLayout(card)
        col.setAlignment(Qt.AlignCenter)
        col.setSpacing(2)

        name_lbl = QLabel(ticker)
        name_lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: bold; border: none;")
        name_lbl.setAlignment(Qt.AlignCenter)

        col.addWidget(name_lbl)
        col.addWidget(price_lbl)
        return card

    # ==========================
    # PERFORMANCE CARDS
    # ==========================
    def _build_performance_bar(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        self.lbl_total_invest = QLabel("R$ 0,00")
        self.lbl_valor_atual = QLabel("R$ 0,00")
        self.lbl_lucro = QLabel("R$ 0,00")
        self.lbl_rentab = QLabel("0,00%")

        row.addWidget(self._perf_card("Total Investido", self.lbl_total_invest, "#1565c0"))
        row.addWidget(self._perf_card("Valor Atual", self.lbl_valor_atual, "#00695c"))
        row.addWidget(self._perf_card("Lucro / Prejuízo", self.lbl_lucro, "#2e7d32"))
        row.addWidget(self._perf_card("Rentabilidade", self.lbl_rentab, "#6a1b9a"))

        return container

    def _perf_card(self, title: str, lbl: QLabel, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px solid #e0e0e0; border-radius: 8px; background: #ffffff; }"
        )
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(72)

        col = QVBoxLayout(card)
        col.setAlignment(Qt.AlignCenter)
        col.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet("font-size: 11px; color: #888; border: none;")
        t.setAlignment(Qt.AlignCenter)

        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color}; border: none;")
        lbl.setAlignment(Qt.AlignCenter)

        col.addWidget(t)
        col.addWidget(lbl)
        return card

    # ==========================
    # ABA POSIÇÕES
    # ==========================
    def _build_positions_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        actions = QHBoxLayout()

        btn_new = QPushButton("+ Nova Compra")
        btn_new.setStyleSheet(
            "background: #2e7d32; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;"
        )
        btn_new.clicked.connect(self._open_buy)

        btn_buy_more = QPushButton("Comprar Mais")
        btn_buy_more.setStyleSheet(
            "background: #1565c0; color: white; padding: 6px 14px; border-radius: 4px;"
        )
        btn_buy_more.clicked.connect(self._open_buy_more)

        btn_sell = QPushButton("Vender")
        btn_sell.setStyleSheet(
            "background: #c62828; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;"
        )
        btn_sell.clicked.connect(self._open_sell)

        btn_delete_pos = QPushButton("Excluir Posição")
        btn_delete_pos.setStyleSheet(
            "background: #757575; color: white; padding: 6px 14px; border-radius: 4px;"
        )
        btn_delete_pos.clicked.connect(self._delete_position)

        btn_refresh = QPushButton("↻ Atualizar")
        btn_refresh.clicked.connect(lambda: (self._fetch_prices_async(), self._refresh_positions()))

        actions.addWidget(btn_new)
        actions.addWidget(btn_buy_more)
        actions.addWidget(btn_sell)
        actions.addWidget(btn_delete_pos)
        actions.addStretch()
        actions.addWidget(btn_refresh)
        layout.addLayout(actions)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(9)
        self.positions_table.setHorizontalHeaderLabels([
            "Ativo", "Corretora", "Quantidade",
            "Preço Médio", "Preço Atual", "Valor Atual",
            "Lucro R$", "Rent. %", "Tipo"
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.positions_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.positions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.verticalHeader().setVisible(False)
        self.positions_table.setMinimumHeight(200)

        layout.addWidget(self.positions_table)
        return widget

    # ==========================
    # ABA HISTÓRICO
    # ==========================
    def _build_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        hist_actions = QHBoxLayout()

        btn_edit_op = QPushButton("✏️ Editar Compra")
        btn_edit_op.setStyleSheet(
            "background: #1565c0; color: white; padding: 6px 14px; border-radius: 4px;"
        )
        btn_edit_op.clicked.connect(self._edit_operation)

        btn_delete_op = QPushButton("🗑️ Excluir Operação")
        btn_delete_op.setStyleSheet(
            "background: #c62828; color: white; padding: 6px 14px; border-radius: 4px;"
        )
        btn_delete_op.clicked.connect(self._delete_operation)

        btn_refresh_hist = QPushButton("↻ Atualizar")
        btn_refresh_hist.clicked.connect(self._refresh_history)

        hist_actions.addWidget(btn_edit_op)
        hist_actions.addWidget(btn_delete_op)
        hist_actions.addStretch()
        hist_actions.addWidget(btn_refresh_hist)
        layout.addLayout(hist_actions)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Data", "Ativo", "Corretora", "Tipo",
            "Quantidade", "Preço", "Total", "Resultado"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)

        layout.addWidget(self.history_table)
        return widget

    # ==========================
    # REFRESH POSIÇÕES
    # ==========================
    def _refresh_positions(self):
        self._positions_data = self.repo.get_open_positions()
        positions = self._positions_data
        self.positions_table.setRowCount(len(positions))

        total_invested = 0.0
        total_current = 0.0

        for row_idx, p in enumerate(positions):
            ticker = p["asset"].upper()
            current_price_brl = self._prices.get(ticker, {}).get("brl", 0.0)

            qty = p["total_quantity"]
            avg = p["avg_price"]
            invested = p["total_invested"]

            valor_atual = qty * current_price_brl if current_price_brl > 0 else invested
            lucro = valor_atual - invested
            rentab = (lucro / invested * 100) if invested > 0 else 0.0

            total_invested += invested
            total_current += valor_atual

            broker = p["broker"] or "—"
            asset_type = p["asset_type"] or "—"

            cols = [
                (ticker, Qt.AlignLeft),
                (broker, Qt.AlignLeft),
                (_fmt_qty(qty), Qt.AlignRight),
                (_fmt(avg), Qt.AlignRight),
                (_fmt(current_price_brl) if current_price_brl > 0 else "N/A", Qt.AlignRight),
                (_fmt(valor_atual), Qt.AlignRight),
                (_fmt(lucro), Qt.AlignRight),
                (f"{rentab:+.2f}%".replace(".", ","), Qt.AlignRight),
                (asset_type, Qt.AlignCenter),
            ]

            for col_idx, (text, align) in enumerate(cols):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align | Qt.AlignVCenter)
                if col_idx in (6, 7):
                    item.setForeground(QColor("#2e7d32") if lucro >= 0 else QColor("#c62828"))
                self.positions_table.setItem(row_idx, col_idx, item)

        lucro_total = total_current - total_invested
        rentab_total = (lucro_total / total_invested * 100) if total_invested > 0 else 0.0

        self.lbl_total_invest.setText(_fmt(total_invested))
        self.lbl_valor_atual.setText(_fmt(total_current))

        color_lucro = "#2e7d32" if lucro_total >= 0 else "#c62828"
        sign = "+" if lucro_total >= 0 else ""
        self.lbl_lucro.setText(f"{sign}{_fmt(lucro_total)}")
        self.lbl_lucro.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color_lucro}; border: none;")

        color_rent = "#2e7d32" if rentab_total >= 0 else "#c62828"
        self.lbl_rentab.setText(f"{rentab_total:+.2f}%".replace(".", ","))
        self.lbl_rentab.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color_rent}; border: none;")

    # ==========================
    # REFRESH HISTÓRICO
    # ==========================
    def _refresh_history(self):
        self._history_data = self.repo.get_all_history()
        history = self._history_data
        self.history_table.setRowCount(len(history))

        for row_idx, op in enumerate(history):
            tipo = op["tipo"]
            profit = op["profit"]

            if profit is not None:
                sign = "+" if profit >= 0 else ""
                profit_text = f"{sign}{_fmt(profit)}"
            else:
                profit_text = "—"

            cols = [
                (op["date"], Qt.AlignCenter),
                (op["asset"], Qt.AlignLeft),
                (op["broker"] or "—", Qt.AlignLeft),
                (tipo, Qt.AlignCenter),
                (_fmt_qty(op["quantity"]), Qt.AlignRight),
                (_fmt(op["price"]), Qt.AlignRight),
                (_fmt(op["total_value"]), Qt.AlignRight),
                (profit_text, Qt.AlignRight),
            ]

            for col_idx, (text, align) in enumerate(cols):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align | Qt.AlignVCenter)
                if col_idx == 3:
                    item.setForeground(QColor("#2e7d32") if tipo == "COMPRA" else QColor("#c62828"))
                if col_idx == 7 and profit is not None:
                    item.setForeground(QColor("#2e7d32") if profit >= 0 else QColor("#c62828"))
                self.history_table.setItem(row_idx, col_idx, item)

    def _on_currency_changed(self):
        self._currency = self.currency_combo.currentData()
        if self._prices:
            self._on_prices_ready(self._prices)
        else:
            self._fetch_prices_async()

    # ==========================
    # AÇÕES DOS BOTÕES
    # ==========================
    def _open_buy(self):
        dialog = CompraAtivoDialog(current_prices=self._prices)
        if dialog.exec():
            self._refresh_positions()
            self._refresh_history()
            self.data_changed.emit()

    def _open_buy_more(self):
        p = self._get_selected_position()
        if not p:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Atenção", "Selecione uma posição na tabela primeiro.")
            return
        dialog = CompraAtivoDialog(asset=p["asset"], position=p, current_prices=self._prices)
        if dialog.exec():
            self._refresh_positions()
            self._refresh_history()
            self.data_changed.emit()

    def _open_sell(self):
        p = self._get_selected_position()
        dialog = VendaAtivoDialog(position=p)
        if dialog.exec():
            self._refresh_positions()
            self._refresh_history()
            self.data_changed.emit()

    def _get_selected_position(self):
        row = self.positions_table.currentRow()
        if row < 0 or row >= len(self._positions_data):
            return None
        return self._positions_data[row]

    def _get_selected_history_row(self):
        row = self.history_table.currentRow()
        if row < 0 or row >= len(self._history_data):
            return None
        return self._history_data[row]

    # ==========================
    # EXCLUIR POSIÇÃO
    # ==========================
    def _delete_position(self):
        from PySide6.QtWidgets import QMessageBox
        p = self._get_selected_position()
        if not p:
            QMessageBox.information(self, "Atenção", "Selecione uma posição na tabela primeiro.")
            return

        resp = QMessageBox.question(
            self, "Excluir Posição",
            f"Deseja excluir a posição {p['asset']} e todas as operações vinculadas?\n\n"
            "Os lançamentos financeiros correspondentes também serão removidos.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return

        self.repo.delete_position(p["id"])
        self._refresh_positions()
        self._refresh_history()
        self.data_changed.emit()

    # ==========================
    # EXCLUIR OPERAÇÃO (compra ou venda)
    # ==========================
    def _delete_operation(self):
        from PySide6.QtWidgets import QMessageBox
        op = self._get_selected_history_row()
        if not op:
            QMessageBox.information(self, "Atenção", "Selecione uma operação no histórico primeiro.")
            return

        tipo = op["tipo"]
        resp = QMessageBox.question(
            self, "Excluir Operação",
            f"Deseja excluir esta {tipo.lower()} de {op['asset']}?\n"
            f"Qtd: {op['quantity']} | Preço: {_fmt(op['price'])} | Data: {op['date']}\n\n"
            "O lançamento financeiro correspondente também será removido.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return

        position_id = op["position_id"]
        if tipo == "COMPRA":
            self.repo.delete_buy(op["op_id"])
        else:
            self.repo.delete_sell(op["op_id"])

        self.repo.recalculate_position(position_id)
        self._refresh_positions()
        self._refresh_history()
        self.data_changed.emit()

    # ==========================
    # EDITAR COMPRA
    # ==========================
    def _edit_operation(self):
        from PySide6.QtWidgets import QMessageBox
        op = self._get_selected_history_row()
        if not op:
            QMessageBox.information(self, "Atenção", "Selecione uma operação no histórico primeiro.")
            return

        if op["tipo"] != "COMPRA":
            QMessageBox.information(self, "Atenção", "Somente compras podem ser editadas.")
            return

        buy_row = self.repo.get_buy(op["op_id"])
        position_row = self.repo.get_position(op["position_id"])

        if not buy_row or not position_row:
            QMessageBox.warning(self, "Erro", "Registro não encontrado.")
            return

        dialog = EditarCompraDialog(buy_row, position_row)
        if dialog.exec():
            self._refresh_positions()
            self._refresh_history()
            self.data_changed.emit()
