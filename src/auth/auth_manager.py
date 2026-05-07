import sqlite3
import hashlib
import json
import os
import re
from pathlib import Path

DB_PATH      = Path(__file__).parent.parent.parent / 'users.db'
SESSION_PATH = Path(__file__).parent.parent.parent / 'session.json'


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt.encode('utf-8'), 260_000
    ).hex()


def register_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return False, 'El correo no es válido.'
    if len(password) < 6:
        return False, 'La contraseña debe tener al menos 6 caracteres.'

    salt = os.urandom(32).hex()
    password_hash = _hash_password(password, salt)

    try:
        conn = _get_conn()
        conn.execute(
            'INSERT INTO users (email, password_hash, salt) VALUES (?, ?, ?)',
            (email, password_hash, salt)
        )
        conn.commit()
        conn.close()
        return True, 'Cuenta creada correctamente.'
    except sqlite3.IntegrityError:
        return False, 'Este correo ya está registrado.'


def save_session(email: str):
    SESSION_PATH.write_text(json.dumps({'email': email}), encoding='utf-8')


def load_session() -> str | None:
    if not SESSION_PATH.exists():
        return None
    try:
        data = json.loads(SESSION_PATH.read_text(encoding='utf-8'))
        return data.get('email') or None
    except Exception:
        return None


def clear_session():
    if SESSION_PATH.exists():
        SESSION_PATH.unlink()


def login_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    conn = _get_conn()
    row = conn.execute(
        'SELECT password_hash, salt FROM users WHERE email = ?', (email,)
    ).fetchone()
    conn.close()

    if not row:
        return False, 'Correo o contraseña incorrectos.'

    password_hash, salt = row
    if _hash_password(password, salt) == password_hash:
        return True, email
    return False, 'Correo o contraseña incorrectos.'
