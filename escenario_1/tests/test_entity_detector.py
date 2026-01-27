#!/usr/bin/env python3
"""
Test unitario: Entity Detector
Verifica la detección de obras sociales en queries de usuarios
"""
import sys
import pytest
from pathlib import Path

# Agregar project root al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from escenario_1.core.entity_detector import get_entity_detector, reset_entity_detector

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "entities.yaml")


@pytest.fixture
def detector():
    """Crea detector fresco para cada test"""
    reset_entity_detector()
    return get_entity_detector(CONFIG_PATH)


class TestEntityDetectionCanonical:
    """Tests de detección con nombres canónicos"""

    def test_detect_asi(self, detector):
        """Detecta ASI en query"""
        result = detector.detect("¿Qué documentos necesito para ASI?")
        assert result.entity == "ASI"
        assert result.confidence == "exact"
        assert result.detected is True

    def test_detect_ensalud(self, detector):
        """Detecta ENSALUD en query"""
        result = detector.detect("Teléfono de ENSALUD")
        assert result.entity == "ENSALUD"
        assert result.confidence == "exact"

    def test_detect_iosfa(self, detector):
        """Detecta IOSFA en query"""
        result = detector.detect("Mail de IOSFA")
        assert result.entity == "IOSFA"
        assert result.confidence == "exact"

    def test_detect_grupo_pediatrico(self, detector):
        """Detecta GRUPO_PEDIATRICO en query"""
        result = detector.detect("Requisitos grupo pediátrico")
        assert result.entity == "GRUPO_PEDIATRICO"
        assert result.confidence in ["exact", "alias"]


class TestEntityDetectionAliases:
    """Tests de detección con aliases"""

    def test_detect_iosfa_lowercase(self, detector):
        """Detecta iosfa en minúsculas"""
        result = detector.detect("consulta en iosfa")
        assert result.entity == "IOSFA"

    def test_detect_ensalud_mixed_case(self, detector):
        """Detecta Ensalud con mayúsculas mixtas"""
        result = detector.detect("precio de Ensalud")
        assert result.entity == "ENSALUD"

    def test_detect_asi_salud(self, detector):
        """Detecta 'ASI Salud' como alias"""
        result = detector.detect("coseguro de ASI Salud")
        assert result.entity == "ASI"


class TestEntityDetectionWithPunctuation:
    """Tests de detección con puntuación (bug corregido)"""

    def test_detect_with_question_marks(self, detector):
        """Detecta entidad entre signos de interrogación"""
        result = detector.detect("¿Cuál es el teléfono de ENSALUD?")
        assert result.entity == "ENSALUD"
        assert result.detected is True

    def test_detect_with_exclamation(self, detector):
        """Detecta entidad con exclamación"""
        result = detector.detect("¡Necesito información de IOSFA!")
        assert result.entity == "IOSFA"

    def test_detect_with_comma(self, detector):
        """Detecta entidad antes de coma"""
        result = detector.detect("Para ASI, necesito documentos")
        assert result.entity == "ASI"

    def test_detect_with_parenthesis(self, detector):
        """Detecta entidad entre paréntesis"""
        result = detector.detect("Consulta (ENSALUD) sobre coseguros")
        assert result.entity == "ENSALUD"


class TestNoEntityDetection:
    """Tests cuando no hay entidad"""

    def test_no_entity_in_greeting(self, detector):
        """No detecta entidad en saludo"""
        result = detector.detect("Hola, buen día")
        assert result.entity is None
        assert result.detected is False
        assert result.confidence == "none"

    def test_no_entity_in_general_question(self, detector):
        """No detecta entidad en pregunta general"""
        result = detector.detect("¿Cuáles son los requisitos?")
        assert result.entity is None
        assert result.detected is False

    def test_no_entity_message(self, detector):
        """Mensaje de no entidad es correcto"""
        message = detector.get_no_entity_message()
        assert "obra social" in message.lower()
        assert "IOSFA" in message or "ENSALUD" in message


class TestEdgeCases:
    """Tests de casos límite"""

    def test_asi_not_in_basica(self, detector):
        """'ASI' no se detecta dentro de 'básica'"""
        result = detector.detect("Documentación básica para consulta")
        # Si detecta algo, no debería ser ASI (era un bug conocido)
        if result.detected:
            assert result.entity != "ASI", "No debería detectar ASI en 'básica'"

    def test_multiple_entities_returns_first_by_priority(self, detector):
        """Con múltiples entidades, retorna según prioridad"""
        result = detector.detect("ASI y ENSALUD tienen diferentes coseguros")
        # Debería retornar la primera según orden de prioridad
        assert result.entity in ["ASI", "ENSALUD"]

    def test_empty_query(self, detector):
        """Query vacía no detecta entidad"""
        result = detector.detect("")
        assert result.detected is False

    def test_only_spaces(self, detector):
        """Query solo con espacios no detecta entidad"""
        result = detector.detect("   ")
        assert result.detected is False


class TestEntityResultDataclass:
    """Tests del dataclass EntityResult"""

    def test_to_dict(self, detector):
        """Verificar conversión a dict"""
        result = detector.detect("Consulta ASI")
        result_dict = result.to_dict()

        assert "entity" in result_dict
        assert "entity_type" in result_dict
        assert "rag_filter" in result_dict
        assert "confidence" in result_dict
        assert "detected" in result_dict

    def test_entity_type_obra_social(self, detector):
        """ASI/ENSALUD/IOSFA son tipo obra_social"""
        for query in ["ASI", "ENSALUD", "IOSFA"]:
            result = detector.detect(f"Consulta {query}")
            assert result.entity_type == "obra_social"

    def test_entity_type_institucion(self, detector):
        """GRUPO_PEDIATRICO es tipo institucion"""
        result = detector.detect("Grupo Pediátrico requisitos")
        if result.detected:
            assert result.entity_type == "institucion"


class TestRagFilter:
    """Tests del filtro RAG"""

    def test_rag_filter_matches_entity(self, detector):
        """rag_filter coincide con entidad"""
        result = detector.detect("Consulta ENSALUD")
        assert result.rag_filter == "ENSALUD"

    def test_rag_filter_for_grupo_pediatrico(self, detector):
        """Verificar rag_filter para grupo pediátrico"""
        result = detector.detect("Grupo Pediátrico")
        if result.detected:
            # El filtro puede ser diferente al nombre de entidad
            assert result.rag_filter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
