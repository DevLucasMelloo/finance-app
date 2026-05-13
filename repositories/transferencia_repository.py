from domain.transferencia import Transferencia
from domain.lancamento import NatureType
from infrastructure.database import get_connection, to_date


class TransferenciaRepository:

    def add(self, transferencia: Transferencia):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transferencias (
                    transfer_date, amount, origin, destination, description
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    transferencia.transfer_date,
                    transferencia.amount,
                    transferencia.origin.value,
                    transferencia.destination.value,
                    transferencia.description,
                ),
            )

    def update(self, transferencia_id: int, transferencia: Transferencia):
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE transferencias SET
                    transfer_date = %s, amount = %s,
                    origin = %s, destination = %s, description = %s
                WHERE id = %s
                """,
                (
                    transferencia.transfer_date,
                    transferencia.amount,
                    transferencia.origin.value,
                    transferencia.destination.value,
                    transferencia.description,
                    transferencia_id,
                ),
            )

    def list_all(self) -> list[Transferencia]:
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT id, transfer_date, amount, origin, destination, description
                FROM transferencias
            """).fetchall()

        return [
            Transferencia(
                id=r["id"],
                transfer_date=to_date(r["transfer_date"]),
                amount=r["amount"],
                origin=NatureType(r["origin"]),
                destination=NatureType(r["destination"]),
                description=r["description"],
            )
            for r in rows
        ]

    def get_by_id(self, transferencia_id: int):
        with get_connection() as conn:
            r = conn.execute(
                """
                SELECT id, transfer_date, amount, origin, destination, description
                FROM transferencias WHERE id = %s
                """,
                (transferencia_id,),
            ).fetchone()

        if not r:
            return None

        return Transferencia(
            id=r["id"],
            transfer_date=to_date(r["transfer_date"]),
            amount=r["amount"],
            origin=NatureType(r["origin"]),
            destination=NatureType(r["destination"]),
            description=r["description"],
        )

    def delete(self, transferencia_id: int):
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM transferencias WHERE id = %s", (transferencia_id,)
            )
