import os
import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger("etl_demo.config")


def _load_dotenv() -> None:
    p = Path(".env")
    if not p.exists():
        logger.info(".env not found at %s; using environment defaults", p.resolve())
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


_load_dotenv()


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


@dataclass
class Settings:
    data_dir: Path
    html_backup_dir: Path
    cache_dir: Path
    books_json: Path
    books_with_country: Path
    countries_cache: Path
    api_key: str | None


def get_settings() -> Settings:
    data_dir = Path(_env("DATA_DIR", "./data")).resolve()
    html_backup_dir = Path(_env("HTML_BACKUP_DIR", str(data_dir / "html_backup"))).resolve()
    cache_dir = Path(_env("CACHE_DIR", str(data_dir / "cache"))).resolve()
    books_json = Path(_env("BOOKS_JSON", str(data_dir / "books.json"))).resolve()
    books_with_country = Path(
        _env("BOOKS_WITH_COUNTRY", str(data_dir / "books_with_country.json"))
    ).resolve()
    countries_cache = Path(
        _env("COUNTRIES_CACHE", str(cache_dir / "countries.json"))
    ).resolve()
    api_key = _env("API_KEY", "").strip() or None

    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    html_backup_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        data_dir=data_dir,
        html_backup_dir=html_backup_dir,
        cache_dir=cache_dir,
        books_json=books_json,
        books_with_country=books_with_country,
        countries_cache=countries_cache,
        api_key=api_key,
    )


settings = get_settings()
