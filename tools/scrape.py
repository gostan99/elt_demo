import json
import re
import argparse
from pathlib import Path
from typing import Any

from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import html

from config import settings
import logging


STAR_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
logger = logging.getLogger("etl_demo.scrape")


def _new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def _slug_from_url(u: str) -> str:
    """builds a safe filename from a product URL so we can save the raw HTML per book"""

    path = urlparse(u).path.rstrip("/")
    name = path.split("/")[-2]
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name)


def _parse_listing(doc: html.HtmlElement, base_url: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for art in doc.xpath("//article[contains(@class,'product_pod')]"):
        rel = art.xpath(".//h3/a/@href")
        if not rel:
            continue
        link = urljoin(base_url, rel[0])
        items.append({"product_url": link})
    return items


def _parse_product(doc: html.HtmlElement) -> dict[str, Any]:
    prod_nodes = doc.xpath("//div[contains(@class, 'product_main')]")
    if not prod_nodes:
        logger.warning("product_main not found; returning empty fields")
        return {"title": "", "price": "", "availability": "", "star_rating": ""}
    prod = prod_nodes[0]
    title = (prod.xpath(".//h1/text()") or [""])[0].strip()
    price = (prod.xpath(".//p[contains(@class,'price_color')]/text()") or [""])[0].strip()
    avail_nodes = prod.xpath(".//p[contains(@class,'instock')]")
    avail_txt = avail_nodes[0].text_content().strip() if avail_nodes else ""
    star_nodes = doc.xpath("//p[contains(@class,'star-rating')]")
    star_cls = star_nodes[0].get("class", "") if star_nodes else ""
    rating_word = None
    for key in STAR_MAP:
		if key in star_cls:
			rating_word = key
			break
    return {"title": title, "price": price, "availability": avail_txt, "star_rating": STAR_MAP.get(rating_word or "", None)}


def scrape(category_url: str, pages: int) -> None:
    session = _new_session()

    # Follow category pages up to N
    to_visit: list[str] = []
    seen: set[str] = set()
    base = category_url.rstrip("/")
    current = base
    to_visit.append(current)

    products: list[dict[str, Any]] = []

    for i in range(pages):
        if not to_visit:
            break
        url = to_visit.pop(0)
        if url in seen:
            continue
        seen.add(url)

        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        doc = html.fromstring(resp.text)

        # Find products on listing
        items = _parse_listing(doc, url)
        products.extend(items)

        # discover next page
        nxt = doc.xpath("//li[@class='next']/a/@href")
        if nxt:
            to_visit.append(urljoin(url, nxt[0]))

    # Visit each product page, save raw HTML, extract details
    output: list[dict[str, Any]] = []
    for link, base in products.items():
        resp = session.get(link, timeout=20)
        resp.raise_for_status()
        slug = _slug_from_url(link)
        html_path = Path(settings.html_backup_dir) / f"{slug}.html"
        html_path.write_text(resp.text, encoding="utf-8")
				
        doc = html.fromstring(resp.text)
        details = _parse_product(doc)
        record = {
            **details,
            "product_url": link,
        }
        output.append(record)

    # Save JSON
    Path(settings.books_json).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape books.toscrape category pages")
    parser.add_argument("--category-url", dest="category_url", required=True, help="Category URL to scrape")
    parser.add_argument("--pages", dest="pages", type=int, default=3, help="Number of pages to scrape (default 3)")
    args = parser.parse_args()
    scrape(args.category_url, args.pages)
