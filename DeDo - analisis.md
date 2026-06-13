# DeDo — Despensa Doméstica
## Análisis del proyecto

> Documento vivo. Se actualiza con cada sesión de trabajo.
> Última actualización: junio 2026

---

## 1. Contexto y motivación

DeDo nace dentro del ecosistema **hogarOS**, un portal doméstico unificado desplegado en Proxmox que agrupa varias aplicaciones especializadas:

| App | Dominio |
|-----|---------|
| **FiDo** | Finanzas domésticas (gastos, ingresos, análisis financiero) |
| **ReDo** | Red doméstica (monitorización de red, Zigbee, dispositivos) |
| **MediDO** | Salud doméstica (servidores, VMs, Docker, Polar Flow) |
| **hogarOS** | Portal y paraguas de todas las aplicaciones |
| **DeDo** | Despensa doméstica ← *este proyecto* |

La motivación concreta: el usuario ya tiene un flujo funcionando en FiDo donde las notificaciones de Google Wallet se capturan como screenshot → se suben a Google Drive → Claude Code las lee cada hora y registra el gasto en FiDo via API. Ese mismo patrón se reutilizará en DeDo.

---

## 2. Qué es DeDo (y qué NO es)

### Es:
- Gestión del inventario de la despensa doméstica
- Generación (semi)automática de la lista de la compra
- Comparativa de precios entre supermercados
- Historial de precios propio basado en tickets reales
- Catálogo vivo de productos del hogar que mejora con el uso
- Registro del menú semanal como fuente de consumo estimado
- Gestión de fechas de caducidad con avisos proactivos

### No es:
- Un gestor de finanzas (eso es FiDo)
- Un gestor de recetas (fuera de scope por ahora)
- Un comparador de precios genérico de internet

### Conexión con FiDo:
Cuando se cierra una compra, DeDo notifica a FiDo el gasto total (importe, comercio, fecha). FiDo no sabe nada de productos ni precios, solo recibe el gasto como haría con cualquier otro movimiento.

---

## 3. Stack técnico

Consistente con el resto de hogarOS y el estilo de trabajo personal:

- **Backend**: Python + FastAPI
- **Base de datos**: SQLite
- **Despliegue**: Docker / Docker Compose en Proxmox (vía Portainer)
- **Automatización**: Claude Code (rutinas periódicas, sin n8n necesario)
- **Almacenamiento intermedio**: Google Drive (carpeta compartida para imágenes)
- **Interfaz principal**: Telegram (bot) + dashboard en Home Assistant
- **Interfaz secundaria**: Voz via Home Assistant (Alexa/Google)
- **Notificaciones**: ntfy (avisos de caducidad y alertas)

---

## 4. Flujo principal de funcionamiento

```
[ENTRADA DE DATOS]
        │
        ├── Foto ticket de compra ──────────────────┐
        │                                           │
        ├── Foto zona de despensa ─────────────────►├──► Google Drive
        │                                           │         │
        ├── Mensaje Telegram ("se acabó el aceite") │         ▼
        │                                           │   Claude Code (rutina)
        ├── Registro de menú del día ───────────────┘         │
        │                                                     ▼
        └── Voz via Home Assistant                  API DeDo (Flask)
                                                         │        │
                                              Actualiza  │        │  Actualiza
                                              despensa   │        │  lista compra
                                                         ▼        ▼
                                                      SQLite ◄────┘
                                                         │
                                                         ▼
                                              [SALIDA / ANÁLISIS]
                                                         │
                                              ├── Notificación Telegram
                                              ├── Aviso ntfy (caducidades)
                                              ├── Dashboard Home Assistant
                                              └── Informe a FiDo (gasto)
```

---

## 5. Fuentes de entrada de datos

### 5.1 Foto de ticket de compra
La más importante. Mismo patrón ya funcionando en FiDo:
- Usuario hace la compra, saca foto del ticket
- La sube manualmente a carpeta de Drive (o automatizado via móvil)
- Claude Code la lee, extrae línea a línea: producto, cantidad, precio unitario, supermercado
- Llama al API de DeDo para actualizar stock y registrar precios
- Si el ticket incluye fecha de caducidad, se extrae y registra
- Llama al API de FiDo para registrar el gasto total

### 5.2 Foto de zona de despensa
Para productos de almacén / limpieza / bebidas:
- Usuario saca foto de un estante (no toda la despensa de golpe, mejor por zonas)
- Claude Code analiza la imagen comparando contra el **catálogo de DeDo**
- Identifica productos, estima cantidad visible
- Genera sugerencias para la lista de la compra
- No requiere reconocimiento "entrenado" — Claude ya reconoce productos con packaging visible

### 5.3 Entrada manual via Telegram
- Texto libre: "se acabó el aceite" / "añade leche a la lista"
- Claude Code interpreta el texto y llama al API correspondiente

### 5.4 Entrada por voz via Home Assistant
- "Oye Google/Alexa, añade papel higiénico a la lista"
- HA captura el comando y llama al endpoint de DeDo

### 5.5 Registro de menú
- Usuario registra lo que ha comido ese día (o planifica el menú de la semana)
- DeDo deduce consumo de ingredientes y actualiza el stock estimado

---

## 6. Generación automática de la lista de la compra

Estrategia híbrida combinando varios métodos:

### Método 1: Stock mínimo
Cada producto tiene un umbral mínimo definido. Cuando el stock registrado baja de ese umbral, se añade automáticamente a la lista.

### Método 2: Frecuencia histórica (aprendizaje pasivo)
Analizando los tickets históricos, Claude Code detecta cadencias de consumo:
- "El aceite aparece cada ~18 días en un ticket"
- "El papel higiénico aparece cada ~10 días"
Con 2-3 meses de uso, DeDo tiene un modelo de consumo real y personal.

### Método 3: Lista base semanal
Una "cesta tipo" de productos que se compran casi siempre. Se genera automáticamente cada semana como punto de partida. El usuario solo gestiona las excepciones.

### Método 4: Análisis visual de la despensa
Foto de zonas concretas → Claude Code detecta qué falta o escasea → sugiere añadir a la lista. Especialmente útil para productos de almacén (limpieza, papel, bebidas, conservas).

### Método 5: Consumo inferido por menú
Si el usuario registra que ha comido lubina al horno, DeDo marca "lubina: consumida" y la añade a la lista aunque no se haya procesado un ticket. Especialmente útil para productos frescos o únicos que no se compran con frecuencia fija.

### Método 6: Entrada libre
Voz o texto en cualquier momento para añadir algo puntual.

---

## 7. El catálogo vivo de productos

Pieza central de DeDo. Un catálogo personalizado de los productos habituales del hogar que mejora con el tiempo de forma orgánica:

### Cómo crece el catálogo:
1. Claude lee un ticket → producto nuevo → crea entrada automáticamente con datos del ticket
2. Claude analiza una foto → producto reconocido con confianza → crea entrada con descripción visual
3. Claude analiza una foto → producto con dudas → crea entrada como **"⚠️ Por definir"**
4. Usuario completa los campos que faltan (tipo de producto, marca)
5. Claude rellena la descripción visual para futuros usos

### Estructura de una entrada del catálogo:
```
nombre:                "Ariel Pods Todo en 1 Frescos"
marca:                 "Ariel"
categoria:             "detergente_lavadora"
descripcion_visual:    "caja rosa/morada con bola de colores, tamaño mediano"
supermercado_habitual: "Mercadona"
stock_actual:          1
stock_minimo:          2
unidad:                "caja"
caducidad_dias_defecto: null  (sin caducidad relevante)
estado:                "activo" | "por_definir"
```

### Ventajas del catálogo vivo:
- El reconocimiento visual mejora con cada foto procesada
- Después de pocos meses, la mayoría de productos habituales están catalogados
- Coste de mantenimiento casi cero — el usuario solo interviene en los "por definir"
- Es personal: no reconoce el mundo entero, reconoce TUS productos

---

## 8. Historial de precios propio

En lugar de depender de scrapers de webs externas (frágiles, con términos de servicio cuestionables), DeDo construye su propio historial de precios a partir de los tickets reales:

- Cada ticket procesado genera registros de precio por producto y supermercado
- Con el tiempo: "la leche en Mercadona ha subido un 12% en 6 meses"
- Comparativa real entre supermercados basada en LO QUE TÚ COMPRAS, no en catálogos genéricos
- Alertas si un producto sube de precio de forma significativa

### Comparativa de supermercados:
Cuando se genera la lista de la compra, DeDo puede calcular el coste estimado de esa lista en los supermercados donde compras habitualmente, usando los últimos precios registrados.

---

## 9. Módulo de menú

El menú actúa como una fuente de **consumo planificado o confirmado**, complementando el stock actualizado por tickets.

### Dos modos de uso:
- **Planificación**: el usuario registra el menú de la semana antes de cocinar → DeDo descuenta ingredientes del stock estimado de forma anticipada
- **Registro a posteriori**: el usuario confirma lo que ha comido → DeDo actualiza el stock

### Qué funciona bien con el menú:
- Productos únicos o poco frecuentes (lubina, salmón, ingredientes especiales)
- Recetas con ingredientes concretos ("paella → arroz, gambas, mejillones, pimiento")
- Productos frescos que no tienen cadencia fija de compra

### Qué funciona peor:
- Productos genéricos de consumo diario (aceite, sal, pan) — se usan en casi todo
- Cantidades exactas — el menú da señales, no mediciones precisas

### Principio de funcionamiento:
No necesita ser preciso al 100% para ser útil. Si se registra "lunes: lubina al horno", DeDo puede marcar "lubina: consumida esta semana" y añadirla a la lista sin saber exactamente cuántas quedaban. Es una señal de consumo, no una medición exacta.

### Registro del menú:
- Via Telegram: "hoy he comido lubina al horno y ensalada"
- Claude extrae los productos relevantes y actualiza el stock estimado
- Entrada manual en el dashboard de HA

---

## 10. Gestión de caducidades

Una de las funcionalidades más valiosas: evitar tirar comida por olvidar las fechas de caducidad.

### Estrategia de fechas por defecto (conservadora)
Cuando no se conoce la fecha exacta de caducidad, se asigna automáticamente según la categoría del producto. Siempre conservadora para reducir el riesgo:

| Categoría | Días por defecto |
|-----------|-----------------|
| Yogur / lácteos frescos | 14 días |
| Leche abierta | 5 días |
| Carne / pescado frescos | 3 días |
| Embutido abierto | 7 días |
| Queso fresco | 7 días |
| Fruta / verdura | 5 días |
| Pan / bollería | 3 días |
| Conservas / enlatados | 730 días (sin aviso urgente) |
| Congelados | 90 días |

### Flujo de caducidades:
1. Producto entra en despensa (via ticket o manual)
2. Si el ticket incluye fecha → se registra directamente
3. Si no → se asigna fecha por defecto según categoría
4. El usuario puede corregirla manualmente cuando ve el envase
5. Con el tiempo: el catálogo aprende las caducidades reales de los productos habituales

### Avisos ntfy escalonados:
```
5 días antes  → aviso suave:   "El yogur Danone caduca el viernes"
2 días antes  → aviso urgente: "⚠️ La lubina caduca mañana"
Día D         → aviso crítico: "🔴 Revisa hoy: yogur, queso fresco"
```

### Endpoints adicionales para caducidades:
```
GET  /api/caducidades/proximas    → productos que caducan en los próximos N días
POST /api/caducidades/{id}        → actualizar fecha de caducidad manualmente
GET  /api/caducidades/vencidas    → productos ya caducados (para revisar y desechar)
```

---

## 11. Webs comparadoras de referencia

Para complementar el historial propio (especialmente al principio, cuando hay pocos datos):

- **preciosdelsuper.es** — analiza diariamente Mercadona, Carrefour, DIA, Alcampo, El Corte Inglés, Consum. Más de 120.000 productos.
- **comparaloo.es** — hasta 37 tiendas en tiempo real, sin registro, independiente
- **preciradar.com** — histórico de precios de Mercadona y Carrefour

No existe API pública oficial de ningún supermercado. Estas webs usan scraping de las tiendas online. A medio plazo, el historial propio de DeDo será más valioso que cualquier comparador genérico.

---

## 12. Infraestructura y automatizaciones

### Rutinas de Claude Code (sin n8n):
El mismo patrón que ya funciona en FiDo — rutinas periódicas que leen imágenes de Google Drive y llaman APIs:

| Rutina | Frecuencia | Qué hace |
|--------|-----------|----------|
| Procesar tickets | Cada hora | Lee fotos nuevas en Drive, extrae datos, actualiza stock y precios |
| Analizar despensa | Semanal / manual | Lee fotos de zonas, compara con catálogo, sugiere lista |
| Análisis de consumo | Semanal | Detecta cadencias, actualiza predicciones de reposición |
| Revisar caducidades | Diaria | Comprueba fechas próximas y lanza avisos ntfy |
| Informe semanal | Semanal | Resumen de la lista, comparativa de precios, tendencias |

### Interfaces de usuario:
- **Telegram**: día a día — añadir productos, registrar menú, consultar lista, recibir alertas
- **ntfy**: avisos de caducidad (push nativo en móvil, sin necesidad de abrir Telegram)
- **Home Assistant dashboard**: panel visual con lista, stock, caducidades próximas, precios
- **Voz (Alexa/Google via HA)**: añadir productos o registrar menú mientras se cocina

---

## 13. API de DeDo (endpoints principales)

```
POST   /api/lista                   → añadir producto a la lista
GET    /api/lista                   → ver lista actual
DELETE /api/lista/{id}              → marcar como comprado / quitar
POST   /api/ticket                  → procesar líneas de ticket (desde Claude Code)
POST   /api/foto-despensa           → procesar análisis visual (desde Claude Code)
GET    /api/stock                   → estado actual del inventario
POST   /api/stock/{producto}        → actualizar stock manualmente
GET    /api/precios/comparativa     → coste estimado lista en cada supermercado
GET    /api/catalogo                → listado de productos del catálogo
PATCH  /api/catalogo/{id}           → completar/editar entrada del catálogo
GET    /api/catalogo/por-definir    → productos pendientes de completar
POST   /api/menu                    → registrar menú del día
GET    /api/menu/semana             → ver menú de la semana actual
GET    /api/caducidades/proximas    → productos que caducan en los próximos N días
POST   /api/caducidades/{id}        → actualizar fecha de caducidad manualmente
GET    /api/caducidades/vencidas    → productos ya caducados
POST   /api/fido/gasto              → enviar gasto de compra a FiDo
```

---

## 14. Decisiones de diseño relevantes

### ¿Por qué no meter la compra en FiDo?
FiDo gestiona lo que **ya se ha gastado** — es histórico y contable. DeDo gestiona lo que **se va a gastar** — es planificación y logística. Son momentos distintos del ciclo doméstico. Mantener la separación permite que cada app tenga un dominio claro y acotado.

### ¿Por qué no n8n?
El patrón imagen → Drive → Claude Code → API ya está probado y funciona muy bien en FiDo. Es más directo, más flexible (acepta cualquier formato de imagen) y no requiere mantener flujos de n8n adicionales.

### ¿Por qué SQLite y no Supabase/PostgreSQL?
Consistencia con el resto del ecosistema hogarOS. Para el volumen de datos de una despensa doméstica, SQLite es más que suficiente y simplifica el despliegue Docker.

### ¿Por qué fotos por zonas y no foto general?
Una foto general de toda la despensa tiene demasiados productos solapados, mal iluminados o tapados. Fotos por zonas concretas (estante limpieza, estante bebidas, nevera puerta) dan mejor resultado con mucho menos ruido.

### ¿Por qué fechas de caducidad conservadoras por defecto?
Es mejor que el sistema avise antes de tiempo (y el usuario descarte el aviso si el producto está bien) que avisar tarde y tirar comida. El coste de un falso positivo es mínimo; el coste de un falso negativo es desperdiciar comida.

### ¿Por qué ntfy para caducidades y no solo Telegram?
ntfy genera notificaciones push nativas en el móvil, sin necesidad de abrir ninguna app. Para algo que requiere acción inmediata como una caducidad, es más intrusivo y efectivo. Ya está integrado en el ecosistema hogarOS (MediDO lo usa).

---

## 15. Preguntas abiertas / pendientes de definir

- [ ] ¿Cómo se gestiona la lista cuando hay varios miembros de la familia? ¿Todos pueden añadir via Telegram?
- [ ] ¿Se integra con el calendario de HA para recordatorios de compra?
- [ ] ¿Alertas de precio cuando algo sube mucho respecto al histórico propio?
- [ ] ¿Exportar la lista para enviarla a la app del supermercado (Mercadona, etc.)?
- [ ] ¿Nivel de detalle del menú? ¿Solo plato principal o también ingredientes concretos?
- [ ] ¿El menú descuenta stock automáticamente o solo sugiere añadir a la lista?
- [ ] ¿Nombre del repo en GitHub? → `DeDo` siguiendo el naming del ecosistema

---

*Documento generado a partir de sesiones de análisis. Continuar refinando antes de pasar al roadmap.md*
