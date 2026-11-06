"""Rutas HTTP del módulo libros (se completa en el change C-04)."""

from fastapi import APIRouter

router = APIRouter(prefix="/libros", tags=["libros"])
