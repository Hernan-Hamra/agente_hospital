"""Core modules for Escenario 2."""
from .normalizer import Normalizer, NormalizedQuery, get_normalizer
from .query_engine import QueryEngine, QueryResult

__all__ = [
    "Normalizer",
    "NormalizedQuery",
    "get_normalizer",
    "QueryEngine",
    "QueryResult"
]
