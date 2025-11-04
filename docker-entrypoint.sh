#!/usr/bin/env bash
set -euo pipefail

: "${CATEGORY_URL:=https://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html}"
: "${PAGES:=3}"
: "${PORT:=8000}"

BOOKS_FILE="${BOOKS_JSON:-$(python - <<'PY'
from config import settings
print(settings.books_json)
PY
)}"

BOOKS_WITH_COUNTRY_FILE="${BOOKS_WITH_COUNTRY:-$(python - <<'PY'
from config import settings
print(settings.books_with_country)
PY
)}"

if [ ! -f "$BOOKS_WITH_COUNTRY_FILE" ]; then
    echo "[entrypoint] Running initial scrape for $CATEGORY_URL (pages=$PAGES)"
    python -m tools.scrape --category-url "$CATEGORY_URL" --pages "$PAGES"
    echo "[entrypoint] Enriching books with country assignments"
    python -m tools.enrich
else
    echo "[entrypoint] Using existing dataset at $BOOKS_WITH_COUNTRY_FILE"
fi

exec uvicorn tools.serve:app --host 0.0.0.0 --port "$PORT"
