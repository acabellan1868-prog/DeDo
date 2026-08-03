# DeDo — Prompt de Cowork: Capturar productos (por_capturar → activo)

> Documento vivo. Tarea de Cowork para enriquecer con datos reales los productos
> del catálogo que el usuario ha marcado como `por_capturar` desde la interfaz
> ("Capturar producto"), usando la API pública de Mercadona como fuente.
>
> Origen: sesión del 2026-08-02, tras capturar manualmente 3 productos
> (aceitunas rellenas de anchoa, chocolate para fundir, almendra frita) para
> afinar el proceso antes de automatizarlo. Detalle completo de esa sesión en
> `bitacora.md`.
>
> **Estado: v1, sin probar dentro de Cowork todavía.** Pensada para lanzarse
> manualmente varias veces antes de convertirla en tarea programada — ver
> "Riesgos a validar" al final.

---

## Nombre de la tarea
DeDo — Capturar productos (por_capturar → activo)

## Frecuencia recomendada (v1)
Bajo demanda / manual. Pasar a programada solo tras validar varias
ejecuciones correctas y que la regla de "no adivinar" (ver más abajo) se
demuestra fiable con más casos reales.

## Instrucciones (pegar tal cual en el prompt de la tarea)

```
Objetivo: enriquecer con datos reales los productos del catálogo de DeDo
que estén en estado `por_capturar`, usando la API pública de Mercadona.

## Endpoints DeDo (red local — usar curl/Bash directo, WebFetch no alcanza IPs locales)
- Listar pendientes:        GET http://192.168.31.131/despensa/api/catalogo/por-capturar
- Ticket de origen (precio): GET http://192.168.31.131/despensa/api/tickets
                             GET http://192.168.31.131/despensa/api/tickets/{id}
- Actualizar producto:       PATCH http://192.168.31.131/despensa/api/catalogo/{id}

## API de Mercadona (pública, sin autenticación)
- Árbol de categorías:       GET https://tienda.mercadona.es/api/categories/
- Productos de subcategoría: GET https://tienda.mercadona.es/api/categories/{id}/
- Detalle de producto:       GET https://tienda.mercadona.es/api/products/{id}/

## Proceso, por cada producto en por_capturar

1. Busca en qué ticket aparece ese `producto_id` y obtén el `precio_unitario`
   real pagado — es tu criterio de desambiguación.
2. Localiza la categoría/subcategoría de Mercadona más probable a partir de
   `categoria` y `nombre` del producto en DeDo, y lista sus productos.
3. Filtra por nombre (coincidencia parcial, ignorando acentos/mayúsculas)
   para obtener candidatos.
4. Para cada candidato, compara `price_instructions.unit_price` contra el
   precio real del ticket:
   - Si hay EXACTAMENTE UN candidato con precio coincidente → es el producto,
     continúa.
   - Si hay CERO o MÁS DE UNO con precio coincidente → NO ADIVINES. Deja el
     producto tal cual (sigue en `por_capturar`) y anótalo en el informe
     final como "pendiente de revisión manual", explicando el motivo exacto
     (sin coincidencias / empate entre N candidatos, con sus nombres y precios).
5. Con el candidato confirmado:
   - Descarga la foto (`photos[0].regular`) a un directorio TEMPORAL de la
     sesión — nunca a una carpeta persistente del repo ni de DeDo.
   - Redacta `descripcion_visual` a partir de la foto, siguiendo el criterio
     de `DeDo - analisis.md` sección 7b: forma y tamaño del envase, colores
     dominantes, elementos visuales clave (logos, tapones, textos destacados),
     y cómo aparece en el ticket (`nombre_raw` original).
   - Determina `zona` (alacena / cuartillo / frigorifico / congelador) con
     criterio, usando el catálogo ya existente como referencia de patrones.
   - Determina `caducidad_dias_defecto` con criterio, apoyándote en la tabla
     de `DeDo - analisis.md` sección 10 si el producto encaja en alguna
     categoría (conservas → 730, congelados → 90, etc.) o con una estimación
     razonable si no encaja.
   - Aplica `PATCH /api/catalogo/{id}` con: `marca`, `descripcion_visual`,
     `zona`, `caducidad_dias_defecto`, `estado: "activo"`.
6. Borra cualquier fichero temporal (imágenes descargadas) antes de terminar.

## Informe final
- Productos capturados con éxito (id, nombre, marca asignada).
- Productos dejados pendientes por ambigüedad, con el motivo concreto.
- Si `por_capturar` estaba vacío, termina sin generar ruido.

## Reglas duras
- Nunca inventes marca, EAN o descripción sin un candidato confirmado por precio.
- Nunca cambies el estado a `activo` si no se ha podido verificar el producto.
- Nunca dejes ficheros temporales al finalizar.
```

---

## Aprendizajes de la sesión manual previa (2026-08-02)

- **El precio del ticket es el desambiguador principal**, no el nombre: para
  las aceitunas hubo 4 productos de Mercadona con el mismo nombre y distinto
  formato/precio; solo uno coincidía exacto con el precio pagado (1,80 €).
- **El precio no siempre basta**: con la almendra frita, dos productos
  distintos (bolsa "pelada" 200g y "marcona" 125g) compartían precio exacto
  (2,95 €). No hay forma de resolverlo solo con datos — hubo que preguntar
  al usuario cuál había comprado realmente. De ahí la regla dura de "no
  adivinar" ante empates.
- La API de Mercadona no tiene búsqueda por texto libre útil — hay que
  navegar el árbol de categorías (`/api/categories/` → subcategoría) y
  filtrar por nombre dentro de ella.
- `zona` y `caducidad_dias_defecto` no vienen de la API de Mercadona en
  ningún caso — siempre son una estimación con criterio propio.
- Tiempo de captura sin ambigüedad: ~1-1.5 min por producto (caso limpio).
  El caso con empate de precio añade el tiempo de resolución manual, que no
  es automatizable sin una política de fallback (de ahí la regla dura).

## Riesgos a validar antes de programarla

- **Alcance de red desde el sandbox de Cowork**: en `FiDo/capturaGastosIA.md`
  hay un antecedente de que el shell no siempre estaba disponible de forma
  consistente en Cowork, y que `WebFetch` no llega a IPs locales. La versión
  actual de FiDo (`CLAUDE.md`, sección "Captura automática de gastos") ya
  llama directo a su API local desde una tarea de Cowork, así que
  probablemente esté resuelto — pero conviene confirmarlo con una ejecución
  real de esta tarea antes de fiarse y programarla en cron.
