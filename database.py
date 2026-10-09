import hashlib
import sqlite3
import pandas as pd

DB_FILE = "phd_positions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            university TEXT,
            region TEXT,
            position_title TEXT,
            department TEXT,
            domains TEXT,
            application_mode TEXT,
            pi_name TEXT,
            pi_email TEXT,
            deadline TEXT,
            min_cgpa TEXT,
            degree_required TEXT,
            language_req TEXT,
            application_link TEXT,
            source_url TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def compute_hash(university: str, title: str, deadline: str) -> str:
    raw = f"{str(university).strip().lower()}_{str(title).strip().lower()}_{str(deadline).strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def upsert_position(entry: dict, university: str, region: str, source_url: str) -> bool:
    pos_id = compute_hash(university, entry.get("position_title", ""), entry.get("application_deadline", ""))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM positions WHERE id = ?", (pos_id,))
    if cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("""
        INSERT INTO positions (
            id, university, region, position_title, department, domains,
            application_mode, pi_name, pi_email, deadline, min_cgpa,
            degree_required, language_req, application_link, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pos_id, university, region, entry.get("position_title"),
        entry.get("department_or_lab"), ", ".join(entry.get("matched_domains", [])),
        entry.get("application_mode"), entry.get("pi_name"),
        entry.get("pi_email"), entry.get("application_deadline"),
        entry.get("min_cgpa_or_grade"), entry.get("degree_required"),
        entry.get("language_requirements"), entry.get("application_link") or source_url,
        source_url
    ))
    conn.commit()
    conn.close()
    return True

def get_all_positions() -> pd.DataFrame:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM positions ORDER BY discovered_at DESC", conn)
    conn.close()
    return df
