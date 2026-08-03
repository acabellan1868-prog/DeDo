"""DeDo — Endpoints del catálogo de productos."""

import sqlite3

from fastapi import APIRouter, HTTPException
from app import bd
from app.modelos import ProductoRespuesta, ProductoCrear, ProductoActualizar

ruta = APIRouter()


@ruta.get("", response_model=list[ProductoRespuesta])
def listar_productos():
    """Devuelve todos los productos del catálogo."""
    return bd.consultar_todos("SELECT * FROM catalogo ORDER BY nombre")


@ruta.get("/por-definir", response_model=list[ProductoRespuesta])
def listar_por_definir():
    """Devuelve productos con estado 'por_definir' pendientes de completar."""
    return bd.consultar_todos(
        "SELECT * FROM catalogo WHERE estado = 'por_definir' ORDER BY creado_en DESC"
    )


@ruta.get("/por-capturar", response_model=list[ProductoRespuesta])
def listar_por_capturar():
    """Devuelve productos marcados con estado 'por_capturar', pendientes de
    que la IA rellene sus datos a partir del catálogo del supermercado."""
    return bd.consultar_todos(
        "SELECT * FROM catalogo WHERE estado = 'por_capturar' ORDER BY creado_en DESC"
    )


@ruta.get("/{producto_id}", response_model=ProductoRespuesta)
def obtener_producto(producto_id: int):
    """Devuelve el detalle de un producto por su id."""
    producto = bd.consultar_uno("SELECT * FROM catalogo WHERE id = ?", (producto_id,))
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    return producto


@ruta.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(datos: ProductoCrear):
    """Crea un nuevo producto en el catálogo."""
    nuevo_id = bd.ejecutar(
        """INSERT INTO catalogo
           (nombre, marca, ean, categoria, descripcion_visual, zona, supermercado_habitual,
            stock_minimo, unidad, caducidad_dias_defecto, estado)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (datos.nombre, datos.marca, datos.ean, datos.categoria, datos.descripcion_visual, datos.zona,
         datos.supermercado_habitual, datos.stock_minimo, datos.unidad,
         datos.caducidad_dias_defecto, datos.estado),
    )
    return bd.consultar_uno("SELECT * FROM catalogo WHERE id = ?", (nuevo_id,))


@ruta.patch("/{producto_id}", response_model=ProductoRespuesta)
def actualizar_producto(producto_id: int, datos: ProductoActualizar):
    """Actualiza los campos enviados de un producto. Solo modifica lo que se manda."""
    existente = bd.consultar_uno("SELECT * FROM catalogo WHERE id = ?", (producto_id,))
    if not existente:
        raise HTTPException(404, "Producto no encontrado")

    campos = []
    valores = []
    for campo, valor in datos.model_dump(exclude_none=True).items():
        campos.append(f"{campo} = ?")
        valores.append(valor)

    if campos:
        valores.append(producto_id)
        bd.ejecutar(
            f"UPDATE catalogo SET {', '.join(campos)} WHERE id = ?",
            tuple(valores),
        )

    return bd.consultar_uno("SELECT * FROM catalogo WHERE id = ?", (producto_id,))


@ruta.delete("/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int):
    """Elimina un producto del catálogo."""
    existente = bd.consultar_uno("SELECT * FROM catalogo WHERE id = ?", (producto_id,))
    if not existente:
        raise HTTPException(404, "Producto no encontrado")
    try:
        bd.ejecutar("DELETE FROM catalogo WHERE id = ?", (producto_id,))
    except sqlite3.IntegrityError:
        raise HTTPException(
            409,
            "No se puede borrar: el producto tiene stock, tickets o histórico de precios asociados",
        )
