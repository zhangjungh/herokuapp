from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _read_legacy_config() -> tuple[dict[str, str], str]:
    parser = ConfigParser()
    path = BASE_DIR / "db.conf.ini"
    if not path.exists():
        return {}, ""

    parser.read(path)
    db: dict[str, str] = {}
    if parser.has_section("postgresql"):
        db = {key: value for key, value in parser.items("postgresql")}

    salt = ""
    if parser.has_section("pwsalt"):
        items = parser.items("pwsalt")
        if items:
            salt = items[0][1]

    return db, salt


def load_settings() -> dict[str, object]:
    legacy_db, legacy_salt = _read_legacy_config()

    session_dir = Path(os.getenv("SESSION_DIR", str(BASE_DIR / "instance" / "sessions")))
    session_dir.mkdir(parents=True, exist_ok=True)

    return {
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-change-me"),
        "DB_HOST": os.getenv("DB_HOST", legacy_db.get("host", "")),
        "DB_PORT": int(os.getenv("DB_PORT", legacy_db.get("port", "5432"))),
        "DB_USER": os.getenv("DB_USER", legacy_db.get("user", "")),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", legacy_db.get("pw", "")),
        "DB_NAME": os.getenv("DB_NAME", legacy_db.get("db", "")),
        "PASSWORD_SALT": os.getenv("PASSWORD_SALT", legacy_salt),
        "SESSION_DIR": session_dir,
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO").upper(),
    }
