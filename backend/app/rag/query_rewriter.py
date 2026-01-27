"""
Query Rewriter para mejorar retrieval semántico.

Transforma queries coloquiales en queries que matchean mejor con el contenido de los chunks.
"""
import re
import unicodedata
from typing import List


def _normalize_for_matching(text: str) -> str:
    """
    Normaliza texto para matching de patrones.
    Remueve tildes y convierte a lowercase.

    "¿Cuánto cuesta?" → "cuanto cuesta"
    """
    text = text.lower()
    # Remover tildes
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text


# Mapeo de sinónimos/expansiones para mejorar retrieval
SYNONYM_EXPANSIONS = {
    # Coseguros/precios
    "cuanto cuesta": "valor precio coseguro tarifa",
    "cuanto sale": "valor precio coseguro tarifa",
    "cuanto es el coseguro": "valor precio coseguro",
    "cuanto es el copago": "valor precio coseguro",
    "que precio tiene": "valor precio coseguro tarifa",
    "importe de coseguro": "valor precio coseguro tarifa pesos consulta especialista",
    "importe coseguro": "valor precio coseguro tarifa pesos consulta especialista",

    # Médicos
    "pediatra": "pediatra médico familia generalista",
    "ginecologo": "ginecólogo tocoginecólogo",
    "clinico": "clínico médico familia generalista",
    "medico de cabecera": "médico familia generalista",

    # Exenciones
    "quienes no pagan": "exentos excluidos programas HIV oncología discapacidad PMI guardia urgencia",
    "quien no paga": "exentos excluidos programas HIV oncología discapacidad PMI",
    "no paga coseguro": "exentos excluidos programas HIV oncología",
    "estan exentos": "exentos excluidos programas HIV oncología discapacidad PMI",
    "exentos de coseguro": "exentos programas HIV oncología discapacidad PMI guardia",

    # Imágenes
    "tomografia": "TAC tomografía alta complejidad",
    "resonancia": "RMN resonancia magnética alta complejidad",
    "ecografia": "ecografía imágenes baja complejidad",
    "radiografia": "RX radiografía imágenes baja complejidad",
    "imagenes alta complejidad": "TAC RMN tomografía resonancia endoscopia medicina nuclear",
    "imágenes alta complejidad": "TAC RMN tomografía resonancia endoscopia medicina nuclear",

    # Autorizaciones
    "necesito autorizacion": "requiere autorización previa",
    "tengo que pedir autorizacion": "requiere autorización previa",
    "hay que autorizar": "requiere autorización previa",

    # Documentación
    "que necesito": "requisitos documentación documentos",
    "que documentos": "requisitos documentación",
    "que tengo que llevar": "requisitos documentación documentos",
    "que debo presentar": "requisitos documentación documentos",

    # Guardia - enfatizar documentación e ingreso
    "guardia": "guardia ingreso documentación validador DNI",
    "urgencia": "guardia urgencia emergencia ingreso",
    "para guardia": "ingreso guardia documentación validador DNI checklist",

    # Internación
    "internarme": "internación internación programada",
    "internacion": "internación hospitalización",

    # Salud mental
    "salud mental": "psiquiatría psicología turnos salud mental",
    "turnos de salud mental": "psiquiatría turnos teléfono 11-5702-9599",
    "telefono salud mental": "psiquiatría turnos teléfono 11-5702-9599",

    # Tiempos y vigencia
    "cuanto tiempo": "plazo días horas vigencia",
    "en cuanto tiempo": "plazo días horas",
    "cuanto dura": "vigencia días plazo tiempo duración",
    "cuanto duran": "vigencia días plazo tiempo duración",
    "debo avisar": "denuncia plazo 24 horas",
    "avisar una internación": "denuncia internación plazo 24 horas",

    # Coseguros específicos (para que matcheen con COSEGUROS_VALORES)
    "coseguro fonoaudiología": "coseguro fonoaudiología valor prestaciones tarifa sesión",
    "coseguro laboratorio": "coseguro laboratorio valor prestaciones determinaciones tarifa",
    "coseguro fono": "coseguro fonoaudiología valor prestaciones",
    "coseguro especialista": "coseguro médicos especialistas valor tarifa precio consulta",
    "especialista": "médicos especialistas consulta valor tarifa precio",

    # Planes
    "planes disponibles": "planes Delta Krono Quantum Integral Total Global categorías",
    "que planes tiene": "planes Delta Krono Quantum Integral Total Global",
    "que planes hay": "planes Delta Krono Quantum categorías",
}

# Palabras a agregar según contexto de obra social
OBRA_SOCIAL_CONTEXT = {
    "ENSALUD": ["ENSALUD", "prestaciones"],
    "ASI": ["ASI", "ASI Salud"],
    "IOSFA": ["IOSFA", "fuerzas armadas"],
    "GRUPO_PEDIATRICO": ["grupo pediátrico", "pediatría"],
}


def rewrite_query(query: str, obra_social: str = None) -> str:
    """
    Reescribe una query para mejorar el retrieval.

    Args:
        query: Query original del usuario
        obra_social: Obra social detectada (opcional)

    Returns:
        Query expandida con sinónimos
    """
    # Normalizar query para matching (sin tildes, lowercase)
    query_normalized = _normalize_for_matching(query)
    expansions = []

    # Buscar expansiones de sinónimos (patrones ya están sin tildes)
    for pattern, expansion in SYNONYM_EXPANSIONS.items():
        if pattern in query_normalized:
            expansions.append(expansion)

    # Si hay expansiones, agregarlas a la query
    if expansions:
        expansion_text = " ".join(expansions)
        rewritten = f"{query} {expansion_text}"
    else:
        rewritten = query

    # Agregar contexto de obra social si está presente
    if obra_social and obra_social.upper() in OBRA_SOCIAL_CONTEXT:
        context = " ".join(OBRA_SOCIAL_CONTEXT[obra_social.upper()])
        if obra_social.upper() not in rewritten.upper():
            rewritten = f"{rewritten} {context}"

    return rewritten


def get_query_variations(query: str) -> List[str]:
    """
    Genera variaciones de la query para multi-query retrieval.

    Args:
        query: Query original

    Returns:
        Lista de variaciones de la query
    """
    variations = [query]
    query_lower = query.lower()

    # Variaciones comunes
    replacements = [
        ("cuanto", "valor precio"),
        ("cuesta", "coseguro"),
        ("pediatra", "médico familia"),
        ("necesito", "requisitos"),
    ]

    for old, new in replacements:
        if old in query_lower:
            variation = query_lower.replace(old, new)
            variations.append(variation)

    return variations[:3]  # Máximo 3 variaciones


# Test rápido
if __name__ == "__main__":
    test_queries = [
        ("cuanto cuesta consulta con especialista", "ENSALUD"),
        ("tarifa consulta pediatra", "ENSALUD"),
        ("quienes no pagan coseguro", "ENSALUD"),
        ("que necesito para guardia", "IOSFA"),
    ]

    print("=== TEST QUERY REWRITER ===\n")
    for query, os in test_queries:
        rewritten = rewrite_query(query, os)
        print(f"Original:  {query}")
        print(f"Reescrita: {rewritten}")
        print()
