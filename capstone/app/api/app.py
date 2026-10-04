"""Message board API.

A deliberately small backend: it stores short messages in PostgreSQL.
It exists so you can practise Docker networking, environment variables,
volumes and Compose. You do not need to understand Flask to use it.

Configuration (environment variables):
  DB_HOST       name of the database container, e.g. "db"   (required)
  DB_NAME       database name                                  (default: board)
  DB_USER       database user                                  (default: board)
  DB_PASSWORD   database password                              (required)
                or DB_PASSWORD_FILE: path to a file that contains it
  APP_ENV       any label, shown by /api/info                  (default: development)
  GREETING      any text, shown by /api/info                   (default: Hello from the API)
"""
import os
import socket
import sys

import psycopg
from flask import Flask, jsonify, request


def setting(name, default=None):
    """Read a setting from NAME, or from the file named in NAME_FILE (Docker secrets)."""
    path = os.environ.get(name + "_FILE")
    if path:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    value = os.environ.get(name, default)
    if value is None:
        # Fail fast, with a message that tells you exactly what is wrong.
        # Exit code 3 tells gunicorn "this app cannot start": it stops instead of retrying forever,
        # so the container stops too and `docker ps -a` / `docker logs` show you the problem.
        print(f"ERROR: required setting {name} is missing. "
              f"Set the environment variable {name} (or {name}_FILE).", file=sys.stderr, flush=True)
        sys.exit(3)
    return value


DB = {
    "host": setting("DB_HOST"),
    "dbname": setting("DB_NAME", "board"),
    "user": setting("DB_USER", "board"),
    "password": setting("DB_PASSWORD"),
    "connect_timeout": 3,
}
APP_ENV = setting("APP_ENV", "development")
GREETING = setting("GREETING", "Hello from the API")

app = Flask(__name__)


def db():
    return psycopg.connect(**DB)


@app.get("/api/health")
def health():
    try:
        with db() as conn:
            conn.execute("SELECT 1")
        return jsonify(status="ok", database="ok")
    except psycopg.Error as e:
        return jsonify(status="error", database=str(e).strip()), 503


@app.get("/api/info")
def info():
    return jsonify(greeting=GREETING, app_env=APP_ENV,
                   container_hostname=socket.gethostname(), database_host=DB["host"])


@app.get("/api/messages")
def list_messages():
    with db() as conn:
        rows = conn.execute("SELECT id, text, created_at FROM messages ORDER BY id").fetchall()
    return jsonify([{"id": r[0], "text": r[1], "created_at": r[2].isoformat()} for r in rows])


@app.post("/api/messages")
def add_message():
    text = str((request.get_json(silent=True) or {}).get("text", "")).strip()
    if not 1 <= len(text) <= 200:
        return jsonify(error="text must be 1-200 characters"), 400
    with db() as conn:
        row = conn.execute("INSERT INTO messages (text) VALUES (%s) RETURNING id", (text,)).fetchone()
    return jsonify(id=row[0], text=text), 201
