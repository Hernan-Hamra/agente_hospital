# Mejoras RAG - Pendientes de Automatizar

## Estado Actual (2024-01)
- **Precisión RAG puro:** 100% (50/50 queries)
- **Cobertura con top_k=3:** 98% (49/50 queries)
- **Query rewriter:** Manual (diccionario de expansiones)

## Mejoras Implementadas

### 1. Keywords semánticas en tablas
**Archivo:** `backend/scripts/convert_docs_to_json_flat.py`
**Función:** `_detect_table_keywords()`

Agrega keywords al inicio de cada tabla para mejorar retrieval:
- Tablas con "$" → agrega "COSEGUROS VALORES PRECIOS TARIFAS"
- Tablas con "médico" → agrega "CONSULTA ESPECIALISTA"
- etc.

### 2. Query Rewriter
**Archivo:** `backend/app/rag/query_rewriter.py`

Expande queries coloquiales a términos técnicos:
- "pediatra" → "pediatra médico familia generalista"
- "quienes no pagan" → "exentos excluidos programas HIV oncología"
- "planes disponibles" → "planes Delta Krono Quantum..."

## Pendiente: Automatización

### Opción 1: LLM Query Expansion
```python
def expand_query_with_llm(query, obra_social):
    prompt = f"Reformula esta consulta médica agregando sinónimos: {query}"
    return groq.complete(prompt)
```
**Pro:** Flexible, no requiere mantenimiento
**Contra:** +1 llamada LLM, latencia, costo

### Opción 2: Word Embeddings
```python
from gensim.models import KeyedVectors
model = KeyedVectors.load("es_word2vec.bin")
synonyms = model.most_similar("pediatra", topn=5)
```
**Pro:** Rápido, offline
**Contra:** Requiere modelo español médico

### Opción 3: Tesauro médico
Usar SNOMED-CT o DeCS para expansión de términos médicos.

## Query problemática restante
- "coseguro imágenes alta complejidad" → rank 18
- Causa: T047 no tiene "imágenes alta complejidad" literal
- Solución: agregar "ALTA COMPLEJIDAD" como keyword en tablas con TAC/RMN
