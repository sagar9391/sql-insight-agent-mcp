"""Claude-Connected SQL Insight Agent: an MCP server.

Flow: prompt -> Claude reasoning -> MCP tool call -> SQL execution -> insight
"""
import json
import os
import re
import sqlite3

from mcp.server.fastmcp import FastMCP

DB_PATH = os.environ.get(
    "SQL_AGENT_DB", os.path.join(os.path.dirname(__file__), "sales.db"))
MAX_ROWS = 200

mcp = FastMCP("sql-insight-agent")


def _connect() -> sqlite3.Connection:
    # Read-only connection: the agent can never modify data
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def list_tables() -> str:
    """List all data tables with their row counts. Call this first."""
    with _connect() as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name != 'schema_metadata'")]
        out = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
               for t in tables}
    return json.dumps(out, indent=2)


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Return columns, types and business descriptions for a table,
    pulled from the metadata layer, so SQL can be schema-aware."""
    with _connect() as conn:
        cols = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        if not cols:
            return f"Table '{table_name}' not found."
        desc = {r["column_name"]: r["description"] for r in conn.execute(
            "SELECT column_name, description FROM schema_metadata "
            "WHERE table_name = ?", (table_name,))}
    return json.dumps([{"column": c["name"], "type": c["type"],
                        "description": desc.get(c["name"], "")}
                       for c in cols], indent=2)


@mcp.tool()
def run_sql(query: str) -> str:
    """Execute a read-only SELECT query (max 200 rows) and return JSON rows."""
    q = query.strip().rstrip(";")
    if not re.match(r"^(select|with)\b", q, re.I) or ";" in q:
        return "Error: only a single SELECT/WITH query is allowed."
    if re.search(r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b",
                 q, re.I):
        return "Error: query contains a forbidden keyword."
    try:
        with _connect() as conn:
            rows = conn.execute(q).fetchmany(MAX_ROWS)
        return json.dumps([dict(r) for r in rows], indent=2, default=str)
    except sqlite3.Error as e:
        return f"SQL error: {e}"


if __name__ == "__main__":
    mcp.run()  # stdio transport
