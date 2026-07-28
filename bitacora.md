# Bitácora — DeDo

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
