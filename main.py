from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__),  "expenses_db")
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
 
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]

        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("info://server")
def server_info()->str:
    """Get information about the server"""
    info = {
        "name":"Expense Tracker Server",
        "version":"1.0.0",
        "description":"A basic MCP server which can track your expenses",
        "tools":["add", "random_number"],
        "author":"Allkeeey"
    }
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)