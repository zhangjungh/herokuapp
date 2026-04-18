from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from whitenoise import WhiteNoise

from .config import load_settings
from .db import fetch_answers, fetch_image, update_local_admin_password, verify_password
from .services import decode_target, is_supported_url, parse_url


class FileSessionStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def load(self, sid: str) -> dict:
        path = self.directory / f"{sid}.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}

    def save(self, sid: str, data: dict) -> None:
        path = self.directory / f"{sid}.json"
        path.write_text(json.dumps(data))

    def delete(self, sid: str) -> None:
        path = self.directory / f"{sid}.json"
        if path.exists():
            path.unlink()


session_store: FileSessionStore | None = None


def get_real_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("X-Real-IP", request.remote_addr or "unknown")


def current_session_data() -> dict:
    if "sid" not in session or session_store is None:
        return {"login": 0, "privilege": 0}
    return session_store.load(session["sid"]) or {"login": 0, "privilege": 0}


def is_logged_in() -> bool:
    return bool(current_session_data().get("login"))


def write_session_data(data: dict) -> None:
    global session_store
    if session_store is None:
        return
    if "sid" not in session:
        session["sid"] = uuid4().hex
    session_store.save(session["sid"], data)


def clear_session_data() -> None:
    global session_store
    sid = session.get("sid")
    if sid and session_store is not None:
        session_store.delete(sid)
    session.clear()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(load_settings())

    global session_store
    session_store = FileSessionStore(app.config["SESSION_DIR"])

    logging.basicConfig(level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO))
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=str(Path(app.root_path) / "static"), prefix="static/")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(app.static_folder, "favico.png")

    @app.route("/ip", methods=["GET", "POST"])
    def ip_echo():
        if request.method == "POST":
            try:
                data = request.get_json(force=True)
                if data.get("key") != "queryImage":
                    raise ValueError("wrong parameter")
                image = fetch_image(data.get("id"))
                if not image:
                    raise ValueError("wrong id")
                if isinstance(image.get("data"), str):
                    return app.response_class(image["data"], mimetype="application/json")
                return jsonify(image.get("data"))
            except Exception:
                return jsonify({"ip": get_real_ip()})
        return get_real_ip()

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if is_logged_in():
            session_data = current_session_data()
            if session_data.get("must_change_password"):
                return redirect(url_for("change_password"))
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("user", "")
            password = request.form.get("passwd", "")
            user = verify_password(username, password)
            if user:
                write_session_data(
                    {
                        "login": 1,
                        "privilege": user.get("privilege", 0),
                        "user": user.get("username", username),
                        "auth_source": user.get("auth_source", "unknown"),
                        "must_change_password": bool(user.get("must_change_password", False)),
                    }
                )
                if user.get("must_change_password"):
                    return redirect(url_for("change_password"))
                return redirect(url_for("index"))
            clear_session_data()
            return render_template(
                "login.html",
                msg="Wrong username or password!",
                default_username=app.config["DEFAULT_ADMIN_USERNAME"],
                default_password=app.config["DEFAULT_ADMIN_PASSWORD"],
            ), 401

        return render_template(
            "login.html",
            msg="Please log in",
            default_username=app.config["DEFAULT_ADMIN_USERNAME"],
            default_password=app.config["DEFAULT_ADMIN_PASSWORD"],
        )

    @app.route("/change-password", methods=["GET", "POST"])
    def change_password():
        if not is_logged_in():
            return redirect(url_for("login"))

        session_data = current_session_data()
        if session_data.get("auth_source") != "local-bootstrap":
            return redirect(url_for("index"))

        if request.method == "POST":
            new_username = request.form.get("new_user", "").strip()
            new_password = request.form.get("new_passwd", "")
            confirm_password = request.form.get("confirm_passwd", "")

            if not new_username:
                return render_template("change_password.html", msg="Username cannot be empty.") , 400
            if len(new_password) < 8:
                return render_template("change_password.html", msg="Password must be at least 8 characters."), 400
            if new_password != confirm_password:
                return render_template("change_password.html", msg="Passwords do not match."), 400

            updated = update_local_admin_password(session_data.get("user", ""), new_username, new_password)
            write_session_data(
                {
                    **session_data,
                    "user": updated["username"],
                    "must_change_password": False,
                }
            )
            return redirect(url_for("index"))

        return render_template("change_password.html", msg="Default credentials must be changed before continuing.")

    @app.route("/logout", methods=["POST"])
    def logout():
        clear_session_data()
        return redirect(url_for("login"))

    @app.route("/math")
    def math_view():
        if not is_logged_in():
            return redirect(url_for("login"))
        if current_session_data().get("must_change_password"):
            return redirect(url_for("change_password"))
        answers = fetch_answers()
        return render_template("math.html", items=answers)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if not is_logged_in():
            return redirect(url_for("login"))
        if current_session_data().get("must_change_password"):
            return redirect(url_for("change_password"))

        if request.method == "POST":
            target = request.form.get("tar", "").strip()
            return render_target(target)

        encoded = request.args.get("data")
        if encoded:
            try:
                target = decode_target(encoded)
                return render_target(target)
            except Exception:
                return render_template("index.html", msg=f"Invalid encoded URL from {get_real_ip()}")

        return render_template("index.html", msg=f"Hello: {get_real_ip()}")

    def render_target(target: str):
        if not target:
            return render_template("index.html", msg=f"Hello: {get_real_ip()}")
        if not is_supported_url(target):
            return render_template("index.html", msg="Unsupported URL")
        try:
            parsed = parse_url(target)
            if parsed and parsed.get("images"):
                return render_template(
                    "image.html",
                    title=parsed["title"],
                    images=parsed["images"],
                    links=parsed["links"],
                )
            return render_template("index.html", msg="No images found")
        except Exception as exc:
            app.logger.exception("Failed to parse target URL")
            return render_template("index.html", msg=f"Error: {exc}")

    return app
