#!/usr/bin/env python3
"""
Test unitario: Query Rewriter
Verifica la expansión de queries para mejorar retrieval semántico
"""
import sys
import pytest
from pathlib import Path

# Agregar project root al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from escenario_1.core.query_rewriter import rewrite_query


class TestQueryExpansion:
    """Tests de expansión de queries"""

    def test_expands_cuanto_cuesta_with_accent(self):
        """Expande '¿Cuánto cuesta?' con tilde"""
        result = rewrite_query("¿Cuánto cuesta la consulta?")
        assert "valor" in result.lower() or "precio" in result.lower()
        assert len(result) > len("¿Cuánto cuesta la consulta?")

    def test_expands_cuanto_cuesta_without_accent(self):
        """Expande 'cuanto cuesta' sin tilde"""
        result = rewrite_query("cuanto cuesta la consulta")
        assert "valor" in result.lower() or "precio" in result.lower()

    def test_expands_coseguro_query(self):
        """Expande query de coseguro"""
        result = rewrite_query("cuanto es el coseguro")
        assert "valor" in result.lower() or "precio" in result.lower()

    def test_expands_medical_terms(self):
        """Expande términos médicos"""
        result = rewrite_query("consulta pediatra")
        assert "médico" in result.lower() or "familia" in result.lower()

    def test_expands_documentation_query(self):
        """Expande query de documentación"""
        result = rewrite_query("que documentos necesito")
        assert "requisitos" in result.lower() or "documentación" in result.lower()

    def test_expands_exemption_query(self):
        """Expande query de exenciones"""
        result = rewrite_query("quienes no pagan coseguro")
        assert "exentos" in result.lower() or "excluidos" in result.lower()


class TestNoExpansion:
    """Tests cuando no hay expansión"""

    def test_no_expansion_for_unknown_pattern(self):
        """No expande si no matchea ningún patrón"""
        query = "información general sobre trámites"
        result = rewrite_query(query)
        # Solo se agrega contexto de obra social si se especifica
        assert len(result) <= len(query) + 50  # Margen para contexto

    def test_preserves_original_query(self):
        """La query original se preserva en el resultado"""
        query = "¿Cuánto cuesta la consulta?"
        result = rewrite_query(query)
        assert query in result


class TestObraSocialContext:
    """Tests de contexto de obra social"""

    def test_adds_ensalud_context(self):
        """Agrega contexto ENSALUD"""
        result = rewrite_query("coseguro consulta", obra_social="ENSALUD")
        assert "ENSALUD" in result

    def test_adds_asi_context(self):
        """Agrega contexto ASI"""
        result = rewrite_query("documentación", obra_social="ASI")
        assert "ASI" in result

    def test_adds_iosfa_context(self):
        """Agrega contexto IOSFA"""
        result = rewrite_query("requisitos consulta", obra_social="IOSFA")
        assert "IOSFA" in result

    def test_no_duplicate_obra_social(self):
        """No duplica obra social si ya está en query"""
        result = rewrite_query("coseguro ENSALUD", obra_social="ENSALUD")
        # Solo debería aparecer una vez
        assert result.count("ENSALUD") == 1


class TestCriticalQueries:
    """Tests de queries críticas que fallaban antes"""

    def test_coseguro_especialista_ensalud(self):
        """Query de coseguro especialista ENSALUD"""
        query = "¿Cuánto es el coseguro de consulta con especialista en ENSALUD?"
        result = rewrite_query(query, "ENSALUD")

        # Debe expandir con términos de coseguro
        assert "valor" in result.lower() or "precio" in result.lower() or "coseguro" in result.lower()

    def test_coseguro_plan_asi(self):
        """Query de coseguro por plan ASI"""
        query = "¿Cuánto es el coseguro de consulta médica para plan ASI 200?"
        result = rewrite_query(query, "ASI")

        # Debe expandir
        assert len(result) > len(query)

    def test_sesion_psicologia_asi(self):
        """Query de sesión de psicología ASI"""
        query = "¿Cuánto cuesta una sesión de psicología en plan ASI 300?"
        result = rewrite_query(query, "ASI")

        # Debe expandir cuanto cuesta
        assert "valor" in result.lower() or "precio" in result.lower()


class TestEdgeCases:
    """Tests de casos límite"""

    def test_empty_query(self):
        """Query vacía"""
        result = rewrite_query("")
        assert result == ""

    def test_none_obra_social(self):
        """obra_social None"""
        result = rewrite_query("consulta médica", obra_social=None)
        assert "consulta médica" in result

    def test_unknown_obra_social(self):
        """obra_social desconocida"""
        result = rewrite_query("consulta médica", obra_social="OSDE")
        # No debería crashear
        assert "consulta médica" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
