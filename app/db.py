from __future__ import annotations

import hashlib
from contextlib import closing
from dataclasses import dataclass

import psycopg2
import psycopg2.extras
from flask import current_app


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    dbname: str


def _db_config() -> DatabaseConfig | None:
    host = current_app.config.get("DB_HOST")
    user = current_app.config.get("DB_USER")
    dbname = current_app.config.get("DB_NAME")
    if not (host and user and dbname):
        return None

    return DatabaseConfig(
        host=host,
        port=int(current_app.config.get("DB_PORT", 5432)),
        user=user,
        password=current_app.config.get("DB_PASSWORD", ""),
        dbname=dbname,
    )


def get_connection():
    cfg = _db_config()
    if cfg is None:
        return None

    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        dbname=cfg.dbname,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def fetch_user(username: str) -> dict | None:
    conn = get_connection()
    if conn is None:
        return None

    with closing(conn), conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
        return cur.fetchone()


def fetch_answers(limit: int = 10) -> list[dict]:
    conn = get_connection()
    if conn is None:
        return []

    with closing(conn), conn.cursor() as cur:
        cur.execute("SELECT * FROM maths ORDER BY id DESC LIMIT %s", (limit,))
        return list(cur.fetchall())


def fetch_image(image_id: str | int) -> dict | None:
    conn = get_connection()
    if conn is None:
        return None

    with closing(conn), conn.cursor() as cur:
        cur.execute("SELECT * FROM images WHERE id = %s LIMIT 1", (image_id,))
        return cur.fetchone()


def verify_password(username: str, password: str) -> dict | None:
    user = fetch_user(username)
    if not user:
        return None

    salted = f"{password}{current_app.config.get('PASSWORD_SALT', '')}"
    digest = hashlib.sha1(salted.encode()).hexdigest()
    if digest == user.get("password"):
        return user
    return None
