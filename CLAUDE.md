# CLAUDE.md — DeDo

## Qué es
Gestión de la despensa doméstica: inventario, lista de la compra automática, historial de precios por ticket y control de caducidades.

- **Repo:** acabellan1868-prog/DeDo
- **Local:** `Desarrollo/DeDo/`
- **Puerto host:** 8085 → contenedor 8080
- **Proxy:** `/despensa/` → `dedo:8080`

## Estructura

```
DeDo/
├── app/
│   ├── principal.py       ← punto de entrada FastAPI
│   ├── bd.py              ← conexión SQLite
│   ├── esquema.sql        ← DDL de la base de datos
│   └── rutas/             ← endpoints por dominio
├── static/
│   ├── index.html
│   ├── app.js
│   └── estilos.css
├── data/                  ← SQLite (ignorado por git)
├── Dockerfile
└── docker-compose.yml
```

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `DEDO_DB_PATH` | Ruta BD SQLite (defecto `data/dedo.db`) |
| `TZ` | Zona horaria (`Europe/Madrid`) |
| `NTFY_URL` | URL base del servidor NTFY |
| `NTFY_TOPIC` | Topic para notificaciones de caducidad |
| `FIDO_API_URL` | URL base de FiDo para notificar gastos de compra |

## Conexión con FiDo
Cuando se cierra una compra (ticket procesado), DeDo llama a `POST {FIDO_API_URL}/movimientos` con el importe total, comercio y fecha. FiDo no recibe información de productos.
