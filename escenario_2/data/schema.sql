-- =============================================================================
-- ESCENARIO 2: Schema SQLite para Obras Sociales
-- Sin LLM - Consultas estructuradas por keyword
-- =============================================================================

-- Tabla principal de obras sociales
CREATE TABLE IF NOT EXISTS obras_sociales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,          -- 'ENSALUD', 'ASI', 'IOSFA'
    nombre TEXT NOT NULL,                  -- Nombre completo
    telefono TEXT,
    email TEXT,
    portal TEXT,
    activa INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requisitos por tipo de ingreso
CREATE TABLE IF NOT EXISTS requisitos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_social_id INTEGER NOT NULL,
    tipo_ingreso TEXT NOT NULL,            -- 'ambulatorio', 'internacion', 'guardia', 'traslados'
    documentacion TEXT,                    -- Lista de docs requeridos
    validador_link TEXT,
    validador_telefono TEXT,
    validador_email TEXT,
    mail_denuncia TEXT,
    plazo_denuncia TEXT,
    formato_requerido TEXT,
    coseguro_aplica INTEGER DEFAULT 0,     -- 0=no, 1=según plan
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (obra_social_id) REFERENCES obras_sociales(id),
    UNIQUE(obra_social_id, tipo_ingreso)
);

-- Coseguros por plan y prestación
CREATE TABLE IF NOT EXISTS coseguros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_social_id INTEGER NOT NULL,
    plan TEXT NOT NULL,                    -- 'Delta Plus', 'Krono', etc.
    prestacion TEXT NOT NULL,              -- 'consulta_pediatra', 'laboratorio', etc.
    aplica INTEGER DEFAULT 1,              -- 0=exento, 1=paga
    valor REAL,                            -- Valor en pesos (NULL si no aplica)
    exentos TEXT,                          -- Condiciones de exención
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (obra_social_id) REFERENCES obras_sociales(id)
);

-- Sinónimos para normalización de input
CREATE TABLE IF NOT EXISTS sinonimos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra TEXT NOT NULL,                 -- 'internado', 'internar', 'cama'
    categoria TEXT NOT NULL,               -- 'tipo_ingreso', 'obra_social', 'prestacion'
    valor_normalizado TEXT NOT NULL,       -- 'internacion', 'ENSALUD', 'consulta_especialista'
    UNIQUE(palabra, categoria)
);

-- Restricciones temporales (falta de pago, convenios suspendidos, etc.)
CREATE TABLE IF NOT EXISTS restricciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_social_id INTEGER NOT NULL,
    tipo_restriccion TEXT NOT NULL,        -- 'falta_pago', 'convenio_suspendido', 'cupo_agotado'
    tipos_bloqueados TEXT,                 -- 'internacion,ambulatorio' (coma separado, NULL = todos)
    tipos_permitidos TEXT,                 -- 'guardia' (solo estos permitidos)
    mensaje TEXT NOT NULL,                 -- Mensaje a mostrar al usuario
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,                        -- NULL = indefinido
    activa INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (obra_social_id) REFERENCES obras_sociales(id)
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_requisitos_tipo ON requisitos(tipo_ingreso);
CREATE INDEX IF NOT EXISTS idx_coseguros_plan ON coseguros(plan);
CREATE INDEX IF NOT EXISTS idx_sinonimos_palabra ON sinonimos(palabra);
CREATE INDEX IF NOT EXISTS idx_obras_sociales_codigo ON obras_sociales(codigo);
CREATE INDEX IF NOT EXISTS idx_restricciones_os ON restricciones(obra_social_id);
CREATE INDEX IF NOT EXISTS idx_restricciones_activa ON restricciones(activa);
