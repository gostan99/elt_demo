from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from config import settings


class Book(BaseModel):
    title: str
    price: str
    availability: str
    product_url: str
    star_rating: Optional[int] = Field(default=None, ge=1, le=5)
    publisher_country: Optional[str] = None


class BookCreate(BaseModel):
    title: str
    price: str
    availability: str
    product_url: str
    star_rating: Optional[int] = Field(default=None, ge=1, le=5)
    publisher_country: Optional[str] = None


_STORE_LOCK = Lock()
_STORE: List[Book] = []


def _load_store() -> None:
    global _STORE
    path = Path(settings.books_with_country)
    if not path.exists():
        _STORE = []
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    _STORE = [Book.model_validate(item) for item in data]


def _persist_store() -> None:
    path = Path(settings.books_with_country)
    payload = [b.model_dump() for b in _STORE]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")





def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = settings.api_key
    if not expected:
        return
    if x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


app = FastAPI(title="Books API", version="1.0.0", dependencies=[Depends(require_api_key)])


@app.on_event("startup")
def on_startup() -> None:
    _load_store()


@app.get("/books", response_model=List[Book])
def list_books(country: Optional[str] = Query(default=None)) -> List[Book]:
    if not country:
        return _STORE
    key = country.strip().lower()
    return [b for b in _STORE if (b.publisher_country or "").lower() == key]


@app.post("/books", status_code=201, response_model=Book)
def add_book(payload: BookCreate) -> Book:
    with _STORE_LOCK:
        book = Book(**payload.model_dump())
        _STORE.append(book)
        _persist_store()
        return book


@app.delete("/books/{title}", status_code=204)
def delete_book(title: str) -> None:
    with _STORE_LOCK:
        idx = next((i for i, b in enumerate(_STORE) if b.title == title), None)
        if idx is None:
            raise HTTPException(status_code=404, detail="Book not found")
        _STORE.pop(idx)
        _persist_store()
