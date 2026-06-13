-- Esquema inicial de DeDo

CREATE TABLE IF NOT EXISTS catalogo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    marca TEXT,
    categoria TEXT,
    descripcion_visual TEXT,
    supermercado_habitual TEXT,
    stock_minimo REAL DEFAULT 1,
    unidad TEXT DEFAULT 'unidad',
    caducidad_dias_defecto INTEGER,
    estado TEXT DEFAULT 'activo' CHECK(estado IN ('activo', 'por_definir')),
    creado_en TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL REFERENCES catalogo(id),
    cantidad REAL DEFAULT 0,
    fecha_caducidad TEXT,
    lote TEXT,
    actualizado_en TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lista_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER REFERENCES catalogo(id),
    nombre_libre TEXT,
    cantidad REAL DEFAULT 1,
    unidad TEXT,
    motivo TEXT,
    creado_en TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supermercado TEXT,
    fecha TEXT,
    total REAL,
    fichero_origen TEXT,
    procesado_en TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lineas_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    producto_id INTEGER REFERENCES catalogo(id),
    nombre_raw TEXT,
    cantidad REAL,
    precio_unitario REAL,
    precio_total REAL
);

CREATE TABLE IF NOT EXISTS historial_precios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL REFERENCES catalogo(id),
    supermercado TEXT,
    precio REAL,
    fecha TEXT,
    ticket_id INTEGER REFERENCES tickets(id)
);

CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    tipo TEXT CHECK(tipo IN ('desayuno', 'almuerzo', 'comida', 'merienda', 'cena')),
    descripcion TEXT,
    registrado_en TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS menu_productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER NOT NULL REFERENCES menu(id),
    producto_id INTEGER REFERENCES catalogo(id),
    nombre_libre TEXT
);
