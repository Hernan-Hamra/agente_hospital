"""
Base de datos SQLite para métricas de comparación de escenarios
Solo almacena métricas operativas, no conversaciones.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import json


class MetricsDB:
    """Gestiona la base de datos de métricas para comparación de escenarios"""

    def __init__(self, db_path: str = "./data/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Inicializa las tablas si no existen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tabla de experimentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    config_snapshot TEXT
                )
            """)

            # Tabla principal de queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id INTEGER,

                    -- Identificación del escenario
                    scenario TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    llm_provider TEXT NOT NULL,
                    llm_model TEXT NOT NULL,

                    -- Input (sin datos sensibles)
                    query_hash TEXT,
                    query_length INTEGER,
                    obra_social TEXT,

                    -- Tokens
                    tokens_input INTEGER,
                    tokens_output INTEGER,
                    tokens_total INTEGER,

                    -- Latencia (ms)
                    latency_embedding_ms REAL,
                    latency_faiss_ms REAL,
                    latency_llm_ms REAL,
                    latency_total_ms REAL,

                    -- Costos (USD)
                    cost_input REAL,
                    cost_output REAL,
                    cost_total REAL,

                    -- Entity Detection (Modo Consulta)
                    entity_detected TEXT,
                    entity_type TEXT,
                    entity_confidence TEXT,
                    llm_skipped INTEGER,

                    -- RAG
                    rag_used INTEGER,
                    rag_chunks_count INTEGER,
                    rag_top_similarity REAL,

                    -- Respuesta
                    response_length INTEGER,
                    response_words INTEGER,

                    -- Estado
                    success INTEGER DEFAULT 1,
                    error_message TEXT,

                    -- Metadata
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                )
            """)

            # Tabla de evaluaciones de calidad
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER NOT NULL,

                    -- Scores automáticos (0-100)
                    precision_score REAL,
                    completitud_score REAL,
                    concision_score REAL,

                    -- Detecciones
                    hallucination_detected INTEGER,
                    terms_found TEXT,
                    terms_missing TEXT,

                    -- Score final
                    total_score REAL,
                    passed INTEGER,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (query_id) REFERENCES queries(id)
                )
            """)

            # Tabla de estadísticas agregadas por día
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    scenario TEXT NOT NULL,

                    -- Conteos
                    total_queries INTEGER,
                    successful_queries INTEGER,
                    failed_queries INTEGER,

                    -- Promedios
                    avg_tokens_total REAL,
                    avg_latency_ms REAL,
                    avg_cost_usd REAL,
                    avg_precision_score REAL,

                    -- Distribución por obra social
                    queries_by_obra_social TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(date, scenario)
                )
            """)

            # Tabla de comparaciones directas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id INTEGER,

                    -- Query comparada (mismo input en ambos escenarios)
                    query_hash TEXT NOT NULL,

                    -- Escenario A
                    scenario_a TEXT NOT NULL,
                    query_id_a INTEGER,
                    tokens_a INTEGER,
                    latency_ms_a REAL,
                    cost_usd_a REAL,
                    precision_a REAL,

                    -- Escenario B
                    scenario_b TEXT NOT NULL,
                    query_id_b INTEGER,
                    tokens_b INTEGER,
                    latency_ms_b REAL,
                    cost_usd_b REAL,
                    precision_b REAL,

                    -- Diferencias
                    tokens_diff INTEGER,
                    latency_diff_ms REAL,
                    cost_diff_usd REAL,
                    precision_diff REAL,

                    -- Ganador por criterio
                    winner_tokens TEXT,
                    winner_latency TEXT,
                    winner_cost TEXT,
                    winner_precision TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                )
            """)

            # Índices para búsquedas rápidas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_scenario ON queries(scenario)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_created ON queries(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_experiment ON queries(experiment_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_stats(date)")

            conn.commit()

    # =========================================================================
    # EXPERIMENTS
    # =========================================================================

    def create_experiment(self, name: str, description: str = None, config: dict = None) -> int:
        """Crea un nuevo experimento y retorna su ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO experiments (name, description, config_snapshot) VALUES (?, ?, ?)",
                (name, description, json.dumps(config) if config else None)
            )
            conn.commit()
            return cursor.lastrowid

    def get_experiment(self, experiment_id: int) -> Optional[Dict]:
        """Obtiene un experimento por ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # =========================================================================
    # QUERIES
    # =========================================================================

    def record_query(
        self,
        scenario: str,
        mode: str,
        llm_provider: str,
        llm_model: str,
        query_hash: str,
        query_length: int,
        obra_social: Optional[str] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        latency_embedding_ms: float = 0,
        latency_faiss_ms: float = 0,
        latency_llm_ms: float = 0,
        cost_input: float = 0,
        cost_output: float = 0,
        entity_detected: str = None,
        entity_type: str = None,
        entity_confidence: str = None,
        llm_skipped: bool = False,
        rag_used: bool = False,
        rag_chunks_count: int = 0,
        rag_top_similarity: float = 0,
        response_length: int = 0,
        response_words: int = 0,
        success: bool = True,
        error_message: str = None,
        user_id: str = None,
        experiment_id: int = None
    ) -> int:
        """Registra una query con todas sus métricas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            tokens_total = tokens_input + tokens_output
            cost_total = cost_input + cost_output
            latency_total = latency_embedding_ms + latency_faiss_ms + latency_llm_ms

            cursor.execute("""
                INSERT INTO queries (
                    experiment_id, scenario, mode, llm_provider, llm_model,
                    query_hash, query_length, obra_social,
                    tokens_input, tokens_output, tokens_total,
                    latency_embedding_ms, latency_faiss_ms, latency_llm_ms, latency_total_ms,
                    cost_input, cost_output, cost_total,
                    entity_detected, entity_type, entity_confidence, llm_skipped,
                    rag_used, rag_chunks_count, rag_top_similarity,
                    response_length, response_words,
                    success, error_message, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id, scenario, mode, llm_provider, llm_model,
                query_hash, query_length, obra_social,
                tokens_input, tokens_output, tokens_total,
                latency_embedding_ms, latency_faiss_ms, latency_llm_ms, latency_total,
                cost_input, cost_output, cost_total,
                entity_detected, entity_type, entity_confidence, 1 if llm_skipped else 0,
                1 if rag_used else 0, rag_chunks_count, rag_top_similarity,
                response_length, response_words,
                1 if success else 0, error_message, user_id
            ))

            conn.commit()
            return cursor.lastrowid

    # =========================================================================
    # EVALUATIONS
    # =========================================================================

    def record_evaluation(
        self,
        query_id: int,
        precision_score: float,
        completitud_score: float,
        concision_score: float,
        hallucination_detected: bool = False,
        terms_found: List[str] = None,
        terms_missing: List[str] = None
    ) -> int:
        """Registra una evaluación de calidad"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            total_score = (precision_score + completitud_score + concision_score) / 3
            passed = total_score >= 70

            cursor.execute("""
                INSERT INTO evaluations (
                    query_id, precision_score, completitud_score, concision_score,
                    hallucination_detected, terms_found, terms_missing,
                    total_score, passed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id, precision_score, completitud_score, concision_score,
                1 if hallucination_detected else 0,
                json.dumps(terms_found) if terms_found else None,
                json.dumps(terms_missing) if terms_missing else None,
                total_score, 1 if passed else 0
            ))

            conn.commit()
            return cursor.lastrowid

    # =========================================================================
    # COMPARISONS
    # =========================================================================

    def record_comparison(
        self,
        query_hash: str,
        scenario_a: str,
        query_id_a: int,
        metrics_a: Dict,
        scenario_b: str,
        query_id_b: int,
        metrics_b: Dict,
        experiment_id: int = None
    ) -> int:
        """Registra una comparación directa entre dos escenarios"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Calcular diferencias
            tokens_diff = metrics_a.get('tokens', 0) - metrics_b.get('tokens', 0)
            latency_diff = metrics_a.get('latency_ms', 0) - metrics_b.get('latency_ms', 0)
            cost_diff = metrics_a.get('cost_usd', 0) - metrics_b.get('cost_usd', 0)
            precision_diff = metrics_a.get('precision', 0) - metrics_b.get('precision', 0)

            # Determinar ganadores (menor es mejor para tokens/latency/cost, mayor para precision)
            winner_tokens = scenario_a if metrics_a.get('tokens', 0) < metrics_b.get('tokens', 0) else scenario_b
            winner_latency = scenario_a if metrics_a.get('latency_ms', 0) < metrics_b.get('latency_ms', 0) else scenario_b
            winner_cost = scenario_a if metrics_a.get('cost_usd', 0) < metrics_b.get('cost_usd', 0) else scenario_b
            winner_precision = scenario_a if metrics_a.get('precision', 0) > metrics_b.get('precision', 0) else scenario_b

            cursor.execute("""
                INSERT INTO comparisons (
                    experiment_id, query_hash,
                    scenario_a, query_id_a, tokens_a, latency_ms_a, cost_usd_a, precision_a,
                    scenario_b, query_id_b, tokens_b, latency_ms_b, cost_usd_b, precision_b,
                    tokens_diff, latency_diff_ms, cost_diff_usd, precision_diff,
                    winner_tokens, winner_latency, winner_cost, winner_precision
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id, query_hash,
                scenario_a, query_id_a,
                metrics_a.get('tokens'), metrics_a.get('latency_ms'),
                metrics_a.get('cost_usd'), metrics_a.get('precision'),
                scenario_b, query_id_b,
                metrics_b.get('tokens'), metrics_b.get('latency_ms'),
                metrics_b.get('cost_usd'), metrics_b.get('precision'),
                tokens_diff, latency_diff, cost_diff, precision_diff,
                winner_tokens, winner_latency, winner_cost, winner_precision
            ))

            conn.commit()
            return cursor.lastrowid

    # =========================================================================
    # REPORTS
    # =========================================================================

    def get_scenario_stats(self, scenario: str, days: int = 7) -> Dict:
        """Obtiene estadísticas agregadas de un escenario"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_queries,
                    SUM(success) as successful,
                    AVG(tokens_total) as avg_tokens,
                    AVG(latency_total_ms) as avg_latency_ms,
                    AVG(cost_total) as avg_cost_usd,
                    MIN(latency_total_ms) as min_latency_ms,
                    MAX(latency_total_ms) as max_latency_ms,
                    SUM(cost_total) as total_cost_usd
                FROM queries
                WHERE scenario = ?
                AND created_at >= datetime('now', ?)
            """, (scenario, f'-{days} days'))

            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_comparison_summary(self, experiment_id: int = None) -> List[Dict]:
        """Obtiene resumen de comparaciones"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    scenario_a,
                    scenario_b,
                    COUNT(*) as comparisons,
                    AVG(tokens_diff) as avg_tokens_diff,
                    AVG(latency_diff_ms) as avg_latency_diff,
                    AVG(cost_diff_usd) as avg_cost_diff,
                    SUM(CASE WHEN winner_latency = scenario_a THEN 1 ELSE 0 END) as wins_latency_a,
                    SUM(CASE WHEN winner_cost = scenario_a THEN 1 ELSE 0 END) as wins_cost_a,
                    SUM(CASE WHEN winner_precision = scenario_a THEN 1 ELSE 0 END) as wins_precision_a
                FROM comparisons
            """

            if experiment_id:
                query += " WHERE experiment_id = ?"
                cursor.execute(query + " GROUP BY scenario_a, scenario_b", (experiment_id,))
            else:
                cursor.execute(query + " GROUP BY scenario_a, scenario_b")

            return [dict(row) for row in cursor.fetchall()]

    def export_to_json(self, filepath: str, experiment_id: int = None):
        """Exporta métricas a JSON para análisis externo"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Queries
            if experiment_id:
                cursor.execute("SELECT * FROM queries WHERE experiment_id = ?", (experiment_id,))
            else:
                cursor.execute("SELECT * FROM queries")
            queries = [dict(row) for row in cursor.fetchall()]

            # Comparisons
            if experiment_id:
                cursor.execute("SELECT * FROM comparisons WHERE experiment_id = ?", (experiment_id,))
            else:
                cursor.execute("SELECT * FROM comparisons")
            comparisons = [dict(row) for row in cursor.fetchall()]

            data = {
                "exported_at": datetime.now().isoformat(),
                "queries": queries,
                "comparisons": comparisons,
                "summary": self.get_comparison_summary(experiment_id)
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
