# Expense Tracker MCP

A local MCP (Model Context Protocol) server that lets you track expenses and budgets directly through Claude. Log spending, set monthly budgets, summarize your finances — all via natural conversation.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Connecting to Claude Desktop](#connecting-to-claude-desktop)
- [Available Tools](#available-tools)
- [Categories](#categories)
- [Example Prompts](#example-prompts)
- [Project Structure](#project-structure)
- [Notes](#notes)

---

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.12+** — [Download here](https://www.python.org/downloads/)
- **uv** (recommended package manager) — Install with:
  ```bash
  pip install uv
  # or on macOS/Linux:
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Claude Desktop** — [Download here](https://claude.ai/download)

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/expense-tracker-mcp.git
cd expense-tracker-mcp
```

**2. Install dependencies**

```bash
uv sync
```

This will create a virtual environment and install all required packages from `uv.lock`.

**3. Verify the setup**

```bash
uv run python main_local.py
```

If no errors appear, the server is ready to be connected to Claude Desktop.

---

## Connecting to Claude Desktop

MCP servers are configured via a JSON config file that Claude Desktop reads on startup.

**1. Find your Claude Desktop config file**

| OS      | Location |
|---------|----------|
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

**2. Open (or create) the config file and add the server entry**

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/expense-tracker-mcp",
        "python",
        "main_local.py"
      ]
    }
  }
}
```

> Replace `/absolute/path/to/expense-tracker-mcp` with the actual full path to the cloned folder.
>
> **Example on macOS:** `/Users/yourname/projects/expense-tracker-mcp`
>
> **Example on Windows:** `C:\\Users\\yourname\\projects\\expense-tracker-mcp`

**3. Restart Claude Desktop**

Quit and relaunch Claude Desktop. You should see the expense tracker tools appear in the tools panel (🔧 icon).

---

## Available Tools

Once connected, Claude can use the following tools on your behalf:

### `add_expenses`
Add a new expense entry to the database.

| Parameter    | Type   | Required  | Description                          |
|--------------|--------|-----------|--------------------------------------|
| `date`       | string | YES       | Date in `YYYY-MM-DD` format          |
| `amount`     | float  | YES       | Expense amount                       |
| `category`   | string | YES       | Main category (e.g. `food`)          |
| `subcategory`| string | NO        | Subcategory (e.g. `groceries`)       |
| `note`       | string | NO        | Optional note or description         |

---

### `list_expenses`
List all expenses within a date range.

| Parameter    | Type   | Required  | Description              |
|--------------|--------|-----------|--------------------------|
| `start_date` | string | YES       | Start date `YYYY-MM-DD`  |
| `end_date`   | string | YES       | End date `YYYY-MM-DD`    |

---

### `summarize`
Get a category-wise spending summary for a date range.

| Parameter    | Type   | Required  | Description                             |
|--------------|--------|---------- |-----------------------------------------|
| `start_date` | string | YES       | Start date `YYYY-MM-DD`                 |
| `end_date`   | string | YES       | End date `YYYY-MM-DD`                   |
| `category`   | string | NO        | Filter summary to a specific category   |

---

### `set_budget`
Set a monthly spending limit for a category.

| Parameter       | Type   | Required | Description                          |
|-----------------|--------|----------|--------------------------------------|
| `category`      | string |YES       | Category name                        |
| `monthly_limit` | float  |YES       | Budget limit amount                  |
| `month`         | string |YES       | Month in `YYYY-MM` format            |

---

### `budget_left`
Check how much budget remains per category, with warning indicators.

| Parameter  | Type   | Required  | Description                          |
|------------|--------|-----------|--------------------------------------|
| `month`    | string | YES       | Month in `YYYY-MM` format            |
| `category` | string | NO        | Filter to a specific category        |

Returns status: `OK`, `WARNING: Low on budget`, or `BUDGET EXHAUSTED`.

---

### `saved_in_budget`
See how much you saved under budget per category for a given month.

| Parameter  | Type   | Required  | Description               |
|------------|--------|-----------|---------------------------|
| `month`    | string | YES       | Month in `YYYY-MM` format |
| `category` | string | NO        | Filter to a specific category |

---

### `fetch_budget`
Retrieve the currently set budget(s) for a month.

| Parameter  | Type   | Required  | Description               |
|------------|--------|-----------|---------------------------|
| `month`    | string | YES       | Month in `YYYY-MM` format |
| `category` | string | NO        | Filter to a specific category |

---

### `update_expense`
Correct the amount or category of an existing expense.

| Parameter  | Type   | Required  | Description                     |
|------------|--------|-----------|---------------------------------|
| `id`       | int    | YES       | Expense ID to update            |
| `amount`   | float  | NO        | New amount                      |
| `category` | string | NO        | New category                    |

---

### `delete_expense`
Remove a mistakenly entered expense.

| Parameter | Type | Required  | Description          |
|-----------|------|-----------|----------------------|
| `id`      | int  | YES       | ID of expense to delete |

---

### `delete_budget`
Remove a budget entry.

| Parameter  | Type   | Required  | Description               |
|------------|--------|-----------|---------------------------|
| `category` | string | YES       | Category budget to remove |

---

## Categories

The tracker ships with a comprehensive category system defined in `categories.json`. Top-level categories include:

| Category         | Example Subcategories                          |
|------------------|------------------------------------------------|
| `food`           | groceries, dining_out, delivery_fees           |
| `transport`      | fuel, cab_ride_hailing, public_transport       |
| `housing`        | rent, repairs_service, furnishing              |
| `utilities`      | electricity, internet_broadband, mobile_phone  |
| `health`         | medicines, doctor_consultation, fitness_gym    |
| `education`      | books, courses, online_subscriptions           |
| `entertainment`  | movies_events, streaming_subscriptions, outing |
| `shopping`       | clothing, electronics_gadgets, home_decor      |
| `investments`    | mutual_funds, stocks, crypto                   |
| `travel`         | flights, hotels, visa_passport                 |
| `taxes`          | income_tax, gst, filing_fees                   |
| `misc`           | uncategorized, other                           |

See `categories.json` for the full list.

---

## Example Prompts

Once connected, try saying to Claude:

```
"Add an expense of ₹450 for groceries today"

"Show me all my expenses from March 1st to March 26th"

"Set a budget of ₹5000 for food for March 2026"

"How much of my food budget is left for this month?"

"Summarize my spending for March 2026"

"I made a mistake on expense ID 3, change the amount to ₹200"

"How much did I save under budget in February?"

"Delete expense number 7"
```

---

## Project Structure

```
expense-tracker-mcp/
├── main_local.py        # MCP server for local use (connect this to Claude Desktop)
├── main.py              # HTTP server variant (for hosted/production deployment)
├── categories.json      # Full category and subcategory definitions
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Locked dependency versions
├── .python-version      # Pinned Python version (3.12)
├── .gitignore
└── README.md
```

**Data files created at runtime (gitignored):**

- `expenses_db` — SQLite database storing all expense records
- `budget.db` — SQLite database storing budget configurations

---

## Notes

- `main_local.py` is the file to use for local Claude Desktop integration. It uses synchronous SQLite via the standard `sqlite3` module.
- `main.py` is a separate HTTP-based server intended for cloud/production deployments and is **not needed** for local use.
- Both databases (`expenses_db` and `budget.db`) are created automatically on first run — no setup required.
- All monetary amounts are stored as floats; use whatever currency you prefer, just stay consistent.
