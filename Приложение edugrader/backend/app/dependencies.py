from sqlalchemy.orm import Session
from .database import SessionLocal
from typing import Optional
from fastapi import Query

# Функция для получения сессии БД (исправленная версия)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для пагинации
def pagination_params(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество записей")
):
    return {"skip": skip, "limit": limit}