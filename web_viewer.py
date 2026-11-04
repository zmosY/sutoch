"""
Interactive Web Viewer for Sutochno & Booking SQLite Database
Provides a sleek visual dashboard to browse tables, run SQL queries, and inspect AI aspects.
"""

import sqlite3
import webbrowser
import os
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Sutochno & Booking Database Viewer")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sutochno_booking.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def index(table: str = "properties", query: str = None):
    conn = get_db()
    cur = conn.cursor()

    # Get all tables and counts
    cur.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts_%'
        ORDER BY name;
    """)
    tables_list = [r["name"] for r in cur.fetchall()]

    table_counts = {}
    for t in tables_list:
        try:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {t}")
            table_counts[t] = cur.fetchone()["cnt"]
        except Exception:
            table_counts[t] = 0

    # Fetch data for current table or query
    columns = []
    rows = []
    error_msg = None

    if query:
        try:
            cur.execute(query)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = [dict(r) for r in cur.fetchmany(100)]
        except Exception as e:
            error_msg = str(e)
    else:
        if table in tables_list:
            cur.execute(f"SELECT * FROM {table} LIMIT 100")
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = [dict(r) for r in cur.fetchall()]

    conn.close()

    # Render HTML template
    table_nav_html = "".join([
        f"""<a href="/?table={t}" class="nav-item {'active' if t == table and not query else ''}">
            <span>{t}</span>
            <span class="badge">{table_counts.get(t, 0)}</span>
        </a>"""
        for t in tables_list
    ])

    table_headers_html = "".join([f"<th>{col}</th>" for col in columns])
    
    table_rows_html = ""
    for r in rows:
        cells = []
        for col in columns:
            val = r.get(col, "")
            val_str = str(val) if val is not None else "<span class='null'>NULL</span>"
            # Format badges
            if val == "positive":
                val_str = "<span class='badge pos'>positive</span>"
            elif val == "negative":
                val_str = "<span class='badge neg'>negative</span>"
            elif col == "rating_overall" or col == "rating_total":
                val_str = f"<b>⭐ {val}</b>"
            elif len(val_str) > 80:
                val_str = f"<span title='{val_str}'>{val_str[:77]}...</span>"
            cells.append(f"<td>{val_str}</td>")
        table_rows_html += f"<tr>{''.join(cells)}</tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Sutochno & Booking DB Viewer</title>
        <style>
            :root {{
                --bg: #0f172a;
                --panel: #1e293b;
                --border: #334155;
                --text: #f8fafc;
                --text-dim: #94a3b8;
                --accent: #38bdf8;
                --accent-hover: #0284c7;
                --green: #22c55e;
                --red: #ef4444;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
            body {{ background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }}
            
            /* Sidebar */
            .sidebar {{ width: 280px; background: var(--panel); border-right: 1px solid var(--border); display: flex; flex-direction: column; }}
            .brand {{ padding: 18px 20px; font-weight: 700; font-size: 16px; border-bottom: 1px solid var(--border); color: var(--accent); display: flex; align-items: center; gap: 8px; }}
            .nav-list {{ flex: 1; overflow-y: auto; padding: 12px 8px; display: flex; flex-direction: column; gap: 4px; }}
            .nav-item {{ display: flex; justify-content: space-between; align-items: center; padding: 9px 14px; text-decoration: none; color: var(--text-dim); border-radius: 6px; font-size: 13.5px; transition: all 0.15s; }}
            .nav-item:hover {{ background: #334155; color: #fff; }}
            .nav-item.active {{ background: var(--accent); color: #0f172a; font-weight: 600; }}
            .nav-item.active .badge {{ background: #0f172a; color: var(--accent); }}
            .badge {{ font-size: 11px; padding: 2px 7px; background: #334155; color: var(--text-dim); border-radius: 12px; font-weight: 600; }}
            .badge.pos {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }}
            .badge.neg {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
            
            /* Main Content */
            .content {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; }}
            .header {{ padding: 14px 24px; background: var(--panel); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ font-size: 18px; font-weight: 600; }}
            .header .subtitle {{ color: var(--text-dim); font-size: 13px; margin-top: 2px; }}
            
            /* SQL Bar */
            .sql-box {{ padding: 14px 24px; background: #131d31; border-bottom: 1px solid var(--border); }}
            .sql-form {{ display: flex; gap: 10px; }}
            .sql-input {{ flex: 1; background: #0f172a; border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; color: #fff; font-family: monospace; font-size: 13px; }}
            .sql-input:focus {{ outline: none; border-color: var(--accent); }}
            .sql-btn {{ background: var(--accent); color: #0f172a; border: none; padding: 0 20px; border-radius: 6px; font-weight: 600; cursor: pointer; transition: background 0.15s; }}
            .sql-btn:hover {{ background: var(--accent-hover); }}
            
            /* Table Area */
            .table-wrap {{ flex: 1; overflow: auto; padding: 20px 24px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: var(--panel); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }}
            th {{ background: #243248; text-align: left; padding: 10px 14px; font-weight: 600; color: #cbd5e1; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; white-space: nowrap; }}
            td {{ padding: 10px 14px; border-bottom: 1px solid #2d3c52; color: #e2e8f0; vertical-align: top; max-width: 320px; }}
            tr:hover td {{ background: #26354a; }}
            .null {{ color: #64748b; font-style: italic; }}
            .error {{ color: var(--red); background: rgba(239, 68, 68, 0.1); padding: 12px 16px; border-radius: 6px; margin-bottom: 14px; border: 1px solid var(--red); }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand">
                <span>🗄️</span>
                <span>Sutochno / Booking DB</span>
            </div>
            <div class="nav-list">
                {table_nav_html}
            </div>
        </div>
        <div class="content">
            <div class="header">
                <div>
                    <h1>{'Таблица: ' + table if not query else 'Результат SQL-запроса'}</h1>
                    <div class="subtitle">Показано {len(rows)} строк (максимум 100)</div>
                </div>
                <div>
                    <a href="/?table={table}" style="color: var(--accent); text-decoration: none; font-size: 13px;">Сбросить фильтр</a>
                </div>
            </div>
            
            <div class="sql-box">
                <form class="sql-form" action="/" method="get">
                    <input type="text" name="query" class="sql-input" placeholder="SELECT * FROM review_aspects WHERE sentiment = 'negative'..." value="{query or ''}">
                    <button type="submit" class="sql-btn">Выполнить SQL</button>
                </form>
            </div>

            <div class="table-wrap">
                {f'<div class="error"><b>Ошибка SQL:</b> {error_msg}</div>' if error_msg else ''}
                <table>
                    <thead>
                        <tr>{table_headers_html}</tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    port = 8501
    url = f"http://127.0.0.1:{port}"
    print(f"\n[DB VIEWER] Запуск визуального просмотрщика базы данных...")
    print(f"[DB VIEWER] Откройте в браузере: {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
