import sqlite3, json, os, time

DB_PATH = os.getenv("DB_PATH", "app.db")

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT,          -- convert | analyze | chat | insights
          provider TEXT,      -- openai | groq | local
          input_preview TEXT,
          result_json TEXT,
          ts INTEGER
        )
        """)
        con.commit()

def save_history(kind: str, provider: str, input_preview: str, result_obj):
    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO history(kind,provider,input_preview,result_json,ts) VALUES (?,?,?,?,?)",
                        (kind, provider, input_preview, json_dump(result_obj), int(time.time())))
            con.commit()
    except Exception:
        pass

def json_dump(o):
    try:
        import json
        return json.dumps(o)[:1_000_000]
    except Exception:
        return "{}"
