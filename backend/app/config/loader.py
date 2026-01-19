"""
Cargador de configuración desde YAML
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml


@dataclass
class LLMConfig:
    """Configuración del LLM"""
    provider: str
    model: str
    host: Optional[str] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ModeConfig:
    """Configuración del modo de operación"""
    type: str  # "consulta" o "agente"
    use_history: bool = False
    max_history_turns: int = 0
    use_function_calling: bool = False


@dataclass
class PromptConfig:
    """Configuración de prompts"""
    system: str
    user_template: str


@dataclass
class CostsConfig:
    """Configuración de costos"""
    input_per_million: float = 0.0
    output_per_million: float = 0.0
    electricity_per_hour: float = 0.0


@dataclass
class LimitsConfig:
    """Límites operativos"""
    max_tokens_per_query: int = 1000
    daily_queries: int = -1  # -1 = sin límite


@dataclass
class ScenarioConfig:
    """Configuración completa de un escenario"""
    name: str
    description: str
    enabled: bool
    llm: LLMConfig
    mode: ModeConfig
    prompt: PromptConfig
    costs: CostsConfig
    limits: LimitsConfig

    @classmethod
    def from_dict(cls, scenario_id: str, data: Dict) -> "ScenarioConfig":
        """Crea ScenarioConfig desde diccionario YAML"""
        return cls(
            name=data.get("name", scenario_id),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            llm=LLMConfig(
                provider=data["llm"]["provider"],
                model=data["llm"]["model"],
                host=data["llm"].get("host"),
                parameters=data["llm"].get("parameters", {})
            ),
            mode=ModeConfig(
                type=data["mode"]["type"],
                use_history=data["mode"].get("use_history", False),
                max_history_turns=data["mode"].get("max_history_turns", 0),
                use_function_calling=data["mode"].get("use_function_calling", False)
            ),
            prompt=PromptConfig(
                system=data["prompt"]["system"],
                user_template=data["prompt"]["user_template"]
            ),
            costs=CostsConfig(
                input_per_million=data.get("costs", {}).get("input_per_million", 0),
                output_per_million=data.get("costs", {}).get("output_per_million", 0),
                electricity_per_hour=data.get("costs", {}).get("electricity_per_hour", 0)
            ),
            limits=LimitsConfig(
                max_tokens_per_query=data.get("limits", {}).get("max_tokens_per_query", 1000),
                daily_queries=data.get("limits", {}).get("daily_queries", -1)
            )
        )


@dataclass
class RAGConfig:
    """Configuración global del RAG"""
    embedding_model: str
    faiss_index_path: str
    top_k: int
    similarity_threshold: float


@dataclass
class GlobalConfig:
    """Configuración global del sistema"""
    rag: RAGConfig
    metrics_db_path: str
    metrics_enabled: bool
    logging_level: str
    obras_sociales: List[str]


class ConfigLoader:
    """Carga y gestiona la configuración desde YAML"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Buscar en ubicaciones estándar
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "config" / "scenarios.yaml",
                Path("config/scenarios.yaml"),
                Path("../config/scenarios.yaml"),
            ]
            for p in possible_paths:
                if p.exists():
                    config_path = str(p)
                    break

        if config_path is None:
            raise FileNotFoundError("No se encontró el archivo de configuración scenarios.yaml")

        self.config_path = Path(config_path)
        self._raw_config: Dict = {}
        self._scenarios: Dict[str, ScenarioConfig] = {}
        self._global: Optional[GlobalConfig] = None
        self._load()

    def _load(self):
        """Carga el archivo YAML"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._raw_config = yaml.safe_load(f)

        # Cargar configuración global
        global_cfg = self._raw_config.get("global", {})
        rag_cfg = global_cfg.get("rag", {})
        metrics_cfg = global_cfg.get("metrics_db", {})
        logging_cfg = global_cfg.get("logging", {})
        obras_cfg = self._raw_config.get("obras_sociales", {})

        self._global = GlobalConfig(
            rag=RAGConfig(
                embedding_model=rag_cfg.get("embedding_model", "BAAI/bge-large-en-v1.5"),
                faiss_index_path=rag_cfg.get("faiss_index_path", "./faiss_index"),
                top_k=rag_cfg.get("top_k", 3),
                similarity_threshold=rag_cfg.get("similarity_threshold", 0.65)
            ),
            metrics_db_path=metrics_cfg.get("path", "./data/metrics.db"),
            metrics_enabled=metrics_cfg.get("enabled", True),
            logging_level=logging_cfg.get("level", "INFO"),
            obras_sociales=obras_cfg.get("supported", ["ENSALUD", "ASI", "IOSFA"])
        )

        # Cargar escenarios (solo los que tienen estructura LLM completa)
        scenarios_cfg = self._raw_config.get("scenarios", {})
        for scenario_id, scenario_data in scenarios_cfg.items():
            # Saltar escenarios especiales (comparativo, etc.) que no tienen llm
            if "llm" not in scenario_data:
                continue
            if scenario_data.get("enabled", True):
                self._scenarios[scenario_id] = ScenarioConfig.from_dict(scenario_id, scenario_data)

    def reload(self):
        """Recarga la configuración desde disco"""
        self._scenarios.clear()
        self._load()

    @property
    def global_config(self) -> GlobalConfig:
        """Retorna la configuración global"""
        return self._global

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        """Obtiene la configuración de un escenario específico"""
        return self._scenarios.get(scenario_id)

    def get_all_scenarios(self) -> Dict[str, ScenarioConfig]:
        """Retorna todos los escenarios habilitados"""
        return self._scenarios.copy()

    def get_enabled_scenarios(self) -> List[str]:
        """Retorna los IDs de escenarios habilitados"""
        return [sid for sid, cfg in self._scenarios.items() if cfg.enabled]

    def get_scenarios_by_mode(self, mode: str) -> List[str]:
        """Retorna escenarios filtrados por modo (consulta/agente)"""
        return [
            sid for sid, cfg in self._scenarios.items()
            if cfg.mode.type == mode and cfg.enabled
        ]

    def get_scenarios_by_provider(self, provider: str) -> List[str]:
        """Retorna escenarios filtrados por provider (groq/ollama)"""
        return [
            sid for sid, cfg in self._scenarios.items()
            if cfg.llm.provider == provider and cfg.enabled
        ]

    def get_comparison_scenarios(self) -> Optional[List[str]]:
        """Retorna los escenarios configurados para comparación"""
        comparativo = self._raw_config.get("scenarios", {}).get("comparativo", {})
        return comparativo.get("compare_scenarios")

    def get_raw_config(self) -> Dict:
        """Retorna la configuración YAML completa"""
        return self._raw_config.copy()


# Singleton global (opcional)
_config_loader: Optional[ConfigLoader] = None


def get_config(config_path: str = None) -> ConfigLoader:
    """Obtiene el loader de configuración (singleton)"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)
    return _config_loader


def reset_config():
    """Resetea el singleton (útil para tests)"""
    global _config_loader
    _config_loader = None
