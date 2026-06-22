# DeDo — Hoja de ruta

> Estado actual: Fase 1 completada. Fase 2 (tickets y precios) pendiente.
> Última actualización: 2026-06-22
> **Próximo paso concreto:**
> 1. 👤 Ejecutar `docker compose up` en local y verificar que los endpoints responden

### Leyenda

| Icono | Significado |
|-------|-------------|
| 🤖 | Tarea de Claude (código, configuración, documentación) |
| 👤 | Tarea manual (requiere acceso a GitHub, VM, móvil, etc.) |

---

## Fase 0 — Esqueleto del proyecto ✅

Estructura base creada. Completado junio 2026.

- [x] 👤 Crear repositorio `DeDo` en GitHub (`acabellan1868-prog/DeDo`)
- [x] 🤖 Estructura de carpetas (`app/`, `static/`, `data/`)
- [x] 🤖 `app/esquema.sql` — DDL completo (catalogo, stock, lista_compra, tickets, lineas_ticket, historial_precios, menu, menu_productos)
- [x] 🤖 `app/bd.py` — conexión SQLite con context manager
- [x] 🤖 `app/principal.py` — punto de entrada FastAPI (skeleton)
- [x] 🤖 `Dockerfile` + `docker-compose.yml`
- [x] 🤖 `CLAUDE.md` — documentación del ecosistema
- [x] 🤖 `DeDo - analisis.md` — análisis completo del proyecto

---

## Fase 1 — Backend core

CRUD completo de catálogo, stock, lista de la compra y caducidades. La base sobre la que todo lo demás se apoya.

### 1a — Arranque de la app

- [x] 🤖 `app/principal.py`: inicializar BD al arrancar (crear tablas desde `esquema.sql` si no existen)
- [x] 🤖 `app/principal.py`: registrar todos los routers
- [x] 🤖 `app/config.py` — variables de entorno (`DEDO_DB_PATH`, `TZ`, `NTFY_URL`, `NTFY_TOPIC`, `FIDO_API_URL`)

### 1b — Catálogo

- [x] 🤖 `app/rutas/catalogo.py`:
  - `GET /api/catalogo` — listado completo
  - `GET /api/catalogo/{id}` — detalle de un producto
  - `GET /api/catalogo/por-definir` — productos con `estado = 'por_definir'`
  - `POST /api/catalogo` — crear producto
  - `PATCH /api/catalogo/{id}` — editar producto (completar campos, cambiar estado)
  - `DELETE /api/catalogo/{id}` — eliminar producto

### 1c — Stock

- [x] 🤖 `app/rutas/stock.py`:
  - `GET /api/stock` — inventario actual (join con catálogo)
  - `GET /api/stock/{producto_id}` — stock de un producto concreto
  - `POST /api/stock` — añadir entrada de stock (cantidad, lote, fecha_caducidad)
  - `PATCH /api/stock/{id}` — actualizar cantidad o fecha de caducidad
  - `DELETE /api/stock/{id}` — eliminar entrada de stock

### 1d — Lista de la compra

- [x] 🤖 `app/rutas/lista.py`:
  - `GET /api/lista` — lista actual completa
  - `POST /api/lista` — añadir producto (del catálogo o nombre libre)
  - `DELETE /api/lista/{id}` — marcar como comprado / quitar
  - `DELETE /api/lista` — vaciar lista completa

### 1e — Caducidades

- [x] 🤖 `app/rutas/caducidades.py`:
  - `GET /api/caducidades/proximas?dias=7` — productos que caducan en los próximos N días
  - `GET /api/caducidades/vencidas` — productos ya caducados
  - `POST /api/caducidades/{id}` — actualizar fecha de caducidad manualmente

### 1f — Verificación

- [ ] 👤 Ejecutar `docker compose up` en local y verificar que los endpoints responden
- [ ] 👤 Probar con curl o Postman: crear producto en catálogo, añadir stock, añadir a lista

---

## Fase 2 — Tickets y precios

Procesado de tickets de compra: actualiza stock, registra precios históricos y notifica el gasto a FiDo.

### 2a — Procesado de tickets

- [ ] 🤖 `app/rutas/tickets.py`:
  - `POST /api/ticket` — recibe las líneas de un ticket (supermercado, fecha, total, líneas con producto + cantidad + precio)
  - Lógica: para cada línea, busca el producto en catálogo por nombre (fuzzy match básico); si no existe, crea entrada con `estado = 'por_definir'`
  - Actualiza stock (suma cantidad a la entrada existente o crea nueva)
  - Registra precio en `historial_precios`
  - `GET /api/tickets` — historial de tickets procesados
  - `GET /api/tickets/{id}` — detalle de un ticket con sus líneas

### 2b — Historial de precios

- [ ] 🤖 `app/rutas/precios.py`:
  - `GET /api/precios/{producto_id}` — historial de precios de un producto (por supermercado y fecha)
  - `GET /api/precios/comparativa` — coste estimado de la lista actual en cada supermercado (usando últimos precios registrados)

### 2c — Notificación a FiDo

- [ ] 🤖 `app/fido_client.py` — cliente HTTP para llamar a FiDo:
  - `POST {FIDO_API_URL}/api/movimientos` — enviar gasto total al procesar un ticket (importe, comercio, fecha)
  - Manejo de errores: si FiDo no responde, loguear pero no fallar el procesado del ticket

### 2d — Verificación

- [ ] 👤 Probar endpoint `POST /api/ticket` con un ticket de prueba
- [ ] 👤 Verificar que el stock se actualiza y que FiDo recibe el movimiento

---

## Fase 3 — Frontend Cockpit

Dashboard web siguiendo el estilo Cockpit del ecosistema hogarOS. Carga `hogar.css` vía proxy.

### 3a — Estructura HTML

- [ ] 🤖 `static/index.html` — header Cockpit (`ck-header`), navegación con pestañas:
  - **Despensa** — inventario actual con stock y caducidades
  - **Lista** — lista de la compra con acciones (añadir, marcar comprado)
  - **Catálogo** — productos del catálogo (activos + por definir)
  - **Tickets** — historial de tickets procesados
  - **Precios** — comparativa y evolución de precios

### 3b — Estilos

- [ ] 🤖 `static/estilos.css` — estilos propios de DeDo sobre la base de `hogar.css` (clases `dedo-`)

### 3c — JavaScript

- [ ] 🤖 `static/app.js`:
  - Carga dinámica de cada pestaña desde la API
  - Pestaña Despensa: tabla de stock con indicadores visuales (verde/amarillo/rojo según stock mínimo y caducidad)
  - Pestaña Lista: CRUD en tiempo real
  - Pestaña Catálogo: listado + formulario de edición para productos "por definir"
  - Pestaña Tickets: historial con detalle expandible
  - Pestaña Precios: tabla comparativa por supermercado

### 3d — Verificación

- [ ] 👤 Verificar en navegador que las pestañas cargan datos reales
- [ ] 👤 Probar en móvil (diseño responsive)

---

## Fase 4 — Integración hogarOS

Añadir DeDo al ecosistema: proxy nginx, docker-compose y tarjeta en el portal.

- [ ] 🤖 `hogarOS/nginx.conf` — nueva ruta `/despensa/` → `dedo:8080`
- [ ] 🤖 `hogarOS/nginx.conf` — nueva ruta `/despensa/static/` → `portal/static/` (para hogar.css, mismo patrón que ReDo/FiDo)
- [ ] 🤖 `hogarOS/docker-compose.yml` — nuevo servicio `dedo` (puerto 8085:8080, volumen `/mnt/datos/dedo`)
- [ ] 🤖 `hogarOS/.env.example` — añadir variables de DeDo (`DEDO_DB_PATH`, `NTFY_TOPIC`, `FIDO_API_URL`)
- [ ] 🤖 `app/rutas/resumen.py` — endpoint `GET /api/resumen` para la tarjeta del portal:
  ```json
  {
    "productos_en_lista": 8,
    "stock_bajo": 3,
    "caducidades_proximas": 2,
    "ultimo_ticket_dias": 4
  }
  ```
- [ ] 🤖 `hogarOS/portal/index.html` — nueva tarjeta "Despensa" en el bento grid
- [ ] 👤 Crear `/mnt/datos/dedo/` en la VM
- [ ] 👤 Clonar repo DeDo en `/mnt/datos/dedo-build/` en la VM
- [ ] 👤 Ejecutar `actualizar.sh` en la VM
- [ ] 👤 Verificar acceso desde red local: `http://192.168.31.131/despensa/`
- [ ] 👤 Verificar tarjeta en el portal con datos reales

---

## Fase 5 — Rutinas Claude Code

Automatizaciones periódicas que leen imágenes de Google Drive y actualizan DeDo sin intervención manual. Mismo patrón que FiDo.

### 5a — Procesado automático de tickets

- [ ] 🤖 Script `rutinas/procesar_tickets.py`:
  - Lee imágenes nuevas de la carpeta de Drive designada
  - Extrae líneas del ticket con Claude Vision (producto, cantidad, precio unitario, supermercado, fecha)
  - Llama a `POST /despensa/api/ticket` con el resultado
  - Mueve la imagen procesada a subcarpeta `procesados/`
- [ ] 👤 Crear carpeta en Google Drive para tickets de DeDo
- [ ] 👤 Configurar rutina periódica (cron o `/schedule`) para ejecutar cada hora

### 5b — Análisis visual de la despensa

- [ ] 🤖 Script `rutinas/analizar_despensa.py`:
  - Lee fotos de zonas de despensa subidas a Drive
  - Compara contra el catálogo de DeDo (`GET /api/catalogo`)
  - Identifica productos visibles y estima cantidades
  - Genera sugerencias para la lista de la compra
  - Llama a `POST /api/lista` para añadir sugerencias (marcadas como origen "foto")
- [ ] 👤 Crear carpeta en Google Drive para fotos de despensa

### 5c — Avisos de caducidad

- [ ] 🤖 Script `rutinas/revisar_caducidades.py`:
  - Llama a `GET /api/caducidades/proximas?dias=5`
  - Envía avisos escalonados via ntfy:
    - 5 días antes → aviso suave
    - 2 días antes → aviso urgente
    - Día D → aviso crítico
- [ ] 👤 Configurar ejecución diaria (cron o `/schedule`)

### 5d — Informe semanal

- [ ] 🤖 Script `rutinas/informe_semanal.py`:
  - Resumen de la semana: tickets procesados, gasto total, productos añadidos al catálogo
  - Lista de la compra generada automáticamente para la semana siguiente
  - Comparativa de precios si hay datos suficientes
  - Envía resumen via ntfy
- [ ] 👤 Configurar ejecución semanal (lunes 8:00 o similar)

---

## Fase 6 — Módulo menú

Registro del menú diario/semanal como señal de consumo de productos.

- [ ] 🤖 `app/rutas/menu.py`:
  - `POST /api/menu` — registrar menú de un día (fecha, tipo, descripción, productos asociados)
  - `GET /api/menu/semana` — menú de la semana actual
  - `GET /api/menu/semana?offset=-1` — semana anterior
- [ ] 🤖 Lógica de consumo inferido: al registrar un menú, marcar productos asociados como "consumidos esta semana" y añadirlos a la lista si su stock estimado baja del mínimo
- [ ] 🤖 Pestaña "Menú" en el frontend: vista semanal con los 5 tipos de comida por día (desayuno, almuerzo, comida, merienda, cena)
- [ ] 🤖 Script `rutinas/procesar_menu_telegram.py` — interpreta mensajes de texto libre ("hoy he comido lubina al horno") y llama a `POST /api/menu`
- [ ] 👤 Probar registro de menú via Telegram y verificar que actualiza el stock

---

## Fase 7 — Interfaces adicionales

Telegram y voz vía Home Assistant para el día a día.

### 7a — Bot de Telegram

- [ ] 🤖 Script `rutinas/telegram_bot.py` (o integración en hogar-api si es más limpio):
  - Comandos principales: `/lista`, `/despensa`, `/caducidades`
  - Texto libre: "añade X a la lista", "se acabó el aceite", "hoy he comido Y"
  - Respuesta con confirmación o pregunta si el producto es ambiguo
- [ ] 👤 Crear bot en Telegram (BotFather) y obtener token
- [ ] 👤 Añadir `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID` al `.env`

### 7b — Voz via Home Assistant

- [ ] 👤 Crear automatización en HA: comando de voz → webhook → `POST /despensa/api/lista`
- [ ] 👤 Probar: "Oye Google, añade papel higiénico a la lista"

---

## Fase 8 — Aprendizaje y análisis

Cadencias de consumo, predicciones de reposición y comparativa avanzada de precios.

- [ ] 🤖 `app/rutas/analisis.py`:
  - `GET /api/analisis/cadencias` — frecuencia de compra por producto (calculada desde historial de tickets)
  - `GET /api/analisis/prediccion` — lista de productos con fecha estimada de próxima compra
  - `GET /api/analisis/tendencias` — evolución de precios de los productos habituales
- [ ] 🤖 Lógica de lista automática semanal: usar cadencias históricas para pre-generar la lista de la compra de la semana
- [ ] 🤖 Alertas de subida de precio: si un producto sube >15% respecto a su media histórica, aviso via ntfy
- [ ] 👤 Verificar con 2-3 meses de datos reales que las predicciones son razonables

---

## Resumen de dependencias entre fases

```
Fase 0 (esqueleto) ✅
    ↓
Fase 1 (backend core)
    ↓
Fase 2 (tickets + precios)    Fase 3 (frontend)
    ↓                              ↓
Fase 4 (integración hogarOS) ←────┘
    ↓
Fase 5 (rutinas Claude Code)
    ↓
Fase 6 (módulo menú)    Fase 7 (Telegram + voz)
    ↓
Fase 8 (aprendizaje + análisis)
```
