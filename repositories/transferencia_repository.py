from infrastructure.database import get_connection
from domain.transferencia import Transferencia
from domain.lancamento import NatureType
from datetime import date


class TransferenciaRepository:

    # -----------------------------
    # ➕ INSERIR
    # -----------------------------
    def add(self, transferencia: Transferencia):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transferencias (
                    transfer_date,
                    amount,
                    origin,
                    destination,
                    description
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    transferencia.transfer_date.isoformat(),
                    transferencia.amount,
                    transferencia.origin.value,
                    transferencia.destination.value,
                    transferencia.description,
                )
            )
            conn.commit()

    # -----------------------------
    # ✏️ ATUALIZAR
    # -----------------------------
    def update(self, transferencia_id: int, transferencia: Transferencia):
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE transferencias
                SET
                    transfer_date = ?,
                    amount = ?,
                    origin = ?,
                    destination = ?,
                    description = ?
                WHERE id = ?
                """,
                (
                    transferencia.transfer_date.isoformat(),
                    transferencia.amount,
                    transferencia.origin.value,
                    transferencia.destination.value,
                    transferencia.description,
                    transferencia_id,
                )
            )
            conn.commit()

    # -----------------------------
    # 📄 LISTAR
    # -----------------------------
    def list_all(self):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    id,
                    transfer_date,
                    amount,
                    origin,
                    destination,
                    description
                FROM transferencias
            """).fetchall()

        transferencias = []
        for r in rows:
            transferencias.append(
                Transferencia(
                    id=r["id"],
                    transfer_date=date.fromisoformat(r["transfer_date"]),
                    amount=r["amount"],
                    origin=NatureType(r["origin"]),
                    destination=NatureType(r["destination"]),
                    description=r["description"],
                )
            )

        return transferencias
    
    def get_by_id(self, transferencia_id: int):
        from datetime import date

        with get_connection() as conn:
            r = conn.execute("""
                SELECT
                    id,
                    transfer_date,
                    amount,
                    origin,
                    destination,
                    description
                FROM transferencias
                WHERE id = ?
            """, (transferencia_id,)).fetchone()

        if not r:
            return None

        return Transferencia(
            id=r["id"],
            transfer_date=date.fromisoformat(r["transfer_date"]),
            amount=r["amount"],
            origin=NatureType(r["origin"]),
            destination=NatureType(r["destination"]),
            description=r["description"],
        )
    def delete(self, transferencia_id: int):
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM transferencias WHERE id = ?",
                (transferencia_id,)
            )
            conn.commit()