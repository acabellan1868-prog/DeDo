"""DeDo — Endpoints de la lista de la compra."""

from fastapi import APIRouter, HTTPException
from app import bd
from app.modelos import ItemListaRespuesta, ItemListaCrear

ruta = APIRouter()

_SQL_LISTA_CON_NOMBRE = """
    SELECT l.*, c.nombre as nombre_producto
    FROM lista_compra l
    LEFT JOIN catalogo c ON c.id = l.producto_id
"""


@ruta.get("", response_model=list[ItemListaRespuesta])
def listar():
    """Devuelve la lista de la compra completa."""
    return bd.consultar_todos(_SQL_LISTA_CON_NOMBRE + " ORDER BY l.creado_en DESC")


@ruta.post("", response_model=ItemListaRespuesta, status_code=201)
def añadir(datos: ItemListaCrear):
    """Añade un producto a la lista. Puede ser del catálogo o nombre libre."""
    if not datos.producto_id and not datos.nombre_libre:
        raise HTTPException(400, "Indica producto_id o nombre_libre")

    if datos.producto_id:
        producto = bd.consultar_uno("SELECT id FROM catalogo WHERE id = ?", (datos.producto_id,))
        if not producto:
            raise HTTPException(404, "Producto no encontrado en el catálogo")

    nuevo_id = bd.ejecutar(
        "INSERT INTO lista_compra (producto_id, nombre_libre, cantidad, unidad, motivo) VALUES (?, ?, ?, ?, ?)",
        (datos.producto_id, datos.nombre_libre, datos.cantidad, datos.unidad, datos.motivo),
    )
    return bd.consultar_uno(_SQL_LISTA_CON_NOMBRE + " WHERE l.id = ?", (nuevo_id,))


@ruta.delete("/{item_id}", status_code=204)
def eliminar(item_id: int):
    """Elimina un item de la lista (marcar como comprado)."""
    existente = bd.consultar_uno("SELECT id FROM lista_compra WHERE id = ?", (item_id,))
    if not existente:
        raise HTTPException(404, "Item no encontrado en la lista")
    bd.ejecutar("DELETE FROM lista_compra WHERE id = ?", (item_id,))


@ruta.delete("", status_code=204)
def vaciar():
    """Vacía la lista de la compra completa."""
    bd.ejecutar("DELETE FROM lista_compra")
