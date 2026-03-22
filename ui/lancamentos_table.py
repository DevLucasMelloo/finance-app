from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor
from datetime import datetime
from infrastructure.database import get_connection


class LancamentosTableModel(QAbstractTableModel):
    headers = [
        "Data",
        "Descrição",
        "Valor",
        "Tipo",
        "Pagamento",
        "Natureza",
        "Categoria",
    ]

    def __init__(self):
        super().__init__()
        self.filters = {}
        self.search_text = ""
        self.page = 1
        self.page_size = 10
        self.total_rows = 0
        self._data = []
        self._load_and_reset()

    # ==========================
    # 🔁 CONTROLE
    # ==========================
    def set_filters(self, filters: dict):
        self.filters = filters
        self.page = 1
        self._load_and_reset()

    def set_search(self, text: str):
        self.search_text = text.strip()
        self.page = 1
        self._load_and_reset()

    def set_page(self, page: int):
        if page >= 1:
            self.page = page
            self._load_and_reset()

    def set_page_size(self, size: int):
        self.page_size = size
        self.page = 1
        self._load_and_reset()

    # ==========================
    # 📊 WHERE
    # ==========================
    def _build_where(self):
        where = " WHERE 1=1 "
        params = []

        if self.filters.get("start_date"):
            where += " AND entry_date >= ?"
            params.append(self.filters["start_date"])

        if self.filters.get("end_date"):
            where += " AND entry_date <= ?"
            params.append(self.filters["end_date"])

        if self.filters.get("entry_type"):
            where += " AND entry_type = ?"
            params.append(self.filters["entry_type"])

        if self.filters.get("nature"):
            where += " AND nature = ?"
            params.append(self.filters["nature"])

        if self.search_text:
            where += """
                AND (
                    description LIKE ?
                    OR category LIKE ?
                    OR payment_method LIKE ?
                )
            """
            like = f"%{self.search_text}%"
            params.extend([like, like, like])

        return where, params

    # ==========================
    # 🔄 LOAD
    # ==========================
    def _load_and_reset(self):
        self.beginResetModel()

        offset = (self.page - 1) * self.page_size
        where, params = self._build_where()

        with get_connection() as conn:
            # 📄 LANÇAMENTOS
            lanc_rows = conn.execute(f"""
                SELECT
                    id,
                    entry_date,
                    description,
                    amount,
                    entry_type,
                    payment_method,
                    nature,
                    category,
                    'LANCAMENTO' as __tipo__
                FROM lancamentos
                {where}
            """, params).fetchall()

            # 🔁 TRANSFERÊNCIAS
            transfer_rows = conn.execute("""
                SELECT
                    id,
                    transfer_date,
                    'Transferência interna',
                    amount,
                    'TRANSFERENCIA',
                    origin || ' → ' || destination,
                    destination,
                    'Transferência',
                    'TRANSFERENCIA' as __tipo__
                FROM transferencias
            """).fetchall()

        # 🔀 UNIR + ORDENAR
        all_rows = list(lanc_rows) + list(transfer_rows)
        all_rows.sort(key=lambda r: r[1], reverse=True)

        self.total_rows = len(all_rows)
        self._data = all_rows[offset: offset + self.page_size]

        self.endResetModel()

    # ==========================
    # 📋 QT MODEL
    # ==========================
    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._data[index.row()]
        value = row[index.column() + 1]

        entry_type = row[4]   # PROVENTO / DESPESA / TRANSFERENCIA
        nature = row[6]       # CAIXA / INVESTIMENTO / RESERVA
        tipo_linha = row[-1]  # LANCAMENTO / TRANSFERENCIA

        # --------------------
        # TEXTO
        # --------------------
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return datetime.fromisoformat(value).strftime("%d/%m/%Y")

            if index.column() == 2:
                return f"R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            return value

        # --------------------
        # ALINHAMENTO
        # --------------------
        if role == Qt.TextAlignmentRole:
            if index.column() == 2:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        # --------------------
        # CORES
        # --------------------
        if role == Qt.ForegroundRole:

            # 🔁 TRANSFERÊNCIA (prioridade máxima)
            if tipo_linha == "TRANSFERENCIA":
                return QColor("#4e4e4e")  # cinza

            # 🟠 INVESTIMENTO
            if nature == "INVESTIMENTO":
                return QColor("#ef6c00")  # laranja

            # 🟣 RESERVA
            if nature == "RESERVA":
                return QColor("#6a1b9a")  # roxo

            # 🟢 PROVENTO (CAIXA)
            if entry_type == "PROVENTO":
                return QColor("#2e7d32")  # verde

            # 🔴 DESPESA (CAIXA)
            if entry_type == "DESPESA":
                return QColor("#c62828")  # vermelho

        return None


    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    # ==========================
    # 🔧 HELPERS
    # ==========================
    def get_row(self, row_index: int):
        return self._data[row_index]

    def get_id(self, row_index: int):
        return self._data[row_index][0]
