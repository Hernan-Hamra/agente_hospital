"""
Extractor de entidades del texto del usuario
"""
import re
from typing import Dict, Optional, List
from difflib import SequenceMatcher


class EntityExtractor:
    """Extrae entidades relevantes de la consulta del usuario"""

    # Obras sociales conocidas
    OBRAS_SOCIALES = {
        'ensalud': 'ENSALUD',
        'en salud': 'ENSALUD',
        'asi': 'ASI',
        'asi salud': 'ASI',
        'iosfa': 'IOSFA',
        'osde': 'OSDE',
        'swiss medical': 'SWISS_MEDICAL',
        'galeno': 'GALENO',
        'omint': 'OMINT',
        'medicus': 'MEDICUS',
        'sancor': 'SANCOR',
    }

    # Tipos de consulta
    TIPOS_CONSULTA = {
        'enrolamiento': ['enrolar', 'enrolamiento', 'enrola', 'alta', 'registrar', 'ingresar'],
        'autorizacion': ['autorizar', 'autorización', 'permiso', 'aprobación'],
        'internacion': ['internar', 'internación', 'ingreso', 'hospitalización'],
        'derivacion': ['derivar', 'derivación', 'transferir', 'trasladar'],
        'documentacion': ['documentos', 'documentación', 'papeles', 'requisitos', 'necesito'],
        'cobertura': ['cubre', 'cobertura', 'cubierto', 'incluye'],
    }

    # Niveles de urgencia
    URGENCIAS = {
        'urgente': ['urgente', 'urgencia', 'ya', 'ahora', 'emergencia', 'guardia'],
        'programado': ['programado', 'turno', 'cita', 'consulta'],
    }

    def extract(self, texto: str) -> Dict:
        """
        Extrae entidades del texto

        Returns:
            Dict con entidades detectadas: {
                'obra_social': str | None,
                'tipo_consulta': List[str],
                'urgencia': str | None,
                'confidence': float
            }
        """
        texto_lower = texto.lower()

        result = {
            'obra_social': None,
            'tipo_consulta': [],
            'urgencia': None,
            'confidence': 0.0
        }

        # 1. Detectar obra social
        obra_social, os_confidence = self._extract_obra_social(texto_lower)
        result['obra_social'] = obra_social

        # 2. Detectar tipo de consulta
        tipos = self._extract_tipo_consulta(texto_lower)
        result['tipo_consulta'] = tipos

        # 3. Detectar urgencia
        urgencia = self._extract_urgencia(texto_lower)
        result['urgencia'] = urgencia

        # 4. Calcular confianza general
        confidence_factors = []
        if obra_social:
            confidence_factors.append(os_confidence)
        if tipos:
            confidence_factors.append(0.8)
        if urgencia:
            confidence_factors.append(0.7)

        result['confidence'] = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0

        return result

    def _extract_obra_social(self, texto: str) -> tuple[Optional[str], float]:
        """Extrae obra social del texto (tolera typos)"""
        # 1. Buscar coincidencias directas (exactas)
        for key, value in self.OBRAS_SOCIALES.items():
            # Buscar palabra completa
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, texto):
                return value, 0.95

        # 2. Buscar coincidencias parciales (substring)
        for key, value in self.OBRAS_SOCIALES.items():
            if key in texto:
                return value, 0.75

        # 3. Fuzzy matching (tolera typos: "ennsalud" → "ensalud")
        palabras = texto.split()
        for palabra in palabras:
            if len(palabra) < 3:  # Ignorar palabras muy cortas
                continue

            for key, value in self.OBRAS_SOCIALES.items():
                # Calcular similitud (0-1)
                similarity = SequenceMatcher(None, palabra.lower(), key.lower()).ratio()

                # Si la similitud es > 0.8, probablemente es un typo
                if similarity > 0.8:
                    return value, similarity * 0.8  # Penalizar un poco por no ser exacto

        return None, 0.0

    def _extract_tipo_consulta(self, texto: str) -> List[str]:
        """Extrae tipos de consulta del texto"""
        tipos_detectados = []

        for tipo, keywords in self.TIPOS_CONSULTA.items():
            for keyword in keywords:
                if keyword in texto:
                    tipos_detectados.append(tipo)
                    break

        return list(set(tipos_detectados))  # Eliminar duplicados

    def _extract_urgencia(self, texto: str) -> Optional[str]:
        """Extrae nivel de urgencia"""
        for nivel, keywords in self.URGENCIAS.items():
            for keyword in keywords:
                if keyword in texto:
                    return nivel

        return None

    def format_summary(self, entities: Dict) -> str:
        """Formatea un resumen de las entidades detectadas"""
        parts = []

        if entities['obra_social']:
            parts.append(f"Obra social: {entities['obra_social']}")

        if entities['tipo_consulta']:
            tipos = ", ".join(entities['tipo_consulta'])
            parts.append(f"Tipo: {tipos}")

        if entities['urgencia']:
            parts.append(f"Urgencia: {entities['urgencia']}")

        if parts:
            return " | ".join(parts)
        else:
            return "Sin entidades detectadas"
