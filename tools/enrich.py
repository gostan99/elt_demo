import json
import random
from pathlib import Path
from typing import Any

import requests

from config import settings


def load_books() -> list[dict[str, Any]]:
    if not Path(settings.books_json).exists():
        raise FileNotFoundError(f"Books file not found: {settings.books_json}")
    return json.loads(Path(settings.books_json).read_text(encoding="utf-8"))


def fetch_countries() -> list[str]:
    cache_path = Path(settings.countries_cache)
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(cached, list) and cached:
                return [str(c) for c in cached]
        except Exception:
            pass

    resp = requests.get("https://restcountries.com/v3.1/all", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    names: list[str] = []
    for item in data:
        name = item.get("name", {}).get("common")
        if name:
            names.append(name)
    names = sorted(set(names))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")
    return names


def enrich() -> None:
    books = load_books()
    countries = fetch_countries()
    if not countries:
        raise RuntimeError("No countries available")

    random.seed(42)
    for b in books:
        b["publisher_country"] = random.choice(countries)

    Path(settings.books_with_country).write_text(
        json.dumps(books, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    enrich()
