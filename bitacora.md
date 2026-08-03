# Bitácora — DeDo

## 2026-08-03 — Rutina de Cowork: falso negativo por almacén regional, fix wh=svq1 y verificación

### Contexto
Primera ejecución real de la rutina de Cowork `rutinas/prompt_capturar_producto.md`
(creada el día anterior), montada por el usuario como rutina local sin
temporización, para capturar productos en estado `por_capturar`.

### Creación de la rutina en Cowork: botón "Crear" desactivado
Al montar la rutina en la interfaz de Cowork, el botón "Crear" permanecía
desactivado. Causa: el campo "Seleccionar carpeta" (obligatorio en una rutina
local, para saber en qué directorio ejecutarse) estaba vacío. Solucionado
seleccionando la carpeta del repo (`Desarrollo/Claude/DeDo`) y dejando
"Worktree" sin marcar, ya que la rutina solo hace llamadas HTTP y no necesita
una copia aislada del código.

### Primer caso real: "Gazpacho fresco" (id 11) — falso negativo
La rutina procesó el producto #11 (ticket 5, línea 11, precio real 1,55 €):
buscó en la categoría "Gazpacho y cremas" de Mercadona, encontró candidatos
Hacendado a 2,65 € y 1,10 €, ninguno coincidía con 1,55 € → aplicó
correctamente la regla de "no adivinar" y dejó el producto sin tocar.

Verificación manual (no solo confiar en el informe de la rutina): se revisó
toda la categoría (20 productos) y ninguno costaba 1,55 € — parecía confirmar
que no había coincidencia real, no solo un fallo de búsqueda.

### La corrección del usuario destapa el problema de fondo
El usuario indicó que el producto real no es de Hacendado sino de **García
Millán**, y aportó la URL directa (`tienda.mercadona.es/product/39968/...`).
Esto reveló que el diagnóstico de "no existe" era un **falso negativo**:

- La API pública de Mercadona **regionaliza el catálogo por almacén** (`wh`),
  asociado al código postal del usuario. Sin `wh` explícito, la API usa un
  almacén genérico que no tiene el surtido de marcas regionales (García
  Millán es una marca de gazpacho "Receta Andaluza").
- El endpoint completo (`/api/products/{id}/`) daba 404 para ese producto sin
  el almacén correcto, pero el endpoint ligero de previsualización
  (`/api/products/{id}/preview/?lang=es`) sí funcionó independientemente del
  almacén — de ahí se pudo sacar al menos la foto para la descripción visual.
- Navegando la web real de Mercadona e introduciendo el CP 41001 (Sevilla,
  por la pista "Receta Andaluza" de la etiqueta) se resolvió `wh=svq1`. Al
  repetir la consulta de categoría con ese parámetro, "Gazpacho fresco García
  Millán" apareció con precio exacto: **1,55 €, 0,33 L** — coincidencia
  perfecta con el ticket.
- Importante: la categoría **no filtra por marca** — ya incluía otras marcas
  de terceros como "Starlux" en la misma lista. El problema era puramente el
  almacén regional por defecto, no una limitación de cobertura de marcas.

Producto #11 actualizado vía `PATCH`: marca "García Millán", zona
`frigorifico`, `caducidad_dias_defecto: 20` (estimación, dato real no
disponible), descripción visual a partir de la foto de la ficha web, estado
`activo`.

### Fix aplicado al prompt de la rutina
`rutinas/prompt_capturar_producto.md` actualizado para fijar `?wh=svq1` en
las tres llamadas a la API de Mercadona (árbol de categorías, productos de
categoría, detalle de producto), con nota explicando el motivo y con el
endpoint `preview` documentado como vía alternativa si el detalle completo
sigue dando 404. Documentado también el caso del gazpacho en la sección de
aprendizajes, para que la rutina no reporte "no existe" como si fuera
definitivo cuando puede ser solo almacén equivocado.

### Verificación del almacén para el código postal real del usuario
`wh=svq1` se había confirmado solo para el CP de prueba 41001 (Sevilla
capital), no para el CP real del usuario. Los intentos de forzar el cambio de
código postal por API sin la sesión real del navegador no dieron resultados
fiables (endpoint `PUT /api/postal-codes/actions/change-pc/` devolvía
`warehouse_changed: false` incluso para códigos postales que deberían haber
cambiado el almacén). El usuario verificó directamente en su propio navegador
la cookie `__mo_da` de tienda.mercadona.es: `{"warehouse":"svq1",
"postalCode":"21100"}` — confirma que `svq1` es también el almacén correcto
para su zona real (Huelva provincia).

### Estado final de la sesión
- Rutina de Cowork creada, con el fix de almacén aplicado y verificado contra
  el código postal real del usuario.
- Producto #11 (Gazpacho fresco García Millán) capturado y activo.
- El usuario confirma que, tras estos cambios, la ejecución manual de la
  rutina "funciona" — seguirá probando manualmente con más productos antes de
  añadir temporización/programación.
- Commits en el repo DeDo: `747163c`, `9ebcad4`, `d0fbe8e`, `e8fc630`.

### Próximo paso concreto
1. 👤 Marcar más productos como `por_capturar` y seguir ejecutando la rutina
   manualmente para validar el patrón con más casos (especialmente si
   aparece otro empate de precio o otro almacén regional).
2. 👤/🤖 Cuando haya confianza suficiente tras varias ejecuciones limpias,
   decidir frecuencia y activar la temporización de la rutina en Cowork.

---

## 2026-08-02 — Captura manual de 3 productos por_capturar y prompt inicial de Cowork

### Contexto
Antes de diseñar la automatización de Cowork, se decidió capturar a mano unos
cuantos productos en estado `por_capturar` para aprender el proceso real y
afinarlo, en vez de adivinar el diseño de la rutina de antemano.

### Método usado
1. Listar pendientes: `GET /despensa/api/catalogo/por-capturar`.
2. Para cada producto, localizar la categoría de Mercadona más probable
   navegando el árbol `GET /api/categories/` (no existe búsqueda por texto
   libre útil en la API pública).
3. **El precio real del ticket es el desambiguador principal**: cuando varios
   productos de Mercadona comparten nombre pero difieren en formato/precio,
   se cruza contra `price_instructions.unit_price` de cada candidato.
4. Descargar la foto del candidato confirmado a un directorio temporal de la
   sesión (nunca persistente) y redactar `descripcion_visual` a mano,
   siguiendo el criterio de `DeDo - analisis.md` sección 7b.
5. Asignar `zona` y `caducidad_dias_defecto` con criterio propio (no vienen
   de la API de Mercadona).
6. `PATCH /api/catalogo/{id}` con los datos y `estado: "activo"`.

### Productos capturados
- **#15 — Aceitunas rellenas de anchoa pack-3**: 4 productos de Mercadona con
  el mismo nombre y distinto formato; solo uno coincidía exacto con el precio
  del ticket (1,80 €) → Hacendado, zona alacena, caducidad 730 días.
- **#2 — Chocolate para fundir sin azúcar 70%**: un único candidato, precio
  exacto (3,25 €) → Hacendado, zona alacena, caducidad 365 días (estimación).
- **#6 — Almendra frita**: **empate de precio** entre dos productos distintos
  a 2,95 € (bolsa "pelada" 200g vs "marcona" 125g) — no hay forma de resolver
  solo con datos. Se preguntó al usuario, confirmó la "pelada" 200g. De aquí
  nace la regla dura de "no adivinar ante empates" para la rutina automática,
  ya que una tarea programada no puede parar a preguntar.

### Tiempos medidos
- Caso limpio (chocolate): ~1 min 24 s.
- Caso con empate (almendra): ~2 min 04 s de reloj total, pero incluye la
  espera de la respuesta del usuario — no comparable a una ejecución
  desatendida.

### Prompt inicial de Cowork
Creado `rutinas/prompt_capturar_producto.md`: nombre, descripción, frecuencia
recomendada (manual/bajo demanda hasta validar más casos), instrucciones
completas del proceso, reglas duras (no inventar datos sin candidato
confirmado por precio, no cambiar a `activo` sin verificación, no dejar
ficheros temporales) y sección de aprendizajes/riesgos a validar.

### Estado final de la sesión
- 3 productos `por_capturar` capturados y activos (#15, #2, #6).
- Prompt de la rutina documentado y subido al repo, listo para probarse
  dentro de Cowork.

### Commits de esta sesión
- `747163c` — prompt inicial de la rutina de Cowork
- `9ebcad4` — descripción corta de la tarea (para el formulario de Cowork)

### Próximo paso concreto
1. 👤 Crear la rutina en la interfaz de Cowork con el contenido del prompt.
2. 👤 Marcar algún producto más como `por_capturar` y ejecutar la rutina
   manualmente para ver qué pasa.

---

## 2026-08-01 (continuación) — Incidente de datos, fix de claves foráneas, ticket real procesado con éxito y pestaña Tickets

### Contexto
Continuación directa de la sesión anterior (mismo día). Tras desplegar `por_capturar`
(commit `09302f5`) con `actualizar.sh`, se detectó un problema grave de datos.

### Incidente: base de datos vaciada tras el despliegue
Al comprobar el catálogo tras el despliegue, `GET /api/catalogo`, `/api/stock` y
`/api/tickets` devolvían todos `[]`. El stock y los tickets vacíos eran intencionados
(se habían borrado a mano en la sesión anterior para deshacer el ticket de prueba),
pero el **catálogo con los 40 productos de Mercadona había desaparecido**, sin que
nadie lo borrara explícitamente.

**Causa raíz identificada:** la migración `_migrar_estado_por_capturar()` (añadida en
`09302f5`) reconstruye la tabla `catalogo` con `ALTER TABLE catalogo RENAME TO
catalogo_old` → `CREATE TABLE catalogo (...)` → `INSERT ... SELECT ... FROM
catalogo_old` → `DROP TABLE catalogo_old`. Desde SQLite 3.25, **renombrar una tabla
reescribe automáticamente las referencias de clave foránea de las demás tablas que
apuntan a ella** (para no romperlas) — así que `stock`, `lista_compra`,
`lineas_ticket`, `historial_precios` y `menu_productos` pasaron a apuntar a
`catalogo_old`. Al borrar esa tabla, quedaron con una FK colgando de un nombre
inexistente. Cualquier `INSERT` que dependiera de esa FK (stock, lista, líneas de
ticket, histórico de precios) empezó a fallar con 500 en bruto — confirmado
probando `POST /api/stock` y `POST /api/lista` directamente, sin pasar por tickets.

Adicionalmente, la migración usaba un `BEGIN` explícito sobre una conexión con el
`isolation_level` por defecto de Python — que **comete implícitamente cualquier
transacción abierta justo antes de una sentencia DDL** (`CREATE`/`ALTER`/`DROP`),
así que la "transacción atómica" nunca lo fue realmente: cada sentencia DDL se
autocometía por separado. Esto probablemente contribuyó a que el catálogo acabase
vacío si algo falló a mitad de la secuencia.

### Fix aplicado (commit `ad9b525`)
- **`_conexion_para_migracion()`**: nueva conexión con `isolation_level=None`, que
  desactiva la gestión implícita de transacciones de Python. Con esto, `BEGIN` /
  `COMMIT` / `ROLLBACK` explícitos controlan de verdad toda la secuencia de
  sentencias DDL como una unidad atómica real.
- **`_reparar_fk_catalogo()`**: nueva función que detecta qué tablas tienen la FK
  rota (`"REFERENCES catalogo(id)"` ausente de su definición) y las reconstruye
  (rename → create con la definición correcta → copiar datos → drop), todo con
  `PRAGMA foreign_keys = OFF` durante la operación y `PRAGMA foreign_key_check`
  antes de confirmar, siguiendo el procedimiento oficial que documenta SQLite para
  este tipo de cambios de esquema.
- Ambas migraciones (`_migrar_estado_por_capturar` y `_reparar_fk_catalogo`) se
  ejecutan siempre al arrancar (`inicializar_bd()`), son idempotentes (comprueban
  el estado actual antes de actuar).

**Verificado tras desplegar:** `POST /api/stock` y `POST /api/lista` ya devuelven
201 correctamente. Los 25 productos que ya se habían creado como prueba antes del
fix sobrevivieron intactos.

Nota importante para el usuario/futuras sesiones: como se acordó explícitamente,
esto ocurrió en fase de desarrollo sin datos reales en juego — no se considera un
incidente grave, pero deja como aprendizaje que las reconstrucciones de tablas en
SQLite necesitan `PRAGMA foreign_keys = OFF` + verificación `foreign_key_check`
+ revisar también las tablas dependientes, no solo la tabla que se modifica.

### Ticket real procesado con éxito: producto_id explícito funciona
Con la base de datos reparada, se reprocesó `ticket_20260801-1411.pdf` (Mercadona,
tienda física, 01/08/2026, 54,01 €, 25 líneas) — el ticket que esperaba en
`Drive/DeDo/Tickets/`. Como el catálogo estaba vacío, se crearon los 25 productos
uno a uno (`POST /api/catalogo`, solo nombre legible + categoría básica, sin buscar
en la API de Mercadona — según el criterio acordado de rapidez para los primeros
tickets), y se envió el ticket con `producto_id` explícito en cada línea.

**Resultado: las 25 líneas casaron exactamente 1:1 con su producto**, sin ninguna
mezcla — a diferencia del primer intento (sesión anterior) donde el fuzzy-match
automático mezcló cantidades entre productos no relacionados. Confirma que la
solución de `producto_id` explícito (commit `708ea25`) resuelve el problema de raíz.

- Ticket creado: **id 5**
- Stock: 25 entradas nuevas, cantidades correctas (incluyendo `Tomate canario` con
  0,598 kg, un producto por peso)
- Catálogo: 25 productos nuevos con estado `por_definir`, candidatos para el flujo
  de "Capturar producto" cuando se decida cuáles enriquecer

### Pestaña Tickets: de placeholder a funcional (commit `6f8adf8`)
La pestaña Tickets solo mostraba "Procesado de tickets — disponible en la Fase 2",
pese a que el backend (`GET /api/tickets`, `GET /api/tickets/{id}`, `DELETE
/api/tickets/{id}`) llevaba tiempo listo. Añadido:
- Listado de tickets (supermercado, fecha, total, nº de líneas)
- Tarjeta expandible al hacer clic — muestra las líneas (producto, cantidad, precio)
- Botón "✕" por ticket que llama al `DELETE /api/tickets/{id}` ya existente
  (revierte stock, borra histórico de precios y líneas)
- Eliminado el CSS `.dedo-proximamente`, que quedó huérfano

### Estado final de la sesión
- **Base de datos reparada y funcionando**: catálogo, stock, lista y tickets
  aceptan inserciones correctamente.
- **Catálogo**: 25 productos reales del ticket #5, todos `por_definir`, sin
  descripción visual ni zona (no se enriquecieron, según lo acordado).
- **Despensa**: 25 entradas de stock reales.
- **Ticket #5**: procesado y visible por API; pendiente de verificar visualmente
  en la nueva pestaña Tickets (código pusheado, falta `actualizar.sh`).
- **Drive `DeDo/Tickets/`**: el ticket ya procesado (`ticket_20260801-1411.pdf`)
  sigue en la carpeta — no hay lógica de mover a "procesados" todavía (eso es
  parte del diseño de la futura tarea de Cowork, no implementado aún).

### Commits de esta sesión (continuación del mismo día)
- `ad9b525` — fix de FK colgadas + migraciones atómicas de verdad
- `6f8adf8` — pestaña Tickets funcional

### Próximo paso concreto
1. 👤 Ejecutar `actualizar.sh` en la VM para desplegar la pestaña Tickets
   (commit `6f8adf8`)
2. 👤 Verificar visualmente que el ticket #5 aparece en la pestaña Tickets, con
   sus 25 líneas correctas al expandir
3. 👤 Decidir qué hacer con los 25 productos `por_definir` del ticket #5: dejarlos,
   o empezar a probar el botón "Capturar producto" con alguno
4. 🤖/👤 Diseñar y montar la tarea programada de Cowork para automatizar la
   lectura de tickets de `Drive/DeDo/Tickets/` (pendiente desde antes, sin empezar)
5. 👤 Aportar el stock real completo de la despensa (más allá de lo que ya
   aportó este ticket) cuando se quiera dejar de estar en modo prueba

---

## 2026-07-30/08-01 — CRUD de catálogo, ticket real de prueba, producto_id explícito y estado por_capturar

### Contexto
Continuación de la sesión anterior. El campo `zona` ya desplegado. Objetivo: probar el
flujo real de tickets (Fase 2d, pendiente desde el despliegue inicial) y dejar el
catálogo editable desde la interfaz.

### Catálogo: CRUD completo en el frontend
La pestaña Catálogo era solo de lectura pese a que el API ya soportaba
`POST`/`PATCH`/`DELETE`. Añadido formulario de alta/edición (reutiliza los campos
del modelo, incluido `zona`) y botón de borrado por tarjeta.
Commit `2411a96`.

### Ticket real de prueba: el fuzzy-match rompe el stock
Se procesó `ticket-727798.pdf` (pedido online Mercadona, 33 líneas, 159,51 €) contra
`POST /api/tickets`. El fuzzy-match de `_buscar_o_crear_producto()` (primera palabra
de >3 letras que aparezca en cualquier nombre del catálogo, sin puntuar relevancia)
emparejó casi todo mal: p.ej. "Leche entera Hacendado", "Golosinas...", "Vinagre...",
"Macarrón..." acabaron todos sumados al stock de "Arroz redondo Hacendado" solo por
compartir la palabra "Hacendado". Se vació el stock manualmente (13 entradas borradas
vía `DELETE /api/stock/{id}`, uno a uno — no hay borrado masivo) para partir de cero.

### Bugs encontrados y arreglados en cascada
1. **Sin endpoint para deshacer tickets**: `rutas/tickets.py` solo tenía GET/POST.
   Añadido `DELETE /api/tickets/{id}` que revierte el stock sumado, borra
   `historial_precios` y `lineas_ticket`, y el propio ticket. Commit `1c1fb29`.
2. **Borrar un producto referenciado daba 500 en bruto**: `eliminar_producto()` no
   capturaba el `IntegrityError` de clave foránea (producto con stock/tickets/histórico
   asociado). Ahora devuelve 409 con mensaje claro. Mismo commit `1c1fb29`.
3. **Conexiones SQLite sin cerrar en error**: `consultar_todos`/`consultar_uno`/`ejecutar`
   en `bd.py` no cerraban la conexión si saltaba una excepción a mitad. Con varios
   `IntegrityError` seguidos (por las pruebas de borrado) se acumularon conexiones
   abiertas y, en modo WAL, provocaron bloqueos intermitentes ("database is locked")
   que no eran `IntegrityError` y por tanto no se capturaban — el mismo borrado a veces
   daba 409 correcto y a veces 500 real. Arreglado con `try/finally`. Commit `65b3312`.
4. **Mensaje de error genérico en el frontend**: `del()` ahora propaga el campo
   `detail` de la respuesta en vez de un "Error al borrar" sin contexto. Commit `97f5b63`.

Tras estos cuatro fixes y borrar el ticket #1 de prueba, el catálogo quedó
completamente editable/borrable sin errores.

### producto_id explícito por línea de ticket
Se detectó que ni el ticket físico ni el pedido online traen ningún identificador
único de producto (ni EAN ni SKU) — solo nombre en texto libre, que además varía
entre el nombre abreviado de TPV en tienda física y el nombre completo del pedido
online. El fuzzy-match automático nunca va a ser fiable con esta entrada.

Solución: `LineaTicketCrear` admite ahora `producto_id` opcional. Si se informa
(porque quien construye el ticket — hoy yo a mano, en el futuro una tarea
automática de Cowork — ya ha comparado el ticket contra el catálogo real con
criterio), se usa directamente sin pasar por el fuzzy-match, validando que exista.
Si no se informa, sigue el comportamiento de siempre (exacto → fuzzy → `por_definir`).
Commit `708ea25`.

### Nueva carpeta de Drive para DeDo
El usuario creó `DeDo/` en Drive (separado de la carpeta de FiDo), con subcarpeta
`Tickets/`. Ya contiene un ticket real nuevo sin procesar: `ticket_20260801-1411.pdf`
(Mercadona, tienda física, 01/08/2026, 54,01 €).

### Diseño acordado para productos nuevos al procesar un ticket
Para no ralentizar el procesado (sobre todo en los primeros tickets, donde casi
todo es nuevo), los productos que no existen en el catálogo se crean con solo lo
esencial (nombre legible, categoría básica si es obvia) — nada de buscar en la API
del supermercado ni generar `descripcion_visual` en el momento.

Para el enriquecimiento se añade un **tercer estado: `por_capturar`**, distinto de
`por_definir`:
- Todo producto nuevo entra como `por_definir` (como siempre).
- El usuario decide, uno a uno, cuáles quiere enriquecer ya, pulsando **"Capturar
  producto"** en la tarjeta — pasa a `por_capturar`.
- Solo los `por_capturar` se procesan (yo busco en la API del supermercado y
  relleno los datos vía `PATCH`) — al principio bajo demanda, más adelante quizá
  con una tarea programada.
- Esto permite probar todo el sistema de forma incremental (uno, tres productos...)
  sin comprometerse a procesar todo el catálogo de golpe ni tener que deshacer nada.

Implementado: migración de `esquema.sql`/`bd.py` (reconstruye la tabla `catalogo`
porque SQLite no permite modificar un `CHECK` con `ALTER TABLE`), endpoint
`GET /api/catalogo/por-capturar`, badge de las tres etiquetas reales, botón
"Capturar producto", indicador "⏳ En cola de captura" y filtro nuevo en la
toolbar. Commit `09302f5`.

### Estado final de la sesión
- Catálogo: CRUD completo funcionando en producción (crear/editar/borrar).
- Ticket de prueba #1 deshecho, stock vacío de nuevo.
- `producto_id` explícito disponible para futuros tickets — pendiente de desplegar
  y de reprocesar el ticket online con emparejamiento correcto.
- Estado `por_capturar` implementado — pendiente de desplegar.
- Ticket real nuevo esperando en Drive (`ticket_20260801-1411.pdf`), sin procesar.

### Próximo paso concreto
1. 👤 Ejecutar `actualizar.sh` en la VM (despliega `producto_id` explícito y `por_capturar`)
2. 🤖 Procesar `ticket_20260801-1411.pdf`: emparejar cada línea contra el catálogo con
   `producto_id` cuando exista, crear como `por_definir` (solo nombre + categoría básica)
   los que no existan
3. 👤 Probar el botón "Capturar producto" con uno o dos productos `por_definir`
4. 🤖 Procesar los marcados como `por_capturar` (buscar en API del supermercado, `PATCH`)

## 2026-07-25/28 — Catálogo real, fix badge Activo/Inactivo y campo zona

### Contexto
Primera revisión del proyecto desde su despliegue (22-23/06). Todas las pestañas de la app
(`http://192.168.31.131/despensa/`) mostraban "Sin resultados": frontend y API funcionando
correctamente, pero base de datos completamente vacía — nunca se había cargado un dato real.

### Carga del catálogo desde la API pública de Mercadona
- Detectada API pública de Mercadona (`tienda.mercadona.es/api/categories/...`), sin autenticación,
  con nombre, marca, categoría, formato/unidad y precio por producto.
- Seleccionados 40 productos reales (5 por categoría) en 8 categorías típicas de despensa:
  Arroz/legumbres/pasta, Aceite/especias, Conservas, Azúcar/chocolate, Agua/refrescos,
  Aperitivos, Huevos/leche/mantequilla, Panadería.
- Insertados vía `POST /api/catalogo` con `supermercado_habitual = "Mercadona"` y
  `caducidad_dias_defecto` estimado por tipo de producto (ninguno de estos dos venía de la API).
- Decisión explícita: **no se cargó stock** con datos inventados — el catálogo es solo un
  diccionario de productos posibles, pero el stock debe reflejar lo que el usuario tiene
  realmente. Queda pendiente que el usuario aporte su inventario real.

### Bug: badge Activo/Inactivo siempre en "Inactivo"
- Causa: `static/app.js` (función `renderCardCatalogo` y filtro de `renderCatalogo`) comprobaba
  `item.activo` (booleano), campo que la API nunca ha devuelto — el campo real es
  `estado` (string: `activo` / `por_definir`). Como `item.activo` era siempre `undefined`,
  todos los productos se pintaban como "Inactivo" sin importar su valor real.
- Fix: comparar `item.estado === 'activo'` en el badge, y `item.estado === _catalogoFiltro`
  en el filtro "Por definir" (antes usaba una negación que mezclaba inactivos y por_definir).
- Commit `87265b5`, desplegado y verificado en producción.
- **Aviso encontrado en el proceso:** tras desplegar, el navegador seguía mostrando el bug
  porque `index.html` carga `app.js` sin parámetro de cache-busting (`<script src="app.js">`).
  Se resolvió con refresco forzado (Ctrl+Shift+R). Mismo problema que tuvieron FiDo/ReDo en su
  día — **pendiente valorar** si añadir `?v=N` a DeDo también, para no depender de que el
  usuario recuerde hacer hard refresh en cada despliegue.

### Campo `zona`: existía en el esquema pero no en el API
- La columna `zona TEXT` ya estaba en `app/esquema.sql` desde el principio, pero completamente
  aislada: no estaba en `ProductoRespuesta`/`ProductoCrear`/`ProductoActualizar` (`modelos.py`)
  ni en la lista de columnas del `INSERT` de `crear_producto()` (`rutas/catalogo.py`). Ni se
  podía leer (Pydantic la descartaba de la respuesta) ni escribir (ausente del modelo de entrada).
- Fix: añadido `zona: Optional[str] = None` a los 3 modelos y a la lista de columnas/valores
  del `INSERT`. El `PATCH` no necesitó cambios (ya es dinámico según el modelo).
- Commit `b3ae39e`, **pendiente desplegar** (`actualizar.sh` en la VM) antes de poder guardar
  valores reales de zona.

### `descripcion_visual` generada a partir de fotos reales
- Recuperado el campo `thumbnail` (imagen 300×300) de la API de Mercadona para los 40 productos
  cargados, cruzando por nombre.
- Descargadas las 40 miniaturas a un directorio temporal de la sesión (no se han guardado en
  DeDo ni en su base de datos — decisión explícita del usuario para no gastar almacenamiento).
- Redactada manualmente una `descripcion_visual` por producto a partir de cada imagen: forma y
  tamaño del envase, colores dominantes, elementos visuales clave (logos, tapones, etiquetas) y
  cómo aparece habitualmente en el ticket — siguiendo el criterio documentado en
  `DeDo - analisis.md` sección 7b.
- Aplicadas las 40 vía `PATCH /api/catalogo/{id}` (sin necesidad de desplegar nada, el campo ya
  existía en el API). Verificado con muestra en producción.
- Preparados también (no aplicados aún) los 40 valores de `zona` correspondientes
  (`alacena` / `cuartillo` / `frigorifico`), pendientes del despliegue del campo.

### Recordatorio del concepto de reconocimiento visual (Fase 5b, sin empezar)
Documentado en `DeDo - analisis.md` 5.2 y 7b: el usuario fotografía una zona de la casa,
Claude compara lo visible contra `descripcion_visual` de cada producto del catálogo, detecta
productos y cantidades, y llama a `POST /api/foto-despensa` con zona + detectados. DeDo
**sobrescribe** (no suma) el stock de esa zona. Lo no reconocido se crea como `por_definir`.
Este endpoint y el flujo completo **no están implementados** — es trabajo futuro de la Fase 5b.

### Estado final de la sesión
- Catálogo: 40 productos reales con nombre, marca, categoría, unidad, caducidad estimada y
  descripción visual completos.
- Stock: vacío, a la espera de datos reales del usuario.
- Campo `zona`: código listo y pusheado, pendiente de despliegue en la VM.
- Bug de badge Activo/Inactivo: corregido y verificado en producción.

### Próximo paso concreto
1. 👤 Ejecutar `actualizar.sh` en la VM para desplegar el campo `zona` (commit `b3ae39e`)
2. 🤖 Enviar los 40 valores de `zona` ya preparados, una vez desplegado
3. 👤 Aportar el stock real (aunque sea aproximado) para cargar la pestaña Despensa
4. 👤 Probar `POST /api/tickets` con un ticket real (Fase 2d, pendiente desde el despliegue inicial)
