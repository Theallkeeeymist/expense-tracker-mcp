from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__),  "expenses_db")
BUD_PATH = os.path.join(os.path.dirname(__file__), "budget.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="Expense Tracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS Expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
    with sqlite3.connect(BUD_PATH) as b:
        b.execute("""
            CREATE TABLE IF NOT EXISTS budget(
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                month TEXT NOT NULL,
                PRIMARY KEY (category, month)
)
        """)
init_db()

@mcp.tool()
def add_expenses(date, amount, category, subcategory='', note=''):
    """Adds expenses based on it's amount date of expenditure, category subcategory and note to the database"""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO Expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {'status': 'ok', 'id':cur.lastrowid}
    
@mcp.tool()
def set_budget(category, monthly_limit, month):
    """Sets Budget for particular CATEGORY for a month"""
    with sqlite3.connect(BUD_PATH) as b:
        cur = b.execute(
            "INSERT OR REPLACE INTO budget(category, monthly_limit, month) VALUES (?,?,?)",
            (category, monthly_limit, month)
        )
        return {'status':'ok', 'category':cur.lastrowid}
    
@mcp.tool()
def budget_left(month, category=None):
    """Returns remaining budget per category with warning if low or exhausted"""
    with sqlite3.connect(DB_PATH) as e_conn:
        e_conn.execute(f"ATTACH DATABASE '{BUD_PATH}' AS bdb")
        query = """
            SELECT 
                b.category,
                b.monthly_limit,
                COALESCE(SUM(e.amount), 0) AS spent,
                b.monthly_limit - COALESCE(SUM(e.amount), 0) AS remaining,
                CASE
                    WHEN b.monthly_limit - COALESCE(SUM(e.amount), 0) < 0 
                        THEN 'BUDGET EXHAUSTED'
                    WHEN b.monthly_limit - COALESCE(SUM(e.amount), 0) < 100 
                        THEN 'WARNING: Low on budget'
                    ELSE 'OK'
                END AS status
            FROM bdb.budget b
            LEFT JOIN Expenses e 
                ON e.category = b.category 
                AND strftime('%Y-%m', e.date) = ?
            WHERE b.month = ?
        """
        params = [month, month]

        if category:
            query += " AND b.category = ?"
            params.append(category)

        query += " GROUP BY b.category ORDER BY spent DESC"

        cur = e_conn.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def saved_in_budget(month, category=None):
    """Returns how much was saved under budget per category for a given month"""
    with sqlite3.connect(DB_PATH) as e_conn:
        e_conn.execute(f"ATTACH DATABASE '{BUD_PATH}' AS bdb")
        query = """
            SELECT 
                b.category,
                b.monthly_limit,
                COALESCE(SUM(e.amount), 0) AS spent,
                b.monthly_limit - COALESCE(SUM(e.amount), 0) AS saved
            FROM bdb.budget b
            LEFT JOIN Expenses e 
                ON e.category = b.category 
                AND strftime('%Y-%m', e.date) = ?
            WHERE b.month = ?
        """
        params = [month, month]

        if category:
            query += " AND b.category = ?"
            params.append(category)

        query += " GROUP BY b.category HAVING saved > 0 ORDER BY saved DESC"

        cur = e_conn.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()  
def list_expenses(start_date, end_date): 
    """Lists all the expenses"""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT id, date, amount, category, subcategory, note FROM Expenses WHERE date BETWEEN ? AND ? ORDER BY id ASC",
                        (start_date, end_date))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def delete_expense(id):
    """Deletes expense in case of mistake"""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM Expenses WHERE id= ?",
            (id,)
        )
        return {'status':'ok', 'id':cur.lastrowid}

@mcp.tool()
def delete_budget(category):
    """Deletes a set budget in case of mistake"""
    with sqlite3.connect(BUD_PATH) as b:
        cur = b.execute(
            "DELETE FROM budget WHERE category=?",
            (category,)
        )
        return {'status':'ok', 'category':cur.lastrowid}
    
@mcp.tool()
def fetch_budget(month, category=None):
    """Returns Set Budget for a month can give explicityly for a category too if mentioned."""
    with sqlite3.connect(BUD_PATH) as b:
        query=("""
            SELECT monthly_limit FROM budget
            WHERE month=?
        """)
        params = [month]

        if category:
            query+=" AND category = ?"
            params.append(category)

        cur = b.execute(query, params)
        cols = [d[0] for d in cur.description]

        return [dict(zip(cols, r)) for r in cur.fetchall()]

    

@mcp.tool()
def update_expense(id, amount=None, category=None):
    """Updates the amount or category of an expense based on the provided ID"""
    if amount is None and category is None:
        return {"status": "error", "message": "No fields provided for update"}

    with sqlite3.connect(DB_PATH) as c:
        update_clauses = []
        params = []

        if amount is not None:
            update_clauses.append("amount = ?")
            params.append(amount)
        
        if category is not None:
            update_clauses.append("category = ?")
            params.append(category)

        set_statement = ", ".join(update_clauses)
        
        query = f"UPDATE Expenses SET {set_statement} WHERE id = ?"
        params.append(id)
        cur = c.execute(query, params)
        
        if cur.rowcount == 0:
            return {"status": "error", "message": f"No expense found with ID {id}"}
            
        return {"status": "ok", "updated_count": cur.rowcount}

@mcp.tool()
def summarize(start_date, end_date, category=None):
    """Summarize expenses within an inclusive date range"""
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount FROM Expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)
        query += " GROUP BY category"
        
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]

        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()
    
if __name__ == "__main__":
    mcp.run()