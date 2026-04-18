FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/instance /app/instance/sessions \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ip', timeout=3).read()" || exit 1

CMD ["uv", "run", "gunicorn", "--workers", "2", "--threads", "4", "--bind", "0.0.0.0:8000", "wsgi:app"]
