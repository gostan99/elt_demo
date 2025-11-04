# ETL Demo – Technical Exam Solution

## Docker (fastest way to run everything)

```bash
docker compose up --build
```

The entrypoint checks `data/books_with_country.json`. If missing, it scrapes
(default category, 3 pages) and enriches once, then serves the API on
`http://localhost:8000`. The `data/` folder is mounted so outputs persist between
runs.

Run the tools inside the container if you need to regenerate data manually:

```bash
docker compose exec books-api python -m tools.scrape --category-url ... --pages ...
docker compose exec books-api python -m tools.enrich
```

After running the tools inside the container, restart the service so FastAPI reloads the dataset
```bash
docker compose restart books-api
```
## Manual run (Python)

### Prerequisites

* Python 3.10+

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Part 1 – Scrape books.toscrape.com

1. Pick any category URL (example below).
2. Scrape at least 3 pages.

```bash
python -m tools.scrape --category-url https://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html --pages 3
```

Outputs:

- `data/books.json`
- Raw HTML backups under `data/html_backup/`

## Part 2 – Assign publisher countries

Requires `data/books.json` from Part 1.

```bash
python -m tools.enrich
```

Outputs:

- `data/books_with_country.json`
- Country cache: `data/cache/countries.json`

## Part 3 – REST API

```bash
uvicorn tools.serve:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /books`
- `GET /books?country=Anguilla`
- `POST /books`
- `DELETE /books/{title}` (URL‑encoded title)

> **Note:** the API loads the dataset into memory on startup. If you run
> `tools/scrape.py` / `tools/enrich.py` again while the API is running,
> restart the API so it picks up the new data.
