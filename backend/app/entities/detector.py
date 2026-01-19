"""
Detector de entidades para Modo Consulta.
Detección SIN LLM usando diccionario de aliases.

Reglas:
- Si detecta entidad → retorna para filtrar RAG
- Si NO detecta entidad → retorna None (el router responde mensaje fijo)
- NO existe RAG general
- NO se mezclan corpora
"""
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import yaml


@dataclass
class EntityResult:
    """Resultado de la detección de entidad"""
    entity: Optional[str]           # IOSFA | ENSALUD | ASI | GRUPO_PEDIATRICO | None
    entity_type: Optional[str]      # obra_social | institucion | None
    rag_filter: Optional[str]       # Valor para filtrar RAG
    matched_term: Optional[str]     # Término que matcheó
    confidence: str                 # exact | alias | none

    @property
    def detected(self) -> bool:
        """True si se detectó una entidad válida"""
        return self.entity is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "entity_type": self.entity_type,
            "rag_filter": self.rag_filter,
            "matched_term": self.matched_term,
            "confidence": self.confidence,
            "detected": self.detected
        }


class EntityDetector:
    """
    Detector de entidades usando diccionario de aliases.
    NO usa LLM. Matching por substring (contains).
    """

    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: Ruta a entities.yaml (opcional, busca por defecto)
        """
        if config_path is None:
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "config" / "entities.yaml",
                Path("config/entities.yaml"),
                Path("../config/entities.yaml"),
            ]
            for p in possible_paths:
                if p.exists():
                    config_path = str(p)
                    break

        if config_path is None:
            raise FileNotFoundError("No se encontró config/entities.yaml")

        self.config_path = Path(config_path)
        self._entities: Dict[str, Dict] = {}
        self._priority: List[str] = []
        self._no_entity_message: str = ""
        self._load_config()

    def _load_config(self):
        """Carga configuración desde YAML"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self._entities = config.get("entities", {})
        self._priority = config.get("detection", {}).get("priority", list(self._entities.keys()))
        self._no_entity_message = config.get("no_entity_response", {}).get(
            "message",
            "¿Para qué obra social es la consulta (IOSFA, ENSALUD, ASI) o es para el Grupo Pediátrico?\nVolvé a hacer la pregunta especificándolo."
        )

    def _normalize(self, text: str) -> str:
        """
        Normaliza texto para matching:
        - Lowercase
        - Remueve acentos
        - Limpia espacios extras
        """
        text = text.lower().strip()
        # Remover acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Limpiar espacios múltiples
        text = ' '.join(text.split())
        return text

    def detect(self, query: str) -> EntityResult:
        """
        Detecta entidad en la query.

        Args:
            query: Texto de la consulta del usuario

        Returns:
            EntityResult con la entidad detectada o None
        """
        query_normalized = self._normalize(query)

        # Evaluar entidades en orden de prioridad
        for entity_name in self._priority:
            entity_config = self._entities.get(entity_name, {})
            aliases = entity_config.get("aliases", [])

            # Verificar nombre canónico (exact)
            canonical_normalized = self._normalize(entity_config.get("canonical", entity_name))
            if canonical_normalized in query_normalized:
                return EntityResult(
                    entity=entity_name,
                    entity_type=entity_config.get("type"),
                    rag_filter=entity_config.get("rag_filter", entity_name),
                    matched_term=entity_config.get("canonical", entity_name),
                    confidence="exact"
                )

            # Verificar aliases
            for alias in aliases:
                alias_normalized = self._normalize(alias)
                if alias_normalized in query_normalized:
                    return EntityResult(
                        entity=entity_name,
                        entity_type=entity_config.get("type"),
                        rag_filter=entity_config.get("rag_filter", entity_name),
                        matched_term=alias,
                        confidence="alias"
                    )

        # No se detectó entidad
        return EntityResult(
            entity=None,
            entity_type=None,
            rag_filter=None,
            matched_term=None,
            confidence="none"
        )

    def get_no_entity_message(self) -> str:
        """Retorna el mensaje fijo cuando no se detecta entidad"""
        return self._no_entity_message.strip()

    def get_valid_entities(self) -> List[str]:
        """Retorna lista de entidades válidas"""
        return list(self._entities.keys())

    def get_entity_type(self, entity: str) -> Optional[str]:
        """Retorna el tipo de una entidad (obra_social | institucion)"""
        return self._entities.get(entity, {}).get("type")


# Singleton global
_entity_detector: Optional[EntityDetector] = None


def get_entity_detector(config_path: str = None) -> EntityDetector:
    """Obtiene el detector de entidades (singleton)"""
    global _entity_detector
    if _entity_detector is None:
        _entity_detector = EntityDetector(config_path)
    return _entity_detector


def reset_entity_detector():
    """Resetea el singleton (útil para tests)"""
    global _entity_detector
    _entity_detector = None
