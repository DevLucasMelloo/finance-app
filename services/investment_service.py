from datetime import date
from repositories.investment_repository import InvestmentRepository
from domain.lancamento import NatureType
from core.finance_app_service import FinanceAppService


class InvestmentService:

    def __init__(self):
        self.repo = InvestmentRepository()
        self.finance = FinanceAppService()

    # ==========================
    # 🟢 COMPRA
    # ==========================
    def buy(
        self,
        asset: str,
        quantity: float,
        price: float,
        origin_account: NatureType
    ):
        total = quantity * price

        # 🔒 valida saldo
        saldo = self.finance.balance_of(origin_account)
        if saldo < total:
            raise ValueError("Saldo insuficiente")

        position = self.repo.get_open_position(asset)

        # ==========================
        # 📌 SE NÃO EXISTE POSIÇÃO
        # ==========================
        if not position:
            position_id = self.repo.create_position(
                asset=asset,
                quantity=quantity,
                price=price,
                total=total,
                origin_account=origin_account.value,
                created_at=date.today().isoformat()
            )

        # ==========================
        # 📌 SE JÁ EXISTE POSIÇÃO
        # ==========================
        else:
            position_id = position["id"]

            total_quantity = position["total_quantity"] + quantity
            total_invested = position["total_invested"] + total

            avg_price = total_invested / total_quantity

            self.repo.update_position(
                position_id,
                total_quantity,
                avg_price,
                total_invested
            )

        # salva compra
        self.repo.add_buy(
            position_id,
            quantity,
            price,
            total,
            date.today().isoformat()
        )

        # 💰 tira dinheiro da conta
        self.finance._lancamento_repo.add_from_investment(
            amount=total,
            nature=origin_account,
            description=f"Compra de {asset}",
            is_income=False
        )

    # ==========================
    # 🔴 VENDA
    # ==========================
    def sell(
        self,
        asset: str,
        quantity: float,
        price: float
    ):
        position = self.repo.get_open_position(asset)

        if not position:
            raise ValueError("Você não possui esse ativo")

        if quantity > position["total_quantity"]:
            raise ValueError("Quantidade maior que a posição")

        total_sale = quantity * price

        avg_price = position["avg_price"]
        profit = (price - avg_price) * quantity

        new_quantity = position["total_quantity"] - quantity
        new_total = new_quantity * avg_price

        # salva venda
        self.repo.add_sell(
            position["id"],
            quantity,
            price,
            total_sale,
            profit,
            date.today().isoformat()
        )

        # 💰 devolve dinheiro para conta original
        origin_account = NatureType(position["origin_account"])

        self.finance._lancamento_repo.add_from_investment(
            amount=total_sale,
            nature=origin_account,
            description=f"Venda de {asset}",
            is_income=True
        )

        # ==========================
        # 📌 FECHAR POSIÇÃO
        # ==========================
        if new_quantity == 0:
            self.repo.close_position(
                position["id"],
                date.today().isoformat()
            )
        else:
            self.repo.update_position(
                position["id"],
                new_quantity,
                avg_price,
                new_total
            )