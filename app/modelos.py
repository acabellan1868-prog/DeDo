"""Modelos Pydantic de DeDo — esquemas de entrada y salida de la API."""

from pydantic import BaseModel
from typing import Optional


# ============================================================
# Catálogo
# ============================================================

class ProductoRespuesta(BaseModel):
    id: int
    nombre: str
    marca: Optional[str] = None
    categoria: Optional[str] = None
    descripcion_visual: Optional[str] = None
    supermercado_habitual: Optional[str] = None
    stock_minimo: float = 1
    unidad: str = "unidad"
    caducidad_dias_defecto: Optional[int] = None
    estado: str = "activo"
    creado_en: Optional[str] = None


class ProductoCrear(BaseModel):
    nombre: str
    marca: Optional[str] = None
    categoria: Optional[str] = None
    descripcion_visual: Optional[str] = None
    supermercado_habitual: Optional[str] = None
    stock_minimo: float = 1
    unidad: str = "unidad"
    caducidad_dias_defecto: Optional[int] = None
    estado: str = "activo"


class ProductoActualizar(BaseModel):
    nombre: Optional[str] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    descripcion_visual: Optional[str] = None
    supermercado_habitual: Optional[str] = None
    stock_minimo: Optional[float] = None
    unidad: Optional[str] = None
    caducidad_dias_defecto: Optional[int] = None
    estado: Optional[str] = None


# ============================================================
# Stock
# ============================================================

class StockRespuesta(BaseModel):
    id: int
    producto_id: int
    nombre_producto: Optional[str] = None
    cantidad: float = 0
    fecha_caducidad: Optional[str] = None
    lote: Optional[str] = None
    actualizado_en: Optional[str] = None


class StockCrear(BaseModel):
    producto_id: int
    cantidad: float = 1
    fecha_caducidad: Optional[str] = None
    lote: Optional[str] = None


class StockActualizar(BaseModel):
    cantidad: Optional[float] = None
    fecha_caducidad: Optional[str] = None
    lote: Optional[str] = None


# ============================================================
# Lista de la compra
# ============================================================

class ItemListaRespuesta(BaseModel):
    id: int
    producto_id: Optional[int] = None
    nombre_producto: Optional[str] = None
    nombre_libre: Optional[str] = None
    cantidad: float = 1
    unidad: Optional[str] = None
    motivo: Optional[str] = None
    creado_en: Optional[str] = None


class ItemListaCrear(BaseModel):
    producto_id: Optional[int] = None
    nombre_libre: Optional[str] = None
    cantidad: float = 1
    unidad: Optional[str] = None
    motivo: Optional[str] = None


# ============================================================
# Caducidades
# ============================================================

class CaducidadRespuesta(BaseModel):
    id: int
    producto_id: int
    nombre_producto: Optional[str] = None
    cantidad: float
    fecha_caducidad: str
    dias_restantes: int


class CaducidadActualizar(BaseModel):
    fecha_caducidad: str


# ============================================================
# Tickets
# ============================================================

class LineaTicketCrear(BaseModel):
    nombre_raw: str
    cantidad: Optional[float] = None
    precio_unitario: Optional[float] = None
    precio_total: Optional[float] = None
    fecha_caducidad: Optional[str] = None


class LineaTicketRespuesta(BaseModel):
    id: int
    ticket_id: int
    producto_id: Optional[int] = None
    nombre_producto: Optional[str] = None
    nombre_raw: str
    cantidad: Optional[float] = None
    precio_unitario: Optional[float] = None
    precio_total: Optional[float] = None


class TicketCrear(BaseModel):
    supermercado: Optional[str] = None
    fecha: Optional[str] = None
    total: Optional[float] = None
    fichero_origen: Optional[str] = None
    lineas: list[LineaTicketCrear] = []


class TicketRespuesta(BaseModel):
    id: int
    supermercado: Optional[str] = None
    fecha: Optional[str] = None
    total: Optional[float] = None
    fichero_origen: Optional[str] = None
    procesado_en: Optional[str] = None
    lineas: list[LineaTicketRespuesta] = []


# ============================================================
# Precios
# ============================================================

class PrecioRespuesta(BaseModel):
    id: int
    producto_id: int
    nombre_producto: Optional[str] = None
    supermercado: Optional[str] = None
    precio: float
    fecha: Optional[str] = None
    ticket_id: Optional[int] = None


class DetalleComparativa(BaseModel):
    producto_id: int
    nombre_producto: Optional[str] = None
    precio: float


class ComparativaRespuesta(BaseModel):
    supermercado: str
    total_estimado: float
    productos_con_precio: int
    detalle: list[DetalleComparativa] = []


# ============================================================
# Resumen (para tarjeta del portal hogarOS)
# ============================================================

class ResumenRespuesta(BaseModel):
    productos_en_lista: int
    stock_bajo: int
    caducidades_proximas: int
    ultimo_ticket_dias: Optional[int] = None
