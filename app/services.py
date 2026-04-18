from __future__ import annotations

import base64
import json
import logging
from typing import Any

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 9; motorola one power) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/72.0.3626.96 Mobile Safari/537.36"
)
SUPPORTED_SITES = ("cswhcs.", "dreamartscenter.", "muamh.", "jsmlny.")


def is_supported_url(url: str) -> bool:
    return any(site in url for site in SUPPORTED_SITES)


def encode_target(url: str) -> str:
    return base64.b64encode(url.encode("utf-8")).decode("ascii")


def decode_target(payload: str) -> str:
    return base64.b64decode(payload.encode("ascii")).decode("utf-8")


def parse_url(url: str) -> dict[str, Any] | None:
    if "jsmlny." in url:
        return parse_url_json(url)
    return parse_url_html(url)


def parse_url_html(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    LOGGER.info("fetch %s -> %s", url, response.status_code)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, features="lxml")
    title = soup.head.title.text if soup.head and soup.head.title else "Untitled"
    images = [
        image.get("data-original")
        for image in soup.find_all("img", class_="lazy")
        if image.get("data-original")
    ]

    base_prefix = url.split("/chapter")[0] if "/chapter" in url else url
    links: list[tuple[str, str]] = []

    def maybe_add(label: str) -> None:
        anchor = soup.find("a", string=label)
        if anchor and anchor.get("href"):
            links.append((f"/?data={encode_target(base_prefix + anchor['href'])}", label))

    for label in ("上一章", "上一页", "下一页", "下一章"):
        maybe_add(label)

    return {"title": title, "images": images, "links": links}


def parse_url_json(url: str) -> dict[str, Any] | None:
    root = "https://comiccdnhw.jsmlny.top/hcomic/chaptercontent?chapterId="
    chapter_id = url.split("chapterId=")[1]
    api_url = root + chapter_id
    headers = {"User-Agent": USER_AGENT}

    response = requests.get(api_url, headers=headers, timeout=20)
    LOGGER.info("fetch %s -> %s", api_url, response.status_code)
    response.raise_for_status()

    payload = json.loads(response.text)
    images = [entry["content"] for entry in payload["data"]["chapterContentList"]]
    links = [
        (f"/?data={encode_target(root + str(int(chapter_id) - 1))}", "上一章"),
        (f"/?data={encode_target(root + str(int(chapter_id) + 1))}", "下一章"),
    ]
    return {"title": chapter_id, "images": images, "links": links}
