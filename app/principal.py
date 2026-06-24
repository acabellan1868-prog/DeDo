"""Punto de entrada de DeDo — Despensa Doméstica."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.bd import inicializar_bd
from app.rutas import catalogo, stock, lista, caducidades, resumen, tickets, precios

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("dedo")


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    """Al arrancar: crea el directorio de datos e inicializa la BD."""
    os.makedirs("data", exist_ok=True)
    inicializar_bd()
    logger.info("DeDo arrancado — BD inicializada")
    yield
    logger.info("DeDo detenido")


app = FastAPI(
    title="DeDo — Despensa Doméstica",
    description="Gestión de inventario, lista de la compra y caducidades",
    version="1.0.0",
    lifespan=ciclo_vida,
)

# ---- Registrar rutas API ----
app.include_router(resumen.ruta,      prefix="/api/resumen",      tags=["Resumen"])
app.include_router(catalogo.ruta,     prefix="/api/catalogo",     tags=["Catálogo"])
app.include_router(stock.ruta,        prefix="/api/stock",        tags=["Stock"])
app.include_router(lista.ruta,        prefix="/api/lista",        tags=["Lista"])
app.include_router(caducidades.ruta,  prefix="/api/caducidades",  tags=["Caducidades"])
app.include_router(tickets.ruta,      prefix="/api/tickets",      tags=["Tickets"])
app.include_router(precios.ruta,      prefix="/api/precios",      tags=["Precios"])

# ---- Servir frontend estático (debe ir al final) ----
@app.get("/")
def raiz():
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")
