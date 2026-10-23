# Claude-Connected SQL Insight Agent (MCP)

An MCP (Model Context Protocol) server that connects Claude to a live SQL database,
so you can ask questions in plain English and get SQL-backed insights.

**Stack:** Python, SQLite, Claude (MCP), SQL, AI

## How it works

```
prompt -> Claude reasoning -> MCP tool call -> SQL execution -> structured insight
```

1. You ask: "Which region had the highest revenue?"
2. Claude calls `list_tables` and `describe_table` to learn the schema.
3. A SQLite **metadata layer** (`schema_metadata`) gives Claude business context
   (e.g. "revenue counts Delivered orders only"), so queries are schema-aware.
4. Claude writes SQL and calls `run_sql`; the server runs it on a **read-only** connection.
5. Claude turns the rows into a plain-language insight.

## Tools

| Tool | Purpose |
|------|---------|
| `list_tables` | Tables and row counts |
| `describe_table` | Columns, types and business descriptions from the metadata layer |
| `run_sql` | Runs a single read-only SELECT/WITH query (max 200 rows) |

## Safety

- SQLite opened with `mode=ro` (cannot modify data)
- Only a single SELECT/WITH statement is accepted
- Write and DDL keywords are rejected
- Row limit on every result

## Setup

```bash
git clone https://github.com/<your-username>/sql-insight-agent-mcp.git
cd sql-insight-agent-mcp
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python setup_db.py        # creates sample sales.db + metadata layer
```

## Connect to Claude Desktop

Edit `claude_desktop_config.json` (Settings > Developer > Edit Config):

```json
{
  "mcpServers": {
    "sql-insight-agent": {
      "command": "/full/path/to/venv/bin/python",
      "args": ["/full/path/to/sql-insight-agent-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop. The tools appear under the hammer/connectors icon.

## Example prompts

- "What tables do we have and what do they contain?"
- "Which region generated the most revenue from delivered orders?"
- "Show monthly revenue trend and flag the weakest month."
- "Which product category has the highest return rate?"
- "Compare Wholesale vs Retail average order value."

## Use your own database

Set `SQL_AGENT_DB=/path/to/your.db` and fill the `schema_metadata` table
(`table_name, column_name, description`) with your business definitions.

## Project structure

```
server.py        MCP server (tools)
setup_db.py      Sample data + metadata layer
requirements.txt
README.md
```
