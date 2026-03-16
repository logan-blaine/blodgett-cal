from __future__ import annotations

from bs4 import BeautifulSoup, Tag
import requests

DEFAULT_SOURCE_URL = "https://recreation.gocrimson.com/sports/2021/5/14/facility-hours"
TARGET_ACCORDION_LABEL = "mac pool & blodgett pool"


def fetch_html(source_url: str = DEFAULT_SOURCE_URL, timeout: int = 30) -> str:
    response = requests.get(source_url, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split()).strip().lower()


def find_pool_accordion(soup: BeautifulSoup) -> Tag:
    for item in soup.select("li.c-story-blocks__structural_accordion_block__list-item"):
        label = item.select_one("button span.flex-item-1")
        if label is None:
            continue
        if normalize_text(label.get_text(" ", strip=True)) == TARGET_ACCORDION_LABEL:
            return item
    raise ValueError("Could not find the 'MAC Pool & Blodgett Pool' accordion section")


def find_pool_table(accordion: Tag) -> Tag:
    content = accordion.select_one(".c-story-blocks__structural_accordion_block__list-item-content")
    if content is None:
        raise ValueError("Pool accordion content is missing")

    for table in content.select("table"):
        headers = [normalize_text(th.get_text(" ", strip=True)) for th in table.select("thead th")]
        if "blodgett pool" in headers:
            return table

    raise ValueError("Could not find the Blodgett Pool table inside the pool accordion")
