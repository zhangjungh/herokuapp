"""Legacy compatibility shim.

New code lives under app/db.py.
"""

from app.db import fetch_answers as get_answers
from app.db import fetch_image as get_image
from app.db import fetch_user as get_user


def init(_filename: str) -> None:
    return None


def put_anwsers(_text: str):
    return None


salt = ""
