"""Conexión y utilidades de base de datos SQLite."""

import os
import sqlite3
from contextlib import contextmanager

_DB_PATH = os.getenv("DEDO_DB_PATH", "data/dedo.db")


@contextmanager
def obtener_conexion():
    """Abre una conexión SQLite con row_factory y cierre automático."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
