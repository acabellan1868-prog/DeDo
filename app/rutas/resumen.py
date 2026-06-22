"""DeDo — Endpoint de resumen para la tarjeta del portal hogarOS."""

from fastapi import APIRouter
from app import bd
from app.modelos import ResumenRespuesta

ruta = APIRouter()


@ruta.get("", response_model=ResumenRespuesta)
def resumen():
    """Estado general de DeDo para la tarjeta del portal."""
    productos_en_lista = bd.consultar_uno(
        "SELECT COUNT(*) as n FROM lista_compra"
    )["n"]

    stock_bajo = bd.consultar_uno(
        """SELECT COUNT(DISTINCT s.producto_id) as n
           FROM stock s
           JOIN catalogo c ON c.id = s.producto_id
           WHERE s.cantidad < c.stock_minimo"""
    )["n"]

    caducidades_proximas = bd.consultar_uno(
        """SELECT COUNT(*) as n FROM stock
           WHERE fecha_caducidad IS NOT NULL
           AND CAST(julianday(fecha_caducidad) - julianday('now') AS INTEGER) <= 7
           AND CAST(julianday(fecha_caducidad) - julianday('now') AS INTEGER) >= 0"""
    )["n"]

    ultimo_ticket = bd.consultar_uno(
        """SELECT CAST(julianday('now') - julianday(MAX(fecha)) AS INTEGER) as dias
           FROM tickets"""
    )

    return {
        "productos_en_lista": productos_en_lista,
        "stock_bajo": stock_bajo,
        "caducidades_proximas": caducidades_proximas,
        "ultimo_ticket_dias": ultimo_ticket["dias"] if ultimo_ticket else None,
    }
