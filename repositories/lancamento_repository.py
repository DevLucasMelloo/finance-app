from domain.lancamento import Lancamento, EntryType, PaymentMethod, NatureType
from infrastructure.database import get_connection, to_date
from infrastructure.enum_mapper import enum_from_db


class LancamentoRepository:

    def add(self, lancamento: Lancamento) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO lancamentos (
                    entry_date, amount, entry_type, payment_method,
                    category, nature, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    lancamento.entry_date,
                    lancamento.amount,
                    lancamento.entry_type.value,
                    lancamento.payment_method.value,
                    lancamento.category,
                    lancamento.nature.value,
                    lancamento.description,
                ),
            )

    def list_all(self) -> list[Lancamento]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM lancamentos").fetchall()

        return [
            Lancamento(
                entry_date=to_date(row["entry_date"]),
                amount=row["amount"],
                entry_type=EntryType(row["entry_type"]),
                payment_method=PaymentMethod(row["payment_method"]),
                category=row["category"],
                nature=NatureType(row["nature"]),
                description=row["description"],
            )
            for row in rows
        ]

    def get_last(self):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM lancamentos ORDER BY id DESC LIMIT 1"
            ).fetchone()

    def get_by_id(self, lancamento_id: int):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT id, entry_date, description, amount,
                       entry_type, payment_method, nature, category
                FROM lancamentos WHERE id = %s
                """,
                (lancamento_id,),
            ).fetchone()

    def update(self, lancamento_id: int, lancamento: Lancamento):
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE lancamentos SET
                    entry_date = %s, description = %s, amount = %s,
                    entry_type = %s, payment_method = %s,
                    nature = %s, category = %s
                WHERE id = %s
                """,
                (
                    lancamento.entry_date,
                    lancamento.description,
                    lancamento.amount,
                    lancamento.entry_type.value,
                    lancamento.payment_method.value,
                    lancamento.nature.value,
                    lancamento.category,
                    lancamento_id,
                ),
            )

    def delete(self, lancamento_id: int):
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM lancamentos WHERE id = %s", (lancamento_id,)
            )

    def add_from_investment(
        self, amount: float, nature: "NatureType", description: str, is_income: bool
    ) -> int:
        from domain.lancamento import EntryType, PaymentMethod
        from datetime import date

        entry_type = EntryType.INCOME if is_income else EntryType.EXPENSE
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO lancamentos (
                    entry_date, amount, entry_type, payment_method,
                    category, nature, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    date.today(),
                    amount,
                    entry_type.value,
                    PaymentMethod.PIX.value,
                    "Investimento",
                    nature.value,
                    description,
                ),
            )
            return cur.fetchone()["id"]

    def add_transferencia(self, amount, from_nature, to_nature):
        from datetime import date
        from domain.lancamento import EntryType

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO lancamentos (
                    entry_date, description, amount, entry_type,
                    from_nature, to_nature
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    date.today(),
                    f"Transferência {from_nature} → {to_nature}",
                    amount,
                    EntryType.TRANSFER.value,
                    from_nature,
                    to_nature,
                ),
            )
