from datetime import date as date_type
from repositories.investment_repository import InvestmentRepository
from domain.lancamento import NatureType
from core.finance_app_service import FinanceAppService

CRYPTO_ASSETS = {"BTC", "ETH", "XRP", "SOL", "BNB", "ADA", "DOT", "MATIC", "USDT"}


class InvestmentService:

    def __init__(self):
        self.repo = InvestmentRepository()
        self.finance = FinanceAppService()

    def buy(
        self,
        asset: str,
        quantity: float,
        price: float,
        origin_account: NatureType,
        broker: str = "",
        operation_date: date_type | None = None,
    ):
        if operation_date is None:
            operation_date = date_type.today()

        total = quantity * price
        asset_type = "CRYPTO" if asset.upper() in CRYPTO_ASSETS else "OUTRO"

        saldo = self.finance.balance_of(origin_account)
        if saldo < total:
            raise ValueError(
                f"Saldo insuficiente em {origin_account.value}.\n"
                f"Disponível: R$ {saldo:,.2f} | Necessário: R$ {total:,.2f}"
            )

        position = self.repo.get_open_position(asset.upper())

        if not position:
            position_id = self.repo.create_position(
                asset=asset.upper(),
                asset_type=asset_type,
                quantity=quantity,
                price=price,
                total=total,
                broker=broker,
                origin_account=origin_account.value,
                created_at=operation_date.isoformat(),
            )
        else:
            position_id = position["id"]
            total_quantity = position["total_quantity"] + quantity
            total_invested = position["total_invested"] + total
            avg_price = total_invested / total_quantity

            self.repo.update_position(position_id, total_quantity, avg_price, total_invested)

        lancamento_id = self.finance._lancamento_repo.add_from_investment(
            amount=total,
            nature=origin_account,
            description=f"Compra de {asset.upper()} - {broker}" if broker else f"Compra de {asset.upper()}",
            is_income=False,
        )

        self.repo.add_buy(
            position_id,
            quantity,
            price,
            total,
            broker,
            operation_date.isoformat(),
            lancamento_id=lancamento_id,
        )

    def sell(
        self,
        asset: str,
        quantity: float,
        price: float,
        operation_date: date_type | None = None,
    ):
        if operation_date is None:
            operation_date = date_type.today()

        position = self.repo.get_open_position(asset.upper())

        if not position:
            raise ValueError(f"Nenhuma posição aberta para {asset.upper()}")

        if quantity > position["total_quantity"]:
            raise ValueError(
                f"Quantidade maior que a posição.\n"
                f"Disponível: {position['total_quantity']:.8f}"
            )

        total_sale = quantity * price
        avg_price = position["avg_price"]
        profit = (price - avg_price) * quantity

        new_quantity = position["total_quantity"] - quantity
        new_total = new_quantity * avg_price

        origin_account = NatureType(position["origin_account"])

        lancamento_id = self.finance._lancamento_repo.add_from_investment(
            amount=total_sale,
            nature=origin_account,
            description=f"Venda de {asset.upper()} | Lucro: R$ {profit:,.2f}",
            is_income=True,
        )

        self.repo.add_sell(
            position["id"],
            quantity,
            price,
            total_sale,
            profit,
            operation_date.isoformat(),
            lancamento_id=lancamento_id,
        )

        if new_quantity <= 1e-9:
            self.repo.close_position(position["id"], operation_date.isoformat())
        else:
            self.repo.update_position(position["id"], new_quantity, avg_price, new_total)
