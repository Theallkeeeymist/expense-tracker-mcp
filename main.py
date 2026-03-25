from fastmcp import FastMCP
import os
import aiosqlite

if os.access(os.path.dirname(__file__), os.W_OK):
    DB_PATH = os.path.join(os.path.dirname(__file__), "expenses_db.sqlite")
else:
    DB_PATH = "/tmp/expenses_db.sqlite"

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="Expense Tracker")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS Expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await db.commit()


@mcp.tool()
async def add_expenses(date, amount, category, subcategory='', note=''):
    """Adds expenses"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO Expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        await db.commit()
        return {'status': 'ok', 'id': cur.lastrowid}


@mcp.tool()
async def list_expenses(start_date, end_date):
    """Lists all the expenses"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT id, date, amount, category, subcategory, note
               FROM Expenses
               WHERE date BETWEEN ? AND ?
               ORDER BY id ASC""",
            (start_date, end_date)
        )
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


@mcp.tool()
async def delete_expense(id):
    """Deletes expense"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM Expenses WHERE id = ?",
            (id,)
        )
        await db.commit()
        return {'status': 'ok', 'deleted_count': cur.rowcount}


@mcp.tool()
async def update_expense(id, amount=None, category=None):
    """Updates expense"""
    if amount is None and category is None:
        return {"status": "error", "message": "No fields provided"}

    async with aiosqlite.connect(DB_PATH) as db:
        update_clauses = []
        params = []

        if amount is not None:
            update_clauses.append("amount = ?")
            params.append(amount)

        if category is not None:
            update_clauses.append("category = ?")
            params.append(category)

        query = f"UPDATE Expenses SET {', '.join(update_clauses)} WHERE id = ?"
        params.append(id)

        cur = await db.execute(query, params)
        await db.commit()

        if cur.rowcount == 0:
            return {"status": "error", "message": f"No expense found with ID {id}"}

        return {"status": "ok", "updated_count": cur.rowcount}


@mcp.tool()
async def summarize(start_date, end_date, category=None):
    """Summarize expenses"""
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM Expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]

        return [dict(zip(cols, r)) for r in rows]


@mcp.resource("expense://categories", mime_type="application/json")
async def categories():
    async with aiosqlite.connect(DB_PATH):  # optional, just to keep async style consistent
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()


@mcp.resource("info://server")
async def server_info() -> dict:
    return {
        "name": "Expense Tracker Server",
        "version": "1.0.0",
        "description": "A basic MCP server which can track your expenses",
        "tools": ["add_expenses", "list_expenses", "delete_expense"],
        "author": "Allkeeey"
    }


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    mcp.run(transport="http", host="0.0.0.0", port=8000)