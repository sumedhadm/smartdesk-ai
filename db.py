import hashlib
import hmac
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "smartdesk.db"
ITERATIONS = 600_000
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                description TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )


# ---------- Password hashing (stdlib only) ----------
def _hash(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2${ITERATIONS}${salt.hex()}${dk.hex()}"


def _verify(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


_DUMMY_HASH = _hash("dummy-password")  # keeps timing similar for unknown usernames


# ---------- Users ----------
def register_user(username: str, password: str) -> tuple[bool, str]:
    username = (username or "").strip()
    password = password or ""
    if not USERNAME_RE.match(username):
        return False, "Username must be 3-30 letters, numbers or underscores."
    if not (8 <= len(password) <= 128):
        return False, "Password must be 8-128 characters."
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username.lower(), _hash(password)),
            )
        return True, "Account created. You can log in now."
    except sqlite3.IntegrityError:
        return False, "That username is taken."


def authenticate(username: str, password: str) -> int | None:
    with _conn() as c:
        row = c.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            ((username or "").strip().lower(),),
        ).fetchone()
    ok = _verify(password or "", row["password_hash"] if row else _DUMMY_HASH)
    return row["id"] if (row and ok) else None


# ---------- Tasks ----------
def save_task(user_id: int, description: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO tasks (user_id, description) VALUES (?, ?)",
            (user_id, description),
        )
        return cur.lastrowid


def list_tasks(user_id: int) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, description, done FROM tasks WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
    return [{"id": r["id"], "description": r["description"], "done": bool(r["done"])} for r in rows]