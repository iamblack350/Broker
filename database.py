import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")

    )

def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        firstname TEXT NOT NULL,
        lastname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password BYTEA NOT NULL
    );
    """)

    # profile holds user-visible info + balance (USD)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile(
        id SERIAL PRIMARY KEY,
        userid INTEGER NOT NULL UNIQUE,
        firstname TEXT NOT NULL,
        lastname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        nationality TEXT,
        balance REAL DEFAULT 0.0,
        FOREIGN KEY(userid) REFERENCES users(id)
    );
    """)
    conn.commit()
    conn.close()
