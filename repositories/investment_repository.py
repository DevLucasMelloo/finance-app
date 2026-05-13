from infrastructure.database import get_connection


class InvestmentRepository:

    # ==========================
    # POSITIONS
    # ==========================
    def get_open_position(self, asset: str):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM positions
                WHERE asset = %s AND is_open = 1
            """, (asset,)).fetchone()

    def create_position(self, asset, asset_type, quantity, price, total,
                        broker, origin_account, created_at):
        with get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO positions (
                    asset, asset_type, total_quantity, avg_price,
                    total_invested, broker, origin_account, is_open, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
                RETURNING id
            """, (asset, asset_type, quantity, price, total,
                  broker, origin_account, created_at))
            return cur.fetchone()["id"]

    def update_position(self, position_id, quantity, avg_price, total):
        with get_connection() as conn:
            conn.execute("""
                UPDATE positions
                SET total_quantity = %s, avg_price = %s, total_invested = %s
                WHERE id = %s
            """, (quantity, avg_price, total, position_id))

    def close_position(self, position_id, closed_at):
        with get_connection() as conn:
            conn.execute("""
                UPDATE positions SET is_open = 0, closed_at = %s WHERE id = %s
            """, (closed_at, position_id))

    # ==========================
    # BUYS
    # ==========================
    def add_buy(self, position_id, quantity, price, total, broker, date,
                lancamento_id=None):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO buys
                    (position_id, quantity, price, total_value, broker, date, lancamento_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (position_id, quantity, price, total, broker, date, lancamento_id))

    def get_last_buy(self):
        with get_connection() as conn:
            return conn.execute("""
                SELECT b.*, p.asset, p.origin_account
                FROM buys b
                JOIN positions p ON b.position_id = p.id
                ORDER BY b.id DESC LIMIT 1
            """).fetchone()

    def get_buy(self, buy_id):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM buys WHERE id = %s", (buy_id,)
            ).fetchone()

    def update_buy(self, buy_id, quantity, price, total, broker, date):
        with get_connection() as conn:
            conn.execute("""
                UPDATE buys
                SET quantity=%s, price=%s, total_value=%s, broker=%s, date=%s
                WHERE id=%s
            """, (quantity, price, total, broker, date, buy_id))

    def delete_buy(self, buy_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT lancamento_id FROM buys WHERE id = %s", (buy_id,)
            ).fetchone()
            lancamento_id = row["lancamento_id"] if row else None
            conn.execute("DELETE FROM buys WHERE id = %s", (buy_id,))
            if lancamento_id:
                conn.execute(
                    "DELETE FROM lancamentos WHERE id = %s", (lancamento_id,)
                )

    # ==========================
    # SELLS
    # ==========================
    def add_sell(self, position_id, quantity, price, total, profit, date,
                 lancamento_id=None):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO sells
                    (position_id, quantity, price, total_value, profit, date, lancamento_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (position_id, quantity, price, total, profit, date, lancamento_id))

    def delete_sell(self, sell_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT lancamento_id FROM sells WHERE id = %s", (sell_id,)
            ).fetchone()
            lancamento_id = row["lancamento_id"] if row else None
            conn.execute("DELETE FROM sells WHERE id = %s", (sell_id,))
            if lancamento_id:
                conn.execute(
                    "DELETE FROM lancamentos WHERE id = %s", (lancamento_id,)
                )

    # ==========================
    # CONSULTAS
    # ==========================
    def get_open_positions(self):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM positions WHERE is_open = 1 ORDER BY created_at DESC
            """).fetchall()

    def get_all_positions(self):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM positions ORDER BY created_at DESC
            """).fetchall()

    def get_position(self, position_id):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM positions WHERE id = %s", (position_id,)
            ).fetchone()

    def get_buys(self, position_id):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM buys WHERE position_id = %s ORDER BY date DESC
            """, (position_id,)).fetchall()

    def get_sells(self, position_id):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM sells WHERE position_id = %s ORDER BY date DESC
            """, (position_id,)).fetchall()

    def delete_position(self, position_id):
        lancamento_ids = self.get_lancamento_ids_for_position(position_id)
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM sells WHERE position_id = %s", (position_id,)
            )
            conn.execute(
                "DELETE FROM buys WHERE position_id = %s", (position_id,)
            )
            conn.execute(
                "DELETE FROM positions WHERE id = %s", (position_id,)
            )
            for lid in lancamento_ids:
                conn.execute(
                    "DELETE FROM lancamentos WHERE id = %s", (lid,)
                )

    def get_lancamento_ids_for_position(self, position_id):
        with get_connection() as conn:
            buys = conn.execute(
                "SELECT lancamento_id FROM buys "
                "WHERE position_id = %s AND lancamento_id IS NOT NULL",
                (position_id,),
            ).fetchall()
            sells = conn.execute(
                "SELECT lancamento_id FROM sells "
                "WHERE position_id = %s AND lancamento_id IS NOT NULL",
                (position_id,),
            ).fetchall()
        return [r["lancamento_id"] for r in buys] + [r["lancamento_id"] for r in sells]

    def recalculate_position(self, position_id):
        with get_connection() as conn:
            buys = conn.execute(
                "SELECT * FROM buys WHERE position_id = %s", (position_id,)
            ).fetchall()
            sells = conn.execute(
                "SELECT * FROM sells WHERE position_id = %s", (position_id,)
            ).fetchall()

            if not buys:
                conn.execute(
                    "DELETE FROM positions WHERE id = %s", (position_id,)
                )
                return

            total_bought_qty = sum(b["quantity"] for b in buys)
            total_bought_value = sum(b["total_value"] for b in buys)
            total_sold_qty = sum(s["quantity"] for s in sells)
            remaining_qty = total_bought_qty - total_sold_qty
            avg_price = total_bought_value / total_bought_qty
            total_invested = remaining_qty * avg_price

            if remaining_qty <= 1e-9:
                conn.execute(
                    "UPDATE positions SET is_open=0, total_quantity=0, "
                    "total_invested=0 WHERE id=%s",
                    (position_id,),
                )
            else:
                conn.execute("""
                    UPDATE positions
                    SET total_quantity=%s, avg_price=%s, total_invested=%s, is_open=1
                    WHERE id=%s
                """, (remaining_qty, avg_price, total_invested, position_id))

    def get_all_history(self):
        with get_connection() as conn:
            buys = conn.execute("""
                SELECT b.id as op_id, p.id as position_id,
                       b.date, p.asset, b.broker, 'COMPRA' as tipo,
                       b.quantity, b.price, b.total_value, NULL as profit
                FROM buys b JOIN positions p ON b.position_id = p.id
            """).fetchall()

            sells = conn.execute("""
                SELECT s.id as op_id, p.id as position_id,
                       s.date, p.asset, p.broker, 'VENDA' as tipo,
                       s.quantity, s.price, s.total_value, s.profit
                FROM sells s JOIN positions p ON s.position_id = p.id
            """).fetchall()

        all_ops = list(buys) + list(sells)
        all_ops.sort(key=lambda r: r["date"], reverse=True)
        return all_ops
