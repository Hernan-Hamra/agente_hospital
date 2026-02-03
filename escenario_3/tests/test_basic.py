#!/usr/bin/env python3
"""
Tests básicos para Escenario 3 (Modo Agente)
=============================================

Verifica que los componentes funcionan correctamente.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest


class TestStructure:
    """Tests de estructura del escenario"""

    def test_config_exists(self):
        """Verifica que existe scenario.yaml"""
        config_path = Path(__file__).parent.parent / "config" / "scenario.yaml"
        assert config_path.exists(), "Falta config/scenario.yaml"

    def test_entities_exists(self):
        """Verifica que existe entities.yaml"""
        entities_path = Path(__file__).parent.parent / "config" / "entities.yaml"
        assert entities_path.exists(), "Falta config/entities.yaml"


class TestImports:
    """Tests de imports"""

    def test_import_retriever(self):
        """Verifica import del retriever"""
        from escenario_3.rag.retriever import ChromaRetriever
        assert ChromaRetriever is not None

    def test_import_llm_client(self):
        """Verifica import del cliente LLM"""
        from escenario_3.llm.client import GroqClient
        assert GroqClient is not None

    def test_import_router(self):
        """Verifica import del router"""
        from escenario_3.core.router import AgenteRouter
        assert AgenteRouter is not None

    def test_import_entity_detector(self):
        """Verifica import del entity detector"""
        from escenario_3.core.entity_detector import EntityDetector
        assert EntityDetector is not None


class TestConfig:
    """Tests de configuración"""

    def test_config_values(self):
        """Verifica valores del config"""
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "scenario.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert config["mode"]["type"] == "agente"
        assert config["mode"]["use_history"] == True
        assert config["rag"]["type"] == "chromadb"


def test_all():
    """Test agregador para pytest"""
    # Estructura
    t = TestStructure()
    t.test_config_exists()
    t.test_entities_exists()

    # Imports
    t2 = TestImports()
    t2.test_import_retriever()
    t2.test_import_llm_client()
    t2.test_import_router()
    t2.test_import_entity_detector()

    # Config
    t3 = TestConfig()
    t3.test_config_values()

    print("All basic tests passed!")


if __name__ == "__main__":
    test_all()
