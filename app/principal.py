"""Punto de entrada de DeDo — Despensa Doméstica."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="DeDo", description="Despensa Doméstica")

app.mount("/static", StaticFiles(directory="static"), name="static")
