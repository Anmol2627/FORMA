"""Local SQLite storage for the FORMA desktop prototype.

This is a development store. It can later be replaced by calls to the course project's API.
"""
import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "forma_local.db"


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
            prompt TEXT NOT NULL,
            explanation TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            option_text TEXT NOT NULL,
            is_correct INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)


def _password_record(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return salt.hex(), digest.hex()


def register_user(display_name, email, password):
    salt, digest = _password_record(password)
    try:
        with connect() as con:
            cur = con.execute(
                "INSERT INTO users(display_name,email,password_salt,password_hash) VALUES(?,?,?,?)",
                (display_name.strip(), email.strip().lower(), salt, digest),
            )
            return dict(con.execute(
                "SELECT id,display_name,email FROM users WHERE id=?", (cur.lastrowid,)
            ).fetchone())
    except sqlite3.IntegrityError:
        return None


def authenticate_user(email, password):
    with connect() as con:
        row = con.execute(
            "SELECT id,display_name,email,password_salt,password_hash FROM users WHERE email=? COLLATE NOCASE",
            (email.strip().lower(),),
        ).fetchone()
    if not row:
        return None
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(row["password_salt"]), 240_000
    ).hex()
    if not hmac.compare_digest(digest, row["password_hash"]):
        return None
    return {"id": row["id"], "display_name": row["display_name"], "email": row["email"]}


def create_quiz(owner_id, title, description, questions):
    with connect() as con:
        cur = con.execute(
            "INSERT INTO quizzes(owner_id,title,description) VALUES(?,?,?)",
            (owner_id, title.strip(), description.strip()),
        )
        quiz_id = cur.lastrowid
        for question in questions:
            qcur = con.execute(
                "INSERT INTO questions(quiz_id,prompt,explanation) VALUES(?,?,?)",
                (quiz_id, question["prompt"].strip(), question.get("explanation", "").strip()),
            )
            for index, option_text in enumerate(question["options"]):
                con.execute(
                    "INSERT INTO options(question_id,option_text,is_correct) VALUES(?,?,?)",
                    (qcur.lastrowid, option_text.strip(), int(index == question["correct_index"])),
                )
        return quiz_id


def list_quizzes(owner_id):
    with connect() as con:
        rows = con.execute("""
            SELECT q.id,q.title,q.description,q.created_at,
                   COUNT(DISTINCT qu.id) AS question_count
            FROM quizzes q LEFT JOIN questions qu ON qu.quiz_id=q.id
            WHERE q.owner_id=? GROUP BY q.id ORDER BY q.id DESC
        """, (owner_id,)).fetchall()
        return [dict(row) for row in rows]


def get_quiz(quiz_id):
    with connect() as con:
        quiz = con.execute("SELECT * FROM quizzes WHERE id=?", (quiz_id,)).fetchone()
        if not quiz:
            return None
        result = dict(quiz)
        questions = con.execute("SELECT * FROM questions WHERE quiz_id=? ORDER BY id", (quiz_id,)).fetchall()
        result["questions"] = []
        for question in questions:
            q = dict(question)
            q["options"] = [dict(row) for row in con.execute(
                "SELECT * FROM options WHERE question_id=? ORDER BY id", (question["id"],)
            ).fetchall()]
            result["questions"].append(q)
        return result


def save_attempt(user_id, quiz_id, score, total):
    with connect() as con:
        con.execute(
            "INSERT INTO attempts(user_id,quiz_id,score,total) VALUES(?,?,?,?)",
            (user_id, quiz_id, score, total),
        )


def list_attempts(user_id):
    with connect() as con:
        rows = con.execute("""
            SELECT a.score,a.total,a.created_at,q.title
            FROM attempts a JOIN quizzes q ON q.id=a.quiz_id
            WHERE a.user_id=? ORDER BY a.id DESC LIMIT 20
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]
