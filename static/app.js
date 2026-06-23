/* DeDo — lógica frontend */

/* ── Prefijo de ruta (funciona en /despensa/ y en /) ── */
const BASE = (() => {
    const p = window.location.pathname;
    const m = p.match(/^(\/[^/]+\/)/);
    return (m && m[1] !== '/') ? m[1].replace(/\/$/, '') : '';
})();
const API = BASE + '/api';

/* ── Reloj ── */
function tickReloj() {
    const now  = new Date();
    const hora = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const fecha = now.toLocaleDateString('es-ES', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
    document.getElementById('dedo-hora').textContent  = hora;
    document.getElementById('dedo-fecha').textContent = fecha;
}
tickReloj();
setInterval(tickReloj, 1000);

/* ── Tema ── */
function toggleTema() {
    const html = document.documentElement;
    const actual = html.getAttribute('data-tema-cockpit');
    const nuevo  = actual === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-tema-cockpit', nuevo);
    localStorage.setItem('dedo-tema', nuevo);
}
(function aplicarTemaGuardado() {
    const guardado = localStorage.getItem('dedo-tema');
    if (guardado) document.documentElement.setAttribute('data-tema-cockpit', guardado);
})();

/* ── Pestañas ── */
const PESTANAS = ['despensa', 'lista', 'catalogo', 'caducidades', 'tickets'];

function cambiarPestana(id) {
    PESTANAS.forEach(p => {
        document.getElementById('sec-' + p).classList.toggle('dedo-seccion--oculta', p !== id);
        document.getElementById('btn-' + p).classList.toggle('activo', p === id);
    });
    if (id === 'despensa')    cargarStock();
    if (id === 'lista')       cargarLista();
    if (id === 'catalogo')    cargarCatalogo();
    if (id === 'caducidades') cargarCaducidades();
}

/* ── Helpers fetch ── */
async function get(ruta) {
    const r = await fetch(API + ruta);
    if (!r.ok) throw new Error(r.status);
    return r.json();
}
async function post(ruta, body) {
    const r = await fetch(API + ruta, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error(r.status);
    return r.json();
}
async function del(ruta) {
    const r = await fetch(API + ruta, { method: 'DELETE' });
    if (!r.ok) throw new Error(r.status);
}

/* ══════════════════════════════════════════
   PESTAÑA: DESPENSA (stock)
══════════════════════════════════════════ */
async function cargarStock() {
    const contenedor = document.getElementById('stock-lista');
    contenedor.innerHTML = '<div class="dedo-cargando">Cargando inventario…</div>';
    try {
        const items = await get('/stock');
        const filtro = document.getElementById('filtro-stock').value;
        const filtrado = filtro === 'todos' ? items
            : filtro === 'bajo' ? items.filter(i => i.cantidad <= i.stock_minimo)
            : items.filter(i => i.cantidad > i.stock_minimo);

        if (!filtrado.length) {
            contenedor.innerHTML = '<div class="dedo-cargando">Sin resultados.</div>';
            return;
        }
        contenedor.innerHTML = filtrado.map(renderCardStock).join('');
    } catch (e) {
        contenedor.innerHTML = '<div class="dedo-cargando">Error al cargar.</div>';
    }
}

function renderCardStock(item) {
    const bajo  = item.cantidad <= item.stock_minimo;
    const vacio = item.cantidad <= 0;
    const cls   = vacio ? 'vacio' : bajo ? 'bajo' : 'ok';
    return `
    <div class="dedo-card-stock">
        <div class="dedo-card-stock__indicador dedo-card-stock__indicador--${cls}"></div>
        <div class="dedo-card-stock__nombre">${esc(item.nombre_producto)}</div>
        <div class="dedo-card-stock__cantidad">${item.cantidad} ${esc(item.unidad || '')}</div>
        <div class="dedo-card-stock__meta">Mín: ${item.stock_minimo} · ${item.ubicacion ? esc(item.ubicacion) : 'Sin ubicación'}</div>
    </div>`;
}

/* ══════════════════════════════════════════
   PESTAÑA: LISTA
══════════════════════════════════════════ */
async function cargarLista() {
    const contenedor = document.getElementById('lista-items');
    contenedor.innerHTML = '<div class="dedo-cargando">Cargando lista…</div>';
    try {
        const items = await get('/lista');
        if (!items.length) {
            contenedor.innerHTML = '<div class="dedo-cargando">La lista está vacía. ¡Bien!</div>';
            return;
        }
        contenedor.innerHTML = items.map(renderItemLista).join('');
    } catch (e) {
        contenedor.innerHTML = '<div class="dedo-cargando">Error al cargar.</div>';
    }
}

function renderItemLista(item) {
    const nombre = item.nombre_libre || item.nombre_producto || '—';
    const meta   = [item.cantidad ? `${item.cantidad} ${item.unidad || ''}` : ''].filter(Boolean).join(' · ');
    return `
    <div class="dedo-item-lista" id="item-lista-${item.id}">
        <div class="dedo-item-lista__nombre">${esc(nombre)}</div>
        ${meta ? `<div class="dedo-item-lista__meta">${esc(meta)}</div>` : ''}
        <button class="dedo-item-lista__del" onclick="eliminarDeListaLocal(${item.id})" title="Eliminar">✕</button>
    </div>`;
}

async function eliminarDeListaLocal(id) {
    const el = document.getElementById('item-lista-' + id);
    if (el) el.style.opacity = '0.4';
    try {
        await del('/lista/' + id);
        if (el) el.remove();
    } catch (e) {
        if (el) el.style.opacity = '1';
    }
}

function mostrarFormLista()  { document.getElementById('form-lista').classList.remove('dedo-form--oculto'); }
function ocultarFormLista()  { document.getElementById('form-lista').classList.add('dedo-form--oculto'); }

async function añadirALista() {
    const nombre   = document.getElementById('input-nombre-libre').value.trim();
    const cantidad = parseFloat(document.getElementById('input-cantidad').value) || null;
    const unidad   = document.getElementById('input-unidad').value.trim() || null;
    if (!nombre) return;
    try {
        await post('/lista', { nombre_libre: nombre, cantidad, unidad });
        document.getElementById('input-nombre-libre').value = '';
        document.getElementById('input-cantidad').value = '1';
        document.getElementById('input-unidad').value = '';
        ocultarFormLista();
        cargarLista();
    } catch (e) { alert('Error al añadir.'); }
}

async function vaciarLista() {
    if (!confirm('¿Vaciar toda la lista?')) return;
    try {
        const items = await get('/lista');
        await Promise.all(items.map(i => del('/lista/' + i.id)));
        cargarLista();
    } catch (e) { alert('Error al vaciar.'); }
}

/* ══════════════════════════════════════════
   PESTAÑA: CATÁLOGO
══════════════════════════════════════════ */
let _catalogoFiltro = 'todos';
let _catalogoItems  = [];

async function cargarCatalogo() {
    const contenedor = document.getElementById('catalogo-lista');
    contenedor.innerHTML = '<div class="dedo-cargando">Cargando catálogo…</div>';
    try {
        _catalogoItems = await get('/catalogo');
        renderCatalogo();
    } catch (e) {
        contenedor.innerHTML = '<div class="dedo-cargando">Error al cargar.</div>';
    }
}

function filtrarCatalogo(f) {
    _catalogoFiltro = f;
    renderCatalogo();
}

function renderCatalogo() {
    const contenedor = document.getElementById('catalogo-lista');
    const filtrado = _catalogoFiltro === 'todos'      ? _catalogoItems
        : _catalogoFiltro === 'activo'    ? _catalogoItems.filter(i => i.activo)
        : _catalogoItems.filter(i => !i.activo);
    if (!filtrado.length) {
        contenedor.innerHTML = '<div class="dedo-cargando">Sin resultados.</div>';
        return;
    }
    contenedor.innerHTML = filtrado.map(renderCardCatalogo).join('');
}

function renderCardCatalogo(item) {
    const badge = item.activo
        ? '<span class="dedo-card-catalogo__badge dedo-card-catalogo__badge--activo">Activo</span>'
        : '<span class="dedo-card-catalogo__badge">Inactivo</span>';
    const meta = [item.categoria, item.marca].filter(Boolean).join(' · ');
    return `
    <div class="dedo-card-catalogo">
        <div class="dedo-card-catalogo__nombre">${esc(item.nombre)}</div>
        ${meta ? `<div class="dedo-card-catalogo__meta">${esc(meta)}</div>` : ''}
        ${badge}
    </div>`;
}

/* ══════════════════════════════════════════
   PESTAÑA: CADUCIDADES
══════════════════════════════════════════ */
async function cargarCaducidades() {
    const dias = document.getElementById('dias-vista').value || 7;
    const elProx = document.getElementById('caducidades-proximas');
    const elVenc = document.getElementById('caducidades-vencidas');
    elProx.innerHTML = '<div class="dedo-cargando">Cargando…</div>';
    elVenc.innerHTML = '<div class="dedo-cargando">Cargando…</div>';
    try {
        const [proximas, vencidas] = await Promise.all([
            get('/caducidades/proximas?dias=' + dias),
            get('/caducidades/vencidas')
        ]);
        elProx.innerHTML = proximas.length
            ? proximas.map(i => renderItemCaducidad(i, false)).join('')
            : '<div class="dedo-cargando">Sin caducidades próximas.</div>';
        elVenc.innerHTML = vencidas.length
            ? vencidas.map(i => renderItemCaducidad(i, true)).join('')
            : '<div class="dedo-cargando">Sin productos vencidos.</div>';
    } catch (e) {
        elProx.innerHTML = '<div class="dedo-cargando">Error.</div>';
        elVenc.innerHTML = '<div class="dedo-cargando">Error.</div>';
    }
}

function renderItemCaducidad(item, vencido) {
    const dias  = Math.abs(item.dias_restantes);
    const label = vencido
        ? `Hace ${dias}d`
        : `${dias}d`;
    const cls = vencido ? 'vencido' : 'pronto';
    return `
    <div class="dedo-item-caducidad">
        <div class="dedo-item-caducidad__nombre">${esc(item.nombre_producto)}</div>
        <span class="dedo-item-caducidad__dias dedo-item-caducidad__dias--${cls}">${label}</span>
    </div>`;
}

/* ── Utilidad escape HTML ── */
function esc(str) {
    return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── Carga inicial ── */
cargarStock();
