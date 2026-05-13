from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor
from infrastructure.database import get_connection, to_date

_COL_KEYS = [
    "entry_date", "description", "amount",
    "entry_type", "payment_method", "nature", "category",
]


class LancamentosTableModel(QAbstractTableModel):
    headers = ["Data", "Descrição", "Valor", "Tipo", "Pagamento", "Natureza", "Categoria"]

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
    # CONTROLE
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
    # WHERE
    # ==========================
    def _build_where(self):
        where = " WHERE 1=1 "
        params = []

        if self.filters.get("start_date"):
            where += " AND entry_date >= %s"
            params.append(self.filters["start_date"])

        if self.filters.get("end_date"):
            where += " AND entry_date <= %s"
            params.append(self.filters["end_date"])

        if self.filters.get("entry_type"):
            where += " AND entry_type = %s"
            params.append(self.filters["entry_type"])

        if self.filters.get("nature"):
            where += " AND nature = %s"
            params.append(self.filters["nature"])

        if self.search_text:
            where += """
                AND (
                    description ILIKE %s
                    OR category ILIKE %s
                    OR payment_method ILIKE %s
                )
            """
            like = f"%{self.search_text}%"
            params.extend([like, like, like])

        return where, params

    # ==========================
    # LOAD
    # ==========================
    def _load_and_reset(self):
        self.beginResetModel()

        offset = (self.page - 1) * self.page_size
        where, params = self._build_where()

        with get_connection() as conn:
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
                    'LANCAMENTO' AS __tipo__
                FROM lancamentos
                {where}
            """, params).fetchall()

            transfer_rows = conn.execute("""
                SELECT
                    id,
                    transfer_date           AS entry_date,
                    description,
                    amount,
                    'TRANSFERENCIA'         AS entry_type,
                    origin || ' → ' || destination AS payment_method,
                    destination             AS nature,
                    'Transferência'         AS category,
                    'TRANSFERENCIA'         AS __tipo__
                FROM transferencias
            """).fetchall()

        all_rows = list(lanc_rows) + list(transfer_rows)
        all_rows.sort(key=lambda r: to_date(r["entry_date"]), reverse=True)

        self.total_rows = len(all_rows)
        self._data = all_rows[offset: offset + self.page_size]

        self.endResetModel()

    # ==========================
    # QT MODEL
    # ==========================
    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._data[index.row()]
        col_key = _COL_KEYS[index.column()]
        value = row[col_key]

        entry_type = row["entry_type"]
        nature = row["nature"]
        tipo_linha = row["__tipo__"]

        if role == Qt.DisplayRole:
            if col_key == "entry_date":
                d = to_date(value)
                return d.strftime("%d/%m/%Y") if d else ""
            if col_key == "amount":
                return f"R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return value if value is not None else ""

        if role == Qt.TextAlignmentRole:
            if col_key == "amount":
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            if tipo_linha == "TRANSFERENCIA":
                return QColor("#4e4e4e")
            if nature == "INVESTIMENTO":
                return QColor("#ef6c00")
            if nature == "RESERVA":
                return QColor("#6a1b9a")
            if entry_type == "PROVENTO":
                return QColor("#2e7d32")
            if entry_type == "DESPESA":
                return QColor("#c62828")

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    # ==========================
    # HELPERS
    # ==========================
    def get_row(self, row_index: int):
        return self._data[row_index]

    def get_id(self, row_index: int):
        return self._data[row_index]["id"]
