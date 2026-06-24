"""DeDo — Endpoints de procesado de tickets de compra.

Flujo de POST /api/ticket:
  1. Guarda el ticket (supermercado, fecha, total)
  2. Por cada línea: busca el producto en el catálogo (fuzzy match por nombre)
     Si no existe, lo crea con estado='por_definir'
  3. Actualiza el stock (suma cantidad a la entrada existente o crea una nueva)
  4. Registra el precio en historial_precios
  5. Notifica el gasto total a FiDo (sin bloquear si falla)
"""

import logging

from fastapi import APIRouter, HTTPException

from app import bd
from app import fido_client
from app.modelos import (
    TicketRespuesta,
    TicketCrear,
    LineaTicketRespuesta,
)

logger = logging.getLogger("dedo.tickets")
ruta = APIRouter()


# ── Helpers internos ──────────────────────────────────────────────────────────

def _buscar_o_crear_producto(nombre_raw: str) -> int:
    """Busca el producto en el catálogo por nombre (fuzzy).

    Si no existe, crea una entrada con estado='por_definir' y devuelve su id.
    """
    # Intentar coincidencia exacta primero
    producto = bd.consultar_uno(
        "SELECT id FROM catalogo WHERE LOWER(nombre) = LOWER(?)",
        (nombre_raw,),
    )
    if producto:
        return producto["id"]

    # Fuzzy: el nombre del catálogo contiene alguna palabra del ticket
    palabras = [p for p in nombre_raw.split() if len(p) > 3]
    for palabra in palabras:
        producto = bd.consultar_uno(
            "SELECT id FROM catalogo WHERE nombre LIKE ?",
            (f"%{palabra}%",),
        )
        if producto:
            return producto["id"]

    # No encontrado — crear como por_definir
    nuevo_id = bd.ejecutar(
        "INSERT INTO catalogo (nombre, estado) VALUES (?, 'por_definir')",
        (nombre_raw,),
    )
    logger.info("Producto nuevo en catálogo (por_definir): %s [id=%d]", nombre_raw, nuevo_id)
    return nuevo_id


def _actualizar_stock(producto_id: int, cantidad: float, fecha_caducidad: str | None):
    """Suma la cantidad al stock existente del producto, o crea entrada nueva."""
    entrada = bd.consultar_uno(
        "SELECT id, cantidad FROM stock WHERE producto_id = ? ORDER BY id LIMIT 1",
        (producto_id,),
    )
    if entrada:
        bd.ejecutar(
            "UPDATE stock SET cantidad = cantidad + ?, actualizado_en = datetime('now') WHERE id = ?",
            (cantidad, entrada["id"]),
        )
    else:
        bd.ejecutar(
            "INSERT INTO stock (producto_id, cantidad, fecha_caducidad) VALUES (?, ?, ?)",
            (producto_id, cantidad, fecha_caducidad),
        )


def _registrar_precio(producto_id: int, supermercado: str, precio: float, fecha: str, ticket_id: int):
    """Guarda un registro en historial_precios."""
    bd.ejecutar(
        "INSERT INTO historial_precios (producto_id, supermercado, precio, fecha, ticket_id) VALUES (?, ?, ?, ?, ?)",
        (producto_id, supermercado, precio, fecha, ticket_id),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@ruta.post("", response_model=TicketRespuesta, status_code=201)
def procesar_ticket(datos: TicketCrear):
    """Procesa un ticket de compra completo.

    Actualiza stock e historial de precios por cada línea,
    y notifica el gasto total a FiDo.
    """
    if not datos.lineas:
        raise HTTPException(400, "El ticket no contiene líneas")

    # 1. Guardar cabecera del ticket
    ticket_id = bd.ejecutar(
        "INSERT INTO tickets (supermercado, fecha, total, fichero_origen) VALUES (?, ?, ?, ?)",
        (datos.supermercado, datos.fecha, datos.total, datos.fichero_origen),
    )
    logger.info("Ticket #%d creado: %s %s %.2f€", ticket_id, datos.supermercado, datos.fecha, datos.total or 0)

    # 2-4. Procesar cada línea
    for linea in datos.lineas:
        producto_id = _buscar_o_crear_producto(linea.nombre_raw)

        bd.ejecutar(
            """INSERT INTO lineas_ticket
               (ticket_id, producto_id, nombre_raw, cantidad, precio_unitario, precio_total)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ticket_id, producto_id, linea.nombre_raw, linea.cantidad,
             linea.precio_unitario, linea.precio_total),
        )

        if linea.cantidad:
            _actualizar_stock(producto_id, linea.cantidad, linea.fecha_caducidad)

        if linea.precio_unitario and datos.supermercado and datos.fecha:
            _registrar_precio(producto_id, datos.supermercado, linea.precio_unitario, datos.fecha, ticket_id)

    # 5. Notificar a FiDo (no bloquea si falla)
    if datos.total and datos.supermercado and datos.fecha:
        fido_client.notificar_gasto(datos.total, datos.supermercado, datos.fecha)

    return _ticket_con_lineas(ticket_id)


@ruta.get("", response_model=list[TicketRespuesta])
def listar_tickets():
    """Devuelve el historial de tickets procesados, del más reciente al más antiguo."""
    tickets = bd.consultar_todos(
        "SELECT * FROM tickets ORDER BY procesado_en DESC"
    )
    return [_ticket_con_lineas(t["id"]) for t in tickets]


@ruta.get("/{ticket_id}", response_model=TicketRespuesta)
def obtener_ticket(ticket_id: int):
    """Devuelve un ticket con todas sus líneas."""
    ticket = bd.consultar_uno("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not ticket:
        raise HTTPException(404, "Ticket no encontrado")
    return _ticket_con_lineas(ticket_id)


def _ticket_con_lineas(ticket_id: int) -> dict:
    """Devuelve un ticket enriquecido con sus líneas y nombre de producto."""
    ticket = bd.consultar_uno("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    lineas = bd.consultar_todos(
        """SELECT lt.*, c.nombre as nombre_producto
           FROM lineas_ticket lt
           LEFT JOIN catalogo c ON c.id = lt.producto_id
           WHERE lt.ticket_id = ?
           ORDER BY lt.id""",
        (ticket_id,),
    )
    return {**ticket, "lineas": lineas}
