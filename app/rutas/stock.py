"""DeDo — Endpoints del inventario (stock)."""

from fastapi import APIRouter, HTTPException
from app import bd
from app.modelos import StockRespuesta, StockCrear, StockActualizar

ruta = APIRouter()

_SQL_STOCK_CON_NOMBRE = """
    SELECT s.*, c.nombre as nombre_producto
    FROM stock s
    LEFT JOIN catalogo c ON c.id = s.producto_id
"""


@ruta.get("", response_model=list[StockRespuesta])
def listar_stock():
    """Devuelve el inventario completo con el nombre de cada producto."""
    return bd.consultar_todos(_SQL_STOCK_CON_NOMBRE + " ORDER BY c.nombre")


@ruta.get("/{producto_id}", response_model=list[StockRespuesta])
def stock_de_producto(producto_id: int):
    """Devuelve todas las entradas de stock de un producto concreto."""
    return bd.consultar_todos(
        _SQL_STOCK_CON_NOMBRE + " WHERE s.producto_id = ? ORDER BY s.fecha_caducidad",
        (producto_id,),
    )


@ruta.post("", response_model=StockRespuesta, status_code=201)
def añadir_stock(datos: StockCrear):
    """Añade una entrada de stock (cantidad, lote, fecha de caducidad)."""
    producto = bd.consultar_uno("SELECT id FROM catalogo WHERE id = ?", (datos.producto_id,))
    if not producto:
        raise HTTPException(404, "Producto no encontrado en el catálogo")

    nuevo_id = bd.ejecutar(
        "INSERT INTO stock (producto_id, cantidad, fecha_caducidad, lote) VALUES (?, ?, ?, ?)",
        (datos.producto_id, datos.cantidad, datos.fecha_caducidad, datos.lote),
    )
    return bd.consultar_uno(_SQL_STOCK_CON_NOMBRE + " WHERE s.id = ?", (nuevo_id,))


@ruta.patch("/{stock_id}", response_model=StockRespuesta)
def actualizar_stock(stock_id: int, datos: StockActualizar):
    """Actualiza cantidad o fecha de caducidad de una entrada de stock."""
    existente = bd.consultar_uno("SELECT * FROM stock WHERE id = ?", (stock_id,))
    if not existente:
        raise HTTPException(404, "Entrada de stock no encontrada")

    campos = []
    valores = []
    for campo, valor in datos.model_dump(exclude_none=True).items():
        campos.append(f"{campo} = ?")
        valores.append(valor)
    campos.append("actualizado_en = datetime('now')")

    valores.append(stock_id)
    bd.ejecutar(
        f"UPDATE stock SET {', '.join(campos)} WHERE id = ?",
        tuple(valores),
    )
    return bd.consultar_uno(_SQL_STOCK_CON_NOMBRE + " WHERE s.id = ?", (stock_id,))


@ruta.delete("/{stock_id}", status_code=204)
def eliminar_stock(stock_id: int):
    """Elimina una entrada de stock."""
    existente = bd.consultar_uno("SELECT * FROM stock WHERE id = ?", (stock_id,))
    if not existente:
        raise HTTPException(404, "Entrada de stock no encontrada")
    bd.ejecutar("DELETE FROM stock WHERE id = ?", (stock_id,))
