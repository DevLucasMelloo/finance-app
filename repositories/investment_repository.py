from infrastructure.database import get_connection


class InvestmentRepository:

    # ==========================
    # 📌 POSITIONS
    # ==========================
    def get_open_position(self, asset: str):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM positions
                WHERE asset = ? AND is_open = 1
            """, (asset,)).fetchone()

    def create_position(self, asset, quantity, price, total, origin_account, created_at):
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO positions (
                    asset,
                    total_quantity,
                    avg_price,
                    total_invested,
                    origin_account,
                    is_open,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                asset,
                quantity,
                price,
                total,
                origin_account,
                created_at
            ))

            return cursor.lastrowid

    def update_position(self, position_id, quantity, avg_price, total):
        with get_connection() as conn:
            conn.execute("""
                UPDATE positions
                SET total_quantity = ?, avg_price = ?, total_invested = ?
                WHERE id = ?
            """, (quantity, avg_price, total, position_id))

    def close_position(self, position_id, closed_at):
        with get_connection() as conn:
            conn.execute("""
                UPDATE positions
                SET is_open = 0, closed_at = ?
                WHERE id = ?
            """, (closed_at, position_id))

    # ==========================
    # 🟢 BUYS
    # ==========================
    def add_buy(self, position_id, quantity, price, total, date):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO buys (
                    position_id,
                    quantity,
                    price,
                    total_value,
                    date
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                position_id,
                quantity,
                price,
                total,
                date
            ))

    # ==========================
    # 🔴 SELLS
    # ==========================
    def add_sell(self, position_id, quantity, price, total, profit, date):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO sells (
                    position_id,
                    quantity,
                    price,
                    total_value,
                    profit,
                    date
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                position_id,
                quantity,
                price,
                total,
                profit,
                date
            ))

    # ==========================
    # 📊 CONSULTAS
    # ==========================
    def get_open_positions(self):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT *
                FROM positions
                WHERE is_open = 1
            """).fetchall()

            return rows

    def get_buys(self, position_id):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM buys
                WHERE position_id = ?
            """, (position_id,)).fetchall()

    def get_sells(self, position_id):
        with get_connection() as conn:
            return conn.execute("""
                SELECT * FROM sells
                WHERE position_id = ?
            """, (position_id,)).fetchall()