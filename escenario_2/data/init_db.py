"""
Inicialización de la base de datos SQLite para Escenario 2.

Uso:
    python escenario_2/data/init_db.py
"""
import sqlite3
from pathlib import Path


def init_database(db_path: str = None) -> sqlite3.Connection:
    """
    Inicializa la base de datos con el schema y datos semilla.

    Args:
        db_path: Ruta a la base de datos. Si es None, usa la ruta por defecto.

    Returns:
        Conexión a la base de datos.
    """
    if db_path is None:
        db_path = Path(__file__).parent / "obras_sociales.db"

    # Crear conexión
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Cargar schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()

    conn.executescript(schema)

    # Insertar sinónimos base
    _seed_sinonimos(conn)

    conn.commit()
    print(f"Base de datos inicializada en: {db_path}")

    return conn


def _seed_sinonimos(conn: sqlite3.Connection):
    """Inserta sinónimos base para normalización."""

    sinonimos = [
        # Tipo de ingreso
        ("ambulatorio", "tipo_ingreso", "ambulatorio"),
        ("turno", "tipo_ingreso", "ambulatorio"),
        ("turnos", "tipo_ingreso", "ambulatorio"),
        ("consulta", "tipo_ingreso", "ambulatorio"),
        ("consultorio", "tipo_ingreso", "ambulatorio"),

        ("internacion", "tipo_ingreso", "internacion"),
        ("internación", "tipo_ingreso", "internacion"),
        ("internar", "tipo_ingreso", "internacion"),
        ("internado", "tipo_ingreso", "internacion"),
        ("cama", "tipo_ingreso", "internacion"),
        ("programada", "tipo_ingreso", "internacion"),
        ("cirugia", "tipo_ingreso", "internacion"),
        ("cirugía", "tipo_ingreso", "internacion"),

        ("guardia", "tipo_ingreso", "guardia"),
        ("urgencia", "tipo_ingreso", "guardia"),
        ("urgencias", "tipo_ingreso", "guardia"),
        ("emergencia", "tipo_ingreso", "guardia"),

        ("traslado", "tipo_ingreso", "traslados"),
        ("traslados", "tipo_ingreso", "traslados"),
        ("derivacion", "tipo_ingreso", "traslados"),
        ("derivación", "tipo_ingreso", "traslados"),
        ("ambulancia", "tipo_ingreso", "traslados"),

        # Obras sociales
        ("ensalud", "obra_social", "ENSALUD"),
        ("en salud", "obra_social", "ENSALUD"),

        ("asi", "obra_social", "ASI"),
        ("asi salud", "obra_social", "ASI"),

        ("iosfa", "obra_social", "IOSFA"),
        ("fuerzas armadas", "obra_social", "IOSFA"),

        # Prestaciones (para coseguros)
        ("pediatra", "prestacion", "consulta_pediatra"),
        ("especialista", "prestacion", "consulta_especialista"),
        ("laboratorio", "prestacion", "laboratorio_basico"),
        ("ecografia", "prestacion", "imagenes_baja"),
        ("ecografía", "prestacion", "imagenes_baja"),
        ("radiografia", "prestacion", "imagenes_baja"),
        ("radiografía", "prestacion", "imagenes_baja"),
        ("tomografia", "prestacion", "imagenes_alta"),
        ("tomografía", "prestacion", "imagenes_alta"),
        ("resonancia", "prestacion", "imagenes_alta"),
        ("tac", "prestacion", "imagenes_alta"),
        ("rmn", "prestacion", "imagenes_alta"),
        ("kinesiologia", "prestacion", "kinesiologia"),
        ("kinesiología", "prestacion", "kinesiologia"),
        ("kinesio", "prestacion", "kinesiologia"),
        ("fonoaudiologia", "prestacion", "fonoaudiologia"),
        ("fonoaudiología", "prestacion", "fonoaudiologia"),
        ("fono", "prestacion", "fonoaudiologia"),
    ]

    # Insertar solo si no existen
    cursor = conn.cursor()
    for palabra, categoria, valor in sinonimos:
        cursor.execute("""
            INSERT OR IGNORE INTO sinonimos (palabra, categoria, valor_normalizado)
            VALUES (?, ?, ?)
        """, (palabra, categoria, valor))

    print(f"Sinónimos cargados: {len(sinonimos)}")


def seed_ensalud(conn: sqlite3.Connection):
    """
    Carga datos de ENSALUD desde los JSON existentes.
    """
    cursor = conn.cursor()

    # 1. Insertar obra social
    cursor.execute("""
        INSERT OR IGNORE INTO obras_sociales (codigo, nombre, telefono, email, portal)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "ENSALUD",
        "ENSALUD - Seguridad Social",
        "11-66075765",
        "administracion@ensalud.org",
        "https://ensalud.org/novedades/soy-prestador/"
    ))

    # Obtener ID
    cursor.execute("SELECT id FROM obras_sociales WHERE codigo = 'ENSALUD'")
    os_id = cursor.fetchone()[0]

    # 2. Insertar requisitos por tipo de ingreso
    requisitos_ensalud = [
        {
            "tipo_ingreso": "ambulatorio",
            "documentacion": "Carnet de afiliación, DNI",
            "validador_link": "https://ensalud.org/novedades/soy-prestador/",
            "validador_telefono": "11-66075765",
            "validador_email": "administracion@ensalud.org",
            "coseguro_aplica": 1,
            "notas": "Especialidades quirúrgicas y obstetricia requieren autorización PREVIA. Vigencia autorizaciones: 30 días."
        },
        {
            "tipo_ingreso": "internacion",
            "documentacion": "DNI, Carnet de afiliación",
            "validador_link": "https://ensalud.org/novedades/soy-prestador/",
            "validador_telefono": "11-66075765",
            "mail_denuncia": "auditoria@ensalud.org",
            "plazo_denuncia": "Dentro de las 24 horas",
            "coseguro_aplica": 0,
            "notas": "Internación programada requiere autorización PREVIA. Censo diario obligatorio a auditoria@ensalud.org"
        },
        {
            "tipo_ingreso": "guardia",
            "documentacion": "DNI, Carnet de afiliación",
            "validador_link": "https://ensalud.org/novedades/soy-prestador/",
            "validador_telefono": "11-66075765",
            "coseguro_aplica": 0,
            "notas": "TODOS los planes exentos de coseguro en guardia. NO requiere autorización previa."
        },
        {
            "tipo_ingreso": "traslados",
            "documentacion": "Consultar con la obra social",
            "validador_link": "https://ensalud.org/novedades/soy-prestador/",
            "validador_telefono": "11-66075765",
            "validador_email": "administracion@ensalud.org",
            "notas": "Información no disponible en documentación actual. Contactar directamente."
        }
    ]

    for req in requisitos_ensalud:
        cursor.execute("""
            INSERT OR REPLACE INTO requisitos
            (obra_social_id, tipo_ingreso, documentacion, validador_link, validador_telefono,
             validador_email, mail_denuncia, plazo_denuncia, coseguro_aplica, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            os_id,
            req["tipo_ingreso"],
            req.get("documentacion"),
            req.get("validador_link"),
            req.get("validador_telefono"),
            req.get("validador_email"),
            req.get("mail_denuncia"),
            req.get("plazo_denuncia"),
            req.get("coseguro_aplica", 0),
            req.get("notas")
        ))

    # 3. Insertar coseguros
    # Planes que SÍ pagan coseguro
    coseguros_delta = [
        ("Delta Plus", "consulta_pediatra", 1, 1553, "HIV, Oncología, Discapacidad, PMI"),
        ("Delta Plus", "consulta_especialista", 1, 2912, "HIV, Oncología, Discapacidad, PMI"),
        ("Delta Plus", "laboratorio_basico", 1, 971, "HIV, Oncología, Discapacidad, PMI"),
        ("Delta Plus", "imagenes_baja", 1, 971, "HIV, Oncología, Discapacidad, PMI"),
        ("Delta Plus", "imagenes_alta", 1, 4854, "HIV, Oncología, Discapacidad, PMI"),
        ("Delta Plus", "kinesiologia", 1, 971, "HIV, Oncología, Discapacidad, PMI"),
        ("Delta Plus", "fonoaudiologia", 1, 971, "HIV, Oncología, Discapacidad, PMI"),
    ]

    # Planes que NO pagan coseguro
    coseguros_quantum = [
        ("Quantum", "consulta_pediatra", 0, None, None),
        ("Quantum", "consulta_especialista", 0, None, None),
        ("Quantum", "laboratorio_basico", 0, None, None),
        ("Quantum", "imagenes_baja", 0, None, None),
        ("Quantum", "imagenes_alta", 0, None, None),
        ("Quantum Plus", "consulta_pediatra", 0, None, None),
        ("Quantum Plus", "consulta_especialista", 0, None, None),
    ]

    for plan, prestacion, aplica, valor, exentos in coseguros_delta + coseguros_quantum:
        cursor.execute("""
            INSERT OR REPLACE INTO coseguros
            (obra_social_id, plan, prestacion, aplica, valor, exentos)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (os_id, plan, prestacion, aplica, valor, exentos))

    conn.commit()
    print("Datos de ENSALUD cargados correctamente.")


if __name__ == "__main__":
    conn = init_database()
    seed_ensalud(conn)
    conn.close()
