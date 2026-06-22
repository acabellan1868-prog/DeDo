"""DeDo — Endpoints de gestión de caducidades."""

from fastapi import APIRouter, HTTPException, Query
from app import bd
from app.modelos import CaducidadRespuesta, CaducidadActualizar

ruta = APIRouter()

_SQL_CADUCIDADES = """
    SELECT s.id, s.producto_id, c.nombre as nombre_producto,
           s.cantidad, s.fecha_caducidad,
           CAST(julianday(s.fecha_caducidad) - julianday('now') AS INTEGER) as dias_restantes
    FROM stock s
    JOIN catalogo c ON c.id = s.producto_id
    WHERE s.fecha_caducidad IS NOT NULL
"""


@ruta.get("/proximas", response_model=list[CaducidadRespuesta])
def proximas(dias: int = Query(7, description="Número de días vista")):
    """Devuelve productos que caducan en los próximos N días."""
    return bd.consultar_todos(
        _SQL_CADUCIDADES + " AND dias_restantes <= ? AND dias_restantes >= 0 ORDER BY dias_restantes",
        (dias,),
    )


@ruta.get("/vencidas", response_model=list[CaducidadRespuesta])
def vencidas():
    """Devuelve productos ya caducados."""
    return bd.consultar_todos(
        _SQL_CADUCIDADES + " AND dias_restantes < 0 ORDER BY dias_restantes"
    )


@ruta.post("/{stock_id}", response_model=CaducidadRespuesta)
def actualizar_caducidad(stock_id: int, datos: CaducidadActualizar):
    """Actualiza la fecha de caducidad de una entrada de stock manualmente."""
    existente = bd.consultar_uno("SELECT id FROM stock WHERE id = ?", (stock_id,))
    if not existente:
        raise HTTPException(404, "Entrada de stock no encontrada")

    bd.ejecutar(
        "UPDATE stock SET fecha_caducidad = ?, actualizado_en = datetime('now') WHERE id = ?",
        (datos.fecha_caducidad, stock_id),
    )
    return bd.consultar_uno(
        _SQL_CADUCIDADES + " AND s.id = ?",
        (stock_id,),
    )
