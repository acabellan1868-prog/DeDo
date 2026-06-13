# DeDo — Despensa Doméstica

Aplicación del ecosistema **hogarOS** para gestión del inventario de la despensa, lista de la compra automática, comparativa de precios y control de caducidades.

## Parte de hogarOS

| App | Dominio |
|-----|---------|
| hogarOS | Portal y paraguas |
| FiDo | Finanzas domésticas |
| ReDo | Red doméstica |
| MediDo | Salud doméstica |
| **DeDo** | Despensa doméstica ← este proyecto |

## Stack

- **Backend**: Python + FastAPI
- **Base de datos**: SQLite
- **Despliegue**: Docker / Docker Compose en Proxmox
- **Automatización**: Claude Code (rutinas periódicas)
- **Notificaciones**: ntfy

## Despliegue

```bash
docker compose up -d
```

La API queda accesible en `http://localhost:8085` y bajo el proxy Nginx en `/despensa/`.
