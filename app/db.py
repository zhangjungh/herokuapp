from __future__ import annotations

import hashlib
import json
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import psycopg2
import psycopg2.extras
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash


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


def _local_admin_file() -> Path:
    path = Path(current_app.config["LOCAL_ADMIN_FILE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_local_admin() -> dict:
    path = _local_admin_file()
    if path.exists():
        return json.loads(path.read_text())

    data = {
        "username": current_app.config["DEFAULT_ADMIN_USERNAME"],
        "password_hash": generate_password_hash(current_app.config["DEFAULT_ADMIN_PASSWORD"]),
        "must_change_password": True,
        "privilege": 999,
        "auth_source": "local-bootstrap",
    }
    path.write_text(json.dumps(data, indent=2))
    return data


def _write_local_admin(data: dict) -> None:
    _local_admin_file().write_text(json.dumps(data, indent=2))


def verify_local_admin(username: str, password: str) -> dict | None:
    admin = _read_local_admin()
    if username != admin.get("username"):
        return None
    if not check_password_hash(admin["password_hash"], password):
        return None
    return {
        "username": admin["username"],
        "privilege": admin.get("privilege", 999),
        "must_change_password": bool(admin.get("must_change_password", False)),
        "auth_source": admin.get("auth_source", "local-bootstrap"),
    }


def update_local_admin_password(current_username: str, new_username: str, new_password: str) -> dict:
    admin = _read_local_admin()
    if current_username != admin.get("username"):
        raise ValueError("local admin username mismatch")

    updated = {
        **admin,
        "username": new_username,
        "password_hash": generate_password_hash(new_password),
        "must_change_password": False,
    }
    _write_local_admin(updated)
    return {
        "username": updated["username"],
        "privilege": updated.get("privilege", 999),
        "must_change_password": False,
        "auth_source": updated.get("auth_source", "local-bootstrap"),
    }


def verify_password(username: str, password: str) -> dict | None:
    local_user = verify_local_admin(username, password)
    if local_user:
        return local_user

    user = fetch_user(username)
    if not user:
        return None

    salted = f"{password}{current_app.config.get('PASSWORD_SALT', '')}"
    digest = hashlib.sha1(salted.encode()).hexdigest()
    if digest == user.get("password"):
        return {
            **user,
            "username": user.get("username", username),
            "must_change_password": False,
            "auth_source": "legacy-db",
        }
    return None
