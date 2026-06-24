"""DeDo — Endpoints de historial y comparativa de precios."""

import logging

from fastapi import APIRouter, HTTPException

from app import bd
from app.modelos import PrecioRespuesta, ComparativaRespuesta

logger = logging.getLogger("dedo.precios")
ruta = APIRouter()


@ruta.get("/{producto_id}", response_model=list[PrecioRespuesta])
def historial_precios(producto_id: int):
    """Devuelve el historial de precios de un producto, por supermercado y fecha."""
    producto = bd.consultar_uno("SELECT id, nombre FROM catalogo WHERE id = ?", (producto_id,))
    if not producto:
        raise HTTPException(404, "Producto no encontrado")

    return bd.consultar_todos(
        """SELECT hp.*, c.nombre as nombre_producto
           FROM historial_precios hp
           JOIN catalogo c ON c.id = hp.producto_id
           WHERE hp.producto_id = ?
           ORDER BY hp.supermercado, hp.fecha DESC""",
        (producto_id,),
    )


@ruta.get("/comparativa/lista", response_model=list[ComparativaRespuesta])
def comparativa_lista():
    """Coste estimado de la lista de la compra en cada supermercado.

    Usa el último precio registrado de cada producto por supermercado.
    Solo incluye supermercados con precio conocido para al menos un producto de la lista.
    """
    items_lista = bd.consultar_todos(
        "SELECT producto_id FROM lista_compra WHERE producto_id IS NOT NULL"
    )
    if not items_lista:
        return []

    ids_productos = [str(i["producto_id"]) for i in items_lista]
    placeholders = ",".join("?" * len(ids_productos))

    # Último precio de cada producto por supermercado
    precios = bd.consultar_todos(
        f"""SELECT hp.producto_id, hp.supermercado, hp.precio, c.nombre as nombre_producto
            FROM historial_precios hp
            JOIN catalogo c ON c.id = hp.producto_id
            WHERE hp.producto_id IN ({placeholders})
              AND hp.fecha = (
                  SELECT MAX(hp2.fecha)
                  FROM historial_precios hp2
                  WHERE hp2.producto_id = hp.producto_id
                    AND hp2.supermercado = hp.supermercado
              )""",
        tuple(ids_productos),
    )

    # Agrupar por supermercado
    por_super: dict[str, dict] = {}
    for p in precios:
        s = p["supermercado"]
        if s not in por_super:
            por_super[s] = {"supermercado": s, "total_estimado": 0.0, "productos_con_precio": 0, "detalle": []}
        por_super[s]["total_estimado"] = round(por_super[s]["total_estimado"] + p["precio"], 2)
        por_super[s]["productos_con_precio"] += 1
        por_super[s]["detalle"].append({
            "producto_id": p["producto_id"],
            "nombre_producto": p["nombre_producto"],
            "precio": p["precio"],
        })

    return sorted(por_super.values(), key=lambda x: x["total_estimado"])
