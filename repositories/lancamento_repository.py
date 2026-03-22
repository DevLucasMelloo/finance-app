from datetime import date
from domain.lancamento import Lancamento, EntryType, PaymentMethod, NatureType
from infrastructure.database import get_connection
from infrastructure.enum_mapper import enum_from_db


class LancamentoRepository:
    def add(self, lancamento: Lancamento) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO lancamentos (
                    entry_date,
                    amount,
                    entry_type,
                    payment_method,
                    category,
                    nature,
                    description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lancamento.entry_date.isoformat(),
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

        lancamentos: list[Lancamento] = []

        for row in rows:
            lancamentos.append(
                Lancamento(
                    entry_date=date.fromisoformat(row["entry_date"]),
                    amount=row["amount"],
                    entry_type=EntryType(row["entry_type"]),
                    payment_method=PaymentMethod(row["payment_method"]),
                    category=row["category"],
                    nature=NatureType(row["nature"]),
                    description=row["description"],
                )
            )

        return lancamentos
    
    def delete(self, lancamento_id: int):
        from infrastructure.database import get_connection

        with get_connection() as conn:
            conn.execute(
                "DELETE FROM lancamentos WHERE id = ?",
                (lancamento_id,)
            )
            conn.commit()

    def get_by_id(self, lancamento_id: int):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    id,
                    entry_date,
                    description,
                    amount,
                    entry_type,
                    payment_method,
                    nature,
                    category
                FROM lancamentos
                WHERE id = ?
                """,
                (lancamento_id,)
            ).fetchone()

            return row
        
    def update(self, lancamento_id: int, lancamento: Lancamento):
        with get_connection() as conn:
            conn.execute("""
                UPDATE lancamentos SET
                    entry_date = ?,
                    description = ?,
                    amount = ?,
                    entry_type = ?,
                    payment_method = ?,
                    nature = ?,
                    category = ?
                WHERE id = ?
            """, (
                lancamento.entry_date,
                lancamento.description,
                lancamento.amount,
                lancamento.entry_type.value,
                lancamento.payment_method.value,
                lancamento.nature.value,
                lancamento.category,
                lancamento_id
            ))
            conn.commit()
            
    def add_transferencia(self, amount, from_nature, to_nature):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO lancamentos (
                    entry_date,
                    description,
                    amount,
                    entry_type,
                    from_nature,
                    to_nature
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                date.today().isoformat(),
                f"Transferência {from_nature} → {to_nature}",
                amount,
                EntryType.TRANSFER.value,
                from_nature,
                to_nature
            ))
            conn.commit()