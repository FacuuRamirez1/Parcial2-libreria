"""Rutas HTTP del módulo autores (se completa en el change C-04)."""

from fastapi import APIRouter

router = APIRouter(prefix="/autores", tags=["autores"])
