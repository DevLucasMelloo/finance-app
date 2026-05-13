from domain.variacao_investimento import VariacaoInvestimento
from infrastructure.database import get_connection, to_date


class VariacaoInvestimentoRepository:

    def add(self, variacao: VariacaoInvestimento) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO variacoes_investimento
                    (reference_date, value_change, description)
                VALUES (%s, %s, %s)
                """,
                (variacao.reference_date, variacao.value_change, variacao.description),
            )

    def list_all(self) -> list[VariacaoInvestimento]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM variacoes_investimento"
            ).fetchall()

        return [
            VariacaoInvestimento(
                reference_date=to_date(row["reference_date"]),
                value_change=row["value_change"],
                description=row["description"],
            )
            for row in rows
        ]
