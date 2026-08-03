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


def _conexion_para_migracion() -> sqlite3.Connection:
    """Conexión con isolation_level=None (autocommit real de Python desactivado
    para su gestión implícita de transacciones).

    Con el isolation_level por defecto, Python comete implícitamente
    cualquier transacción abierta justo antes de ejecutar una sentencia DDL
    (CREATE/ALTER/DROP), aunque esa transacción se haya abierto con un
    BEGIN explícito. Eso rompe cualquier intento de envolver una secuencia
    de sentencias DDL en una transacción atómica. Con isolation_level=None,
    Python no gestiona nada por su cuenta: BEGIN/COMMIT/ROLLBACK explícitos
    controlan la transacción tal cual los ve SQLite.
    """
    conn = sqlite3.connect(_DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_bd():
    """Crea las tablas si no existen ejecutando esquema.sql, y aplica migraciones."""
    ruta_esquema = Path(__file__).parent / "esquema.sql"
    conn = obtener_conexion()
    conn.executescript(ruta_esquema.read_text(encoding="utf-8"))
    conn.close()
    _migrar_estado_por_capturar()
    _reparar_fk_catalogo()
    _migrar_columna_ean()


def _migrar_columna_ean():
    """Añade la columna 'ean' a catalogo si falta.

    El EAN (código de barras) lo asigna el fabricante vía GS1, no el
    supermercado — identifica el producto físico independientemente de
    dónde se compre. A diferencia de la migración de 'por_capturar', esta
    es un simple ALTER TABLE ADD COLUMN: no hace falta reconstruir la tabla
    porque SQLite sí permite añadir una columna nullable sin tocar el CHECK
    ni las claves foráneas de las tablas que apuntan a catalogo.
    """
    conn = _conexion_para_migracion()
    try:
        columnas = conn.execute("PRAGMA table_info(catalogo)").fetchall()
        if any(col["name"] == "ean" for col in columnas):
            return
        conn.execute("ALTER TABLE catalogo ADD COLUMN ean TEXT")
    finally:
        conn.close()


def _migrar_estado_por_capturar():
    """Añade 'por_capturar' al CHECK de catalogo.estado si falta.

    SQLite no permite modificar un CHECK con ALTER TABLE, así que hay que
    reconstruir la tabla conservando los datos existentes. Sigue el
    procedimiento seguro documentado por SQLite: FK desactivadas, todo en
    una transacción, verificación con foreign_key_check antes de confirmar.
    """
    conn = _conexion_para_migracion()
    try:
        definicion = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='catalogo'"
        ).fetchone()
        if not definicion or "por_capturar" in definicion[0]:
            return

        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.execute("BEGIN")
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
            comprobacion = conn.execute("PRAGMA foreign_key_check").fetchall()
            if comprobacion:
                raise RuntimeError(f"foreign_key_check encontró incidencias: {comprobacion}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
    finally:
        conn.close()


# Tablas con producto_id REFERENCES catalogo(id). Si en algún momento
# catalogo fue renombrada (p.ej. durante una migración anterior) y luego
# se borró la copia renombrada, SQLite reescribe automáticamente estas
# definiciones para apuntar al nombre renombrado — dejándolas "colgadas"
# de una tabla que ya no existe. Esta función lo detecta y lo repara.
_TABLAS_CON_FK_CATALOGO = {
    "stock": (
        """CREATE TABLE stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL REFERENCES catalogo(id),
            cantidad REAL DEFAULT 0,
            fecha_caducidad TEXT,
            lote TEXT,
            actualizado_en TEXT DEFAULT (datetime('now'))
        )""",
        "id, producto_id, cantidad, fecha_caducidad, lote, actualizado_en",
    ),
    "lista_compra": (
        """CREATE TABLE lista_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER REFERENCES catalogo(id),
            nombre_libre TEXT,
            cantidad REAL DEFAULT 1,
            unidad TEXT,
            motivo TEXT,
            creado_en TEXT DEFAULT (datetime('now'))
        )""",
        "id, producto_id, nombre_libre, cantidad, unidad, motivo, creado_en",
    ),
    "lineas_ticket": (
        """CREATE TABLE lineas_ticket (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id),
            producto_id INTEGER REFERENCES catalogo(id),
            nombre_raw TEXT,
            cantidad REAL,
            precio_unitario REAL,
            precio_total REAL
        )""",
        "id, ticket_id, producto_id, nombre_raw, cantidad, precio_unitario, precio_total",
    ),
    "historial_precios": (
        """CREATE TABLE historial_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL REFERENCES catalogo(id),
            supermercado TEXT,
            precio REAL,
            fecha TEXT,
            ticket_id INTEGER REFERENCES tickets(id)
        )""",
        "id, producto_id, supermercado, precio, fecha, ticket_id",
    ),
    "menu_productos": (
        """CREATE TABLE menu_productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER NOT NULL REFERENCES menu(id),
            producto_id INTEGER REFERENCES catalogo(id),
            nombre_libre TEXT
        )""",
        "id, menu_id, producto_id, nombre_libre",
    ),
}


def _reparar_fk_catalogo():
    """Reconstruye las tablas cuya referencia a catalogo quedó apuntando a
    catalogo_old (u otro nombre temporal de una reconstrucción previa)."""
    conn = _conexion_para_migracion()
    try:
        rotas = []
        for tabla in _TABLAS_CON_FK_CATALOGO:
            definicion = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
            ).fetchone()
            if definicion and "REFERENCES catalogo(id)" not in definicion[0]:
                rotas.append(tabla)

        if not rotas:
            return

        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.execute("BEGIN")
            for tabla in rotas:
                creacion, columnas = _TABLAS_CON_FK_CATALOGO[tabla]
                temporal = f"{tabla}_roto"
                conn.execute(f"ALTER TABLE {tabla} RENAME TO {temporal}")
                conn.execute(creacion)
                conn.execute(
                    f"INSERT INTO {tabla} ({columnas}) SELECT {columnas} FROM {temporal}"
                )
                conn.execute(f"DROP TABLE {temporal}")

            comprobacion = conn.execute("PRAGMA foreign_key_check").fetchall()
            if comprobacion:
                raise RuntimeError(f"foreign_key_check encontró incidencias: {comprobacion}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
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
