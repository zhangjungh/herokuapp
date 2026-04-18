"""Legacy compatibility shim.

Primary application factory now lives in app/main.py.
"""

from app.main import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
