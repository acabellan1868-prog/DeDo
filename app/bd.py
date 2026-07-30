"""Conexión y utilidades de base de datos SQLite."""

import sqlite3
from pathlib import Path

from app.config import RUTA_BD

_DB_PATH = RUTA_BD


def obtener_conexion() -> sqlite3.Connection:
    """Abre una conexión SQLite con row_factory y foreign keys activados."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def inicializar_bd():
    """Crea las tablas si no existen ejecutando esquema.sql."""
    ruta_esquema = Path(__file__).parent / "esquema.sql"
    conn = obtener_conexion()
    conn.executescript(ruta_esquema.read_text(encoding="utf-8"))
    conn.close()


def consultar_todos(sql: str, parametros: tuple = ()) -> list[dict]:
    """Ejecuta SELECT y devuelve todas las filas como lista de dicts."""
    conn = obtener_conexion()
    try:
        filas = conn.execute(sql, parametros).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conn.close()


def consultar_uno(sql: str, parametros: tuple = ()) -> dict | None:
    """Ejecuta SELECT y devuelve una fila como dict, o None."""
    conn = obtener_conexion()
    try:
        fila = conn.execute(sql, parametros).fetchone()
        return dict(fila) if fila else None
    finally:
        conn.close()


def ejecutar(sql: str, parametros: tuple = ()) -> int:
    """Ejecuta INSERT/UPDATE/DELETE y devuelve el lastrowid."""
    conn = obtener_conexion()
    try:
        cursor = conn.execute(sql, parametros)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
