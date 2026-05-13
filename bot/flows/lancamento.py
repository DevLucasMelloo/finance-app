from datetime import date, datetime
from domain.lancamento import Lancamento, EntryType, PaymentMethod, NatureType
from repositories.lancamento_repository import LancamentoRepository

# ──────────────────────────────────────────
# Opções
# ──────────────────────────────────────────
TIPOS = {"1": EntryType.INCOME, "2": EntryType.EXPENSE}
TIPOS_LABEL = {"1": "Provento ✅", "2": "Despesa ❌"}

NATUREZAS = {"1": NatureType.CASH, "2": NatureType.INVESTMENT, "3": NatureType.RESERVE}
NATUREZA_LABEL = {"1": "Caixa 💵", "2": "Investimento 📈", "3": "Reserva 🏦"}

METODOS = {
    "1": PaymentMethod.PIX,
    "2": PaymentMethod.CASH,
    "3": PaymentMethod.BOLETO,
    "4": PaymentMethod.DEBIT_CARD,
    "5": PaymentMethod.CREDIT_CARD,
}
METODO_LABEL = {
    "1": "PIX", "2": "Dinheiro", "3": "Boleto",
    "4": "Débito", "5": "Crédito",
}

# ──────────────────────────────────────────
# Mensagens
# ──────────────────────────────────────────
MENU = """\U0001f4cb *Lançamentos*
━━━━━━━━━━━━━━
1️⃣ Novo lançamento
2️⃣ Alterar último lançamento
3️⃣ Deletar último lançamento
0️⃣ Voltar ao menu"""

ASK_TIPO = "Qual o *tipo*?\n1️⃣ Provento\n2️⃣ Despesa"
ASK_NATUREZA = "Qual a *natureza*?\n1️⃣ Caixa\n2️⃣ Investimento\n3️⃣ Reserva"
ASK_CATEGORIA = "Qual a *categoria*?\n_ex: Alimentação, Salário, Aluguel_"
ASK_METODO = "Método de *pagamento*?\n1️⃣ PIX\n2️⃣ Dinheiro\n3️⃣ Boleto\n4️⃣ Débito\n5️⃣ Crédito"
ASK_VALOR = "Qual o *valor*? _ex: 150.00_"
ASK_DATA = "Qual a *data*?\n1️⃣ Hoje\n2️⃣ Digitar (DD/MM/AAAA)"
ASK_DATA_DIGITAR = "Digite a data no formato *DD/MM/AAAA*:"
ASK_DESCRICAO = "Alguma *descrição*? _(ou digite *pular*)_"


def _resumo(d: dict) -> str:
    return (
        f"📋 *Resumo do lançamento*\n"
        f"━━━━━━━━━━━━━━\n"
        f"Tipo: {d.get('tipo_label', '—')}\n"
        f"Natureza: {d.get('natureza_label', '—')}\n"
        f"Categoria: {d.get('categoria', '—')}\n"
        f"Método: {d.get('metodo_label', '—')}\n"
        f"Valor: R$ {d.get('valor', 0):.2f}\n"
        f"Data: {d.get('data_str', '—')}\n"
        f"Descrição: {d.get('descricao') or '—'}\n"
        f"━━━━━━━━━━━━━━\n"
        f"Confirmar? *s* / *n*"
    )


def _fmt_row(row) -> str:
    return (
        f"🔎 *Último lançamento*\n"
        f"━━━━━━━━━━━━━━\n"
        f"ID: {row['id']}\n"
        f"Tipo: {row['entry_type']}\n"
        f"Natureza: {row['nature']}\n"
        f"Categoria: {row['category']}\n"
        f"Método: {row['payment_method']}\n"
        f"Valor: R$ {row['amount']:.2f}\n"
        f"Data: {row['entry_date']}\n"
        f"Descrição: {row['description'] or '—'}\n"
        f"━━━━━━━━━━━━━━"
    )


# ──────────────────────────────────────────
# Handler principal
# Retorna (reply: str, next_step: str, data: dict)
# ──────────────────────────────────────────
def handle(step: str, text: str, data: dict) -> tuple[str, str, dict]:
    t = text.strip()

    if step == "LANC_MENU":
        if t == "1":
            return ASK_TIPO, "LANC_TIPO", {}
        if t == "2":
            row = LancamentoRepository().get_last()
            if not row:
                return "❌ Nenhum lançamento encontrado.", "MAIN_MENU", {}
            d = {"edit_id": row["id"]}
            return _fmt_row(row) + "\n\nVamos atualizar. " + ASK_TIPO, "LANC_TIPO", d
        if t == "3":
            row = LancamentoRepository().get_last()
            if not row:
                return "❌ Nenhum lançamento encontrado.", "MAIN_MENU", {}
            return (
                _fmt_row(row) + "\n\n⚠️ *Confirmar exclusão?* *s* / *n*",
                "LANC_DEL_CONFIRM",
                {"del_id": row["id"]},
            )
        if t == "0":
            return "", "MAIN_MENU", {}
        return MENU, "LANC_MENU", data

    if step == "LANC_DEL_CONFIRM":
        if t.lower() == "s":
            LancamentoRepository().delete(data["del_id"])
            return "✅ Lançamento excluído!", "MAIN_MENU", {}
        return "Cancelado.", "MAIN_MENU", {}

    if step == "LANC_TIPO":
        if t not in TIPOS:
            return "❌ " + ASK_TIPO, "LANC_TIPO", data
        data["tipo"] = TIPOS[t].value
        data["tipo_label"] = TIPOS_LABEL[t]
        return ASK_NATUREZA, "LANC_NATUREZA", data

    if step == "LANC_NATUREZA":
        if t not in NATUREZAS:
            return "❌ " + ASK_NATUREZA, "LANC_NATUREZA", data
        data["natureza"] = NATUREZAS[t].value
        data["natureza_label"] = NATUREZA_LABEL[t]
        return ASK_CATEGORIA, "LANC_CATEGORIA", data

    if step == "LANC_CATEGORIA":
        if not t:
            return ASK_CATEGORIA, "LANC_CATEGORIA", data
        data["categoria"] = t
        return ASK_METODO, "LANC_METODO", data

    if step == "LANC_METODO":
        if t not in METODOS:
            return "❌ " + ASK_METODO, "LANC_METODO", data
        data["metodo"] = METODOS[t].value
        data["metodo_label"] = METODO_LABEL[t]
        return ASK_VALOR, "LANC_VALOR", data

    if step == "LANC_VALOR":
        try:
            val = float(t.replace(",", "."))
            if val <= 0:
                raise ValueError
        except ValueError:
            return "❌ Valor inválido. " + ASK_VALOR, "LANC_VALOR", data
        data["valor"] = val
        return ASK_DATA, "LANC_DATA", data

    if step == "LANC_DATA":
        if t == "1":
            data["data"] = date.today().isoformat()
            data["data_str"] = date.today().strftime("%d/%m/%Y")
            return ASK_DESCRICAO, "LANC_DESCRICAO", data
        if t == "2":
            return ASK_DATA_DIGITAR, "LANC_DATA_INPUT", data
        return "❌ " + ASK_DATA, "LANC_DATA", data

    if step == "LANC_DATA_INPUT":
        try:
            d = datetime.strptime(t, "%d/%m/%Y").date()
            data["data"] = d.isoformat()
            data["data_str"] = t
            return ASK_DESCRICAO, "LANC_DESCRICAO", data
        except ValueError:
            return "❌ Data inválida. " + ASK_DATA_DIGITAR, "LANC_DATA_INPUT", data

    if step == "LANC_DESCRICAO":
        data["descricao"] = None if t.lower() == "pular" else t
        return _resumo(data), "LANC_CONFIRM", data

    if step == "LANC_CONFIRM":
        if t.lower() != "s":
            return "Cancelado.", "MAIN_MENU", {}
        try:
            lancamento = Lancamento(
                entry_date=date.fromisoformat(data["data"]),
                amount=data["valor"],
                entry_type=EntryType(data["tipo"]),
                payment_method=PaymentMethod(data["metodo"]),
                category=data["categoria"],
                nature=NatureType(data["natureza"]),
                description=data.get("descricao"),
            )
            repo = LancamentoRepository()
            if "edit_id" in data:
                repo.update(data["edit_id"], lancamento)
                return "✅ Lançamento atualizado!", "MAIN_MENU", {}
            else:
                repo.add(lancamento)
                return "✅ Lançamento salvo!", "MAIN_MENU", {}
        except Exception as exc:
            return f"❌ Erro: {exc}", "MAIN_MENU", {}

    return MENU, "LANC_MENU", data
