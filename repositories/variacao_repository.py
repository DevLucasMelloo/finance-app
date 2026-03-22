from datetime import date
from domain.variacao_investimento import VariacaoInvestimento
from infrastructure.database import get_connection


class VariacaoInvestimentoRepository:
    def add(self, variacao: VariacaoInvestimento) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO variacoes_investimento
                (reference_date, value_change, description)
                VALUES (?, ?, ?)
                """,
                (
                    variacao.reference_date.isoformat(),
                    variacao.value_change,
                    variacao.description,
                ),
            )

    def list_all(self) -> list[VariacaoInvestimento]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM variacoes_investimento"
            ).fetchall()

        return [
            VariacaoInvestimento(
                reference_date=date.fromisoformat(row["reference_date"]),
                value_change=row["value_change"],
                description=row["description"],
            )
            for row in rows
        ]
