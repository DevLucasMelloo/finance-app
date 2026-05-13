from datetime import date, datetime
from domain.lancamento import NatureType
from repositories.investment_repository import InvestmentRepository
from repositories.lancamento_repository import LancamentoRepository
from services.investment_service import InvestmentService

# ──────────────────────────────────────────
# Opções
# ──────────────────────────────────────────
BROKERS = {"1": "Binance", "2": "Mercado Bitcoin", "3": "outro"}
NATUREZAS = {"1": NatureType.CASH, "2": NatureType.INVESTMENT, "3": NatureType.RESERVE}
NATUREZA_LABEL = {"1": "Caixa", "2": "Investimento", "3": "Reserva"}

# ──────────────────────────────────────────
# Mensagens
# ──────────────────────────────────────────
MENU = """\U0001f4c8 *Investimentos*
━━━━━━━━━━━━━━
1️⃣ Nova compra
2️⃣ Alterar última compra
3️⃣ Deletar última compra
0️⃣ Voltar ao menu"""

ASK_ATIVO = "Qual o *ativo*? _ex: BTC, ETH, PETR4_"
ASK_BROKER = "Qual a *corretora*?\n1️⃣ Binance\n2️⃣ Mercado Bitcoin\n3️⃣ Outra (digitar)"
ASK_BROKER_CUSTOM = "Digite o *nome da corretora*:"
ASK_NATUREZA = "Qual a *conta de origem*?\n1️⃣ Caixa\n2️⃣ Investimento\n3️⃣ Reserva"
ASK_QTDE = "Qual a *quantidade*? _ex: 0.001 ou 10_"
ASK_PRECO = "Qual o *preço unitário* (R$)? _ex: 350000.00_"
ASK_DATA = "Qual a *data* da operação?\n1️⃣ Hoje\n2️⃣ Digitar (DD/MM/AAAA)"
ASK_DATA_DIGITAR = "Digite a data no formato *DD/MM/AAAA*:"


def _resumo(d: dict) -> str:
    total = d.get("quantidade", 0) * d.get("preco", 0)
    return (
        f"📋 *Resumo da compra*\n"
        f"━━━━━━━━━━━━━━\n"
        f"Ativo: {d.get('ativo', '—')}\n"
        f"Corretora: {d.get('broker', '—')}\n"
        f"Conta: {d.get('natureza_label', '—')}\n"
        f"Quantidade: {d.get('quantidade', 0)}\n"
        f"Preço unit.: R$ {d.get('preco', 0):.2f}\n"
        f"Total: R$ {total:.2f}\n"
        f"Data: {d.get('data_str', '—')}\n"
        f"━━━━━━━━━━━━━━\n"
        f"Confirmar? *s* / *n*"
    )


def _fmt_buy(row) -> str:
    return (
        f"🔎 *Última compra*\n"
        f"━━━━━━━━━━━━━━\n"
        f"ID: {row['id']}\n"
        f"Ativo: {row['asset']}\n"
        f"Corretora: {row['broker'] or '—'}\n"
        f"Quantidade: {row['quantity']}\n"
        f"Preço unit.: R$ {row['price']:.2f}\n"
        f"Total: R$ {row['total_value']:.2f}\n"
        f"Data: {row['date']}\n"
        f"━━━━━━━━━━━━━━"
    )


# ──────────────────────────────────────────
# Handler principal
# ──────────────────────────────────────────
def handle(step: str, text: str, data: dict) -> tuple[str, str, dict]:
    t = text.strip()

    if step == "INV_MENU":
        if t == "1":
            return ASK_ATIVO, "INV_ATIVO", {}
        if t == "2":
            row = InvestmentRepository().get_last_buy()
            if not row:
                return "❌ Nenhuma compra encontrada.", "MAIN_MENU", {}
            d = {"edit_id": row["id"], "position_id": row["position_id"],
                 "lancamento_id": row["lancamento_id"]}
            return _fmt_buy(row) + "\n\nVamos atualizar. " + ASK_ATIVO, "INV_ATIVO", d
        if t == "3":
            row = InvestmentRepository().get_last_buy()
            if not row:
                return "❌ Nenhuma compra encontrada.", "MAIN_MENU", {}
            return (
                _fmt_buy(row) + "\n\n⚠️ *Confirmar exclusão?* *s* / *n*",
                "INV_DEL_CONFIRM",
                {"del_id": row["id"], "position_id": row["position_id"]},
            )
        if t == "0":
            return "", "MAIN_MENU", {}
        return MENU, "INV_MENU", data

    if step == "INV_DEL_CONFIRM":
        if t.lower() == "s":
            repo = InvestmentRepository()
            repo.delete_buy(data["del_id"])
            repo.recalculate_position(data["position_id"])
            return "✅ Compra excluída!", "MAIN_MENU", {}
        return "Cancelado.", "MAIN_MENU", {}

    if step == "INV_ATIVO":
        if not t:
            return ASK_ATIVO, "INV_ATIVO", data
        data["ativo"] = t.upper()
        return ASK_BROKER, "INV_BROKER", data

    if step == "INV_BROKER":
        if t == "3":
            return ASK_BROKER_CUSTOM, "INV_BROKER_CUSTOM", data
        if t in BROKERS:
            data["broker"] = BROKERS[t]
            return ASK_NATUREZA, "INV_NATUREZA", data
        return "❌ " + ASK_BROKER, "INV_BROKER", data

    if step == "INV_BROKER_CUSTOM":
        data["broker"] = t if t else "Outra"
        return ASK_NATUREZA, "INV_NATUREZA", data

    if step == "INV_NATUREZA":
        if t not in NATUREZAS:
            return "❌ " + ASK_NATUREZA, "INV_NATUREZA", data
        data["natureza"] = NATUREZAS[t]
        data["natureza_label"] = NATUREZA_LABEL[t]
        return ASK_QTDE, "INV_QTDE", data

    if step == "INV_QTDE":
        try:
            val = float(t.replace(",", "."))
            if val <= 0:
                raise ValueError
        except ValueError:
            return "❌ Quantidade inválida. " + ASK_QTDE, "INV_QTDE", data
        data["quantidade"] = val
        return ASK_PRECO, "INV_PRECO", data

    if step == "INV_PRECO":
        try:
            val = float(t.replace(",", "."))
            if val <= 0:
                raise ValueError
        except ValueError:
            return "❌ Preço inválido. " + ASK_PRECO, "INV_PRECO", data
        data["preco"] = val
        return ASK_DATA, "INV_DATA", data

    if step == "INV_DATA":
        if t == "1":
            data["data"] = date.today().isoformat()
            data["data_str"] = date.today().strftime("%d/%m/%Y")
            return _resumo(data), "INV_CONFIRM", data
        if t == "2":
            return ASK_DATA_DIGITAR, "INV_DATA_INPUT", data
        return "❌ " + ASK_DATA, "INV_DATA", data

    if step == "INV_DATA_INPUT":
        try:
            d = datetime.strptime(t, "%d/%m/%Y").date()
            data["data"] = d.isoformat()
            data["data_str"] = t
            return _resumo(data), "INV_CONFIRM", data
        except ValueError:
            return "❌ Data inválida. " + ASK_DATA_DIGITAR, "INV_DATA_INPUT", data

    if step == "INV_CONFIRM":
        if t.lower() != "s":
            return "Cancelado.", "MAIN_MENU", {}
        try:
            op_date = date.fromisoformat(data["data"])

            if "edit_id" in data:
                # Edição: atualiza o registro da compra e recalcula posição
                repo = InvestmentRepository()
                total = data["quantidade"] * data["preco"]
                repo.update_buy(
                    data["edit_id"],
                    data["quantidade"],
                    data["preco"],
                    total,
                    data["broker"],
                    data["data"],
                )
                repo.recalculate_position(data["position_id"])
                # Atualiza o lançamento associado
                if data.get("lancamento_id"):
                    LancamentoRepository().update(
                        data["lancamento_id"],
                        _make_lancamento_obj(data, total),
                    )
                return "✅ Compra atualizada!", "MAIN_MENU", {}
            else:
                svc = InvestmentService()
                svc.buy(
                    asset=data["ativo"],
                    quantity=data["quantidade"],
                    price=data["preco"],
                    origin_account=data["natureza"],
                    broker=data["broker"],
                    operation_date=op_date,
                )
                return "✅ Compra registrada!", "MAIN_MENU", {}
        except Exception as exc:
            return f"❌ Erro: {exc}", "MAIN_MENU", {}

    return MENU, "INV_MENU", data


def _make_lancamento_obj(data: dict, total: float):
    """Cria objeto Lancamento para atualização do lançamento vinculado."""
    from domain.lancamento import Lancamento, EntryType, PaymentMethod
    return Lancamento(
        entry_date=date.fromisoformat(data["data"]),
        amount=total,
        entry_type=EntryType.EXPENSE,
        payment_method=PaymentMethod.PIX,
        category="Investimento",
        nature=data["natureza"],
        description=f"Compra de {data['ativo']} - {data['broker']}",
    )
