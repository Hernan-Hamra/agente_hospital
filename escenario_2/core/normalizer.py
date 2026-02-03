"""
Normalizador de input del usuario.

Usa la tabla de sinónimos para convertir:
- "internado" → "internacion"
- "ensalud" → "ENSALUD"
- "pediatra" → "consulta_pediatra"
"""
import sqlite3
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NormalizedQuery:
    """Resultado de la normalización."""
    obra_social: Optional[str] = None
    tipo_ingreso: Optional[str] = None
    prestacion: Optional[str] = None
    raw_text: str = ""

    @property
    def is_valid(self) -> bool:
        """Una query es válida si tiene obra_social Y tipo_ingreso."""
        return self.obra_social is not None and self.tipo_ingreso is not None

    def to_dict(self) -> Dict:
        return {
            "obra_social": self.obra_social,
            "tipo_ingreso": self.tipo_ingreso,
            "prestacion": self.prestacion,
            "is_valid": self.is_valid
        }


class Normalizer:
    """
    Normaliza el input del usuario usando sinónimos de la DB.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._load_sinonimos()

    def _load_sinonimos(self):
        """Carga todos los sinónimos en memoria para búsqueda rápida."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT palabra, categoria, valor_normalizado FROM sinonimos")

        self.sinonimos = {
            "obra_social": {},
            "tipo_ingreso": {},
            "prestacion": {}
        }

        for palabra, categoria, valor in cursor.fetchall():
            self.sinonimos[categoria][palabra.lower()] = valor

    def normalize(self, text: str) -> NormalizedQuery:
        """
        Normaliza un texto de usuario.

        Args:
            text: Texto libre del usuario (ej: "internación ensalud")

        Returns:
            NormalizedQuery con los valores detectados
        """
        result = NormalizedQuery(raw_text=text)

        # Limpiar y tokenizar
        text_lower = text.lower()
        # Remover puntuación pero mantener espacios
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        words = text_clean.split()

        # Buscar matches en cada categoría
        for word in words:
            # Buscar obra social
            if word in self.sinonimos["obra_social"]:
                result.obra_social = self.sinonimos["obra_social"][word]

            # Buscar tipo de ingreso
            if word in self.sinonimos["tipo_ingreso"]:
                result.tipo_ingreso = self.sinonimos["tipo_ingreso"][word]

            # Buscar prestación
            if word in self.sinonimos["prestacion"]:
                result.prestacion = self.sinonimos["prestacion"][word]

        # También buscar frases de 2 palabras (ej: "asi salud", "en salud")
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"

            if phrase in self.sinonimos["obra_social"]:
                result.obra_social = self.sinonimos["obra_social"][phrase]

        return result

    def add_sinonimo(self, palabra: str, categoria: str, valor: str):
        """Agrega un nuevo sinónimo a la DB y al cache."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO sinonimos (palabra, categoria, valor_normalizado)
            VALUES (?, ?, ?)
        """, (palabra.lower(), categoria, valor))
        self.conn.commit()

        # Actualizar cache
        self.sinonimos[categoria][palabra.lower()] = valor


def get_normalizer(db_path: str = None) -> Normalizer:
    """Factory function para obtener el normalizador."""
    from pathlib import Path

    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "obras_sociales.db"

    conn = sqlite3.connect(db_path)
    return Normalizer(conn)
