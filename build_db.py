import sqlite3
import pandas as pd
import os

def build_database():
    db_file = 'lawgic.db'
    csv_file = 'bns_laws.csv'

    if os.path.exists(db_file):
        os.remove(db_file)
        print("Old database removed.")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # ─── Laws table (smart-chunked) ───
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS laws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            description TEXT NOT NULL,
            definition TEXT,
            punishment TEXT,
            illustrations TEXT,
            exceptions TEXT,
            full_text TEXT,
            pos_precedent TEXT,
            neg_precedent TEXT
        )
    ''')

    # ─── Similar cases table ───
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS similar_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fir_id TEXT,
            title TEXT NOT NULL,
            summary TEXT,
            source_url TEXT,
            court TEXT,
            sections TEXT,
            similarity_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ─── Cache tables ───
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_cache (
            query_hash TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_cache (
            prompt_hash TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            provider TEXT,
            created_at REAL NOT NULL
        )
    ''')

    try:
        df = pd.read_csv(csv_file)
        df.fillna("", inplace=True)

        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO laws (section, description, definition, punishment,
                                  illustrations, exceptions, full_text,
                                  pos_precedent, neg_precedent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['section'],
                row['description'],
                row.get('definition', ''),
                row.get('punishment', ''),
                row.get('illustrations', ''),
                row.get('exceptions', ''),
                row.get('full_text', ''),
                row.get('pos_precedent', ''),
                row.get('neg_precedent', ''),
            ))

        conn.commit()
        print(f"Success! Lawgic DB powered by {len(df)} smart-chunked BNS sections.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    build_database()