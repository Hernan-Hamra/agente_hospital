# Agente Hospitalario - Grupo Pediátrico

## Claude Rules

### Restricciones
NO sin permiso: refactorizar, renombrar, mover archivos, cambiar lógica, optimizar, eliminar código.

### Permitido
Explicar, detectar errores (sin corregir), escribir código SOLO si se pide.

### Plan obligatorio antes de cambios
```
1. archivo1.py - cambio A
2. archivo2.py - cambio B (depende 1)
¿Proceder?
```

---

## Stack
FastAPI + Ollama (llama3.2:3b) + FAISS + sentence-transformers/all-MiniLM-L6-v2

---

## Config Crítica

**Indexer** (`app/rag/indexer.py:50,72`)
```python
chunk_size = 1000
chunk_overlap = 50
```

**Retriever** (`app/rag/retriever.py`)
```python
# L39: Normaliza query embedding
faiss.normalize_L2(query_embedding)

# L59: Convierte inner product → cosine similarity (0-1)
similarity = (distance + 1.0) / 2.0

# L64: Threshold RAG - descarta chunks irrelevantes
if similarity < 0.65:  # 0.65=moderado, 0.8+=muy similar
    continue
```

**Entity Extractor** (`app/rag/entity_extractor.py`)
```python
# L13: 9 obras sociales (ENSALUD, ASI, IOSFA + 6)

# L114-115: Fuzzy matching typos
if similarity > 0.8:  # Tolera errores ortográficos
    return value, similarity * 0.8
```

**Embeddings**
- Modelo: sentence-transformers/all-MiniLM-L6-v2
- Dim: 384
- Normalización: L2 (para cosine similarity)

**FAISS**
- IndexFlatIP: Inner Product con embeddings normalizados = cosine similarity
- Rango: -1 (opuestos) a +1 (idénticos)
- Búsqueda exacta, no aproximada

---

## Archivos Críticos

```
backend/app/
├── main.py                    # API endpoints
├── rag/
│   ├── entity_extractor.py    # L13: OBRAS_SOCIALES
│   ├── retriever.py           # L62: threshold
│   └── indexer.py             # L50: chunk_size
└── llm/client.py              # System prompt

scripts/index_data.py          # Reindexar
```

---

## Problemas Activos
1. LLM alucina (llama3.2:3b pequeño)
2. Sin memoria conversacional
3. Lento (1:53 min/query)
