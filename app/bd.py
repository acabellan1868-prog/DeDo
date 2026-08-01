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
    """Crea las tablas si no existen ejecutando esquema.sql, y aplica migraciones."""
    ruta_esquema = Path(__file__).parent / "esquema.sql"
    conn = obtener_conexion()
    conn.executescript(ruta_esquema.read_text(encoding="utf-8"))
    conn.close()
    _migrar_estado_por_capturar()


def _migrar_estado_por_capturar():
    """Añade 'por_capturar' al CHECK de catalogo.estado si falta.

    SQLite no permite modificar un CHECK con ALTER TABLE, así que hay que
    reconstruir la tabla conservando los datos existentes.
    """
    conn = obtener_conexion()
    try:
        definicion = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='catalogo'"
        ).fetchone()
        if not definicion or "por_capturar" in definicion[0]:
            return

        conn.execute("ALTER TABLE catalogo RENAME TO catalogo_old")
        conn.execute(
            """CREATE TABLE catalogo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                marca TEXT,
                categoria TEXT,
                descripcion_visual TEXT,
                zona TEXT,
                supermercado_habitual TEXT,
                stock_minimo REAL DEFAULT 1,
                unidad TEXT DEFAULT 'unidad',
                caducidad_dias_defecto INTEGER,
                estado TEXT DEFAULT 'activo' CHECK(estado IN ('activo', 'por_definir', 'por_capturar')),
                creado_en TEXT DEFAULT (datetime('now'))
            )"""
        )
        conn.execute(
            """INSERT INTO catalogo
               (id, nombre, marca, categoria, descripcion_visual, zona, supermercado_habitual,
                stock_minimo, unidad, caducidad_dias_defecto, estado, creado_en)
               SELECT id, nombre, marca, categoria, descripcion_visual, zona, supermercado_habitual,
                      stock_minimo, unidad, caducidad_dias_defecto, estado, creado_en
               FROM catalogo_old"""
        )
        conn.execute("DROP TABLE catalogo_old")
        conn.commit()
    finally:
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
