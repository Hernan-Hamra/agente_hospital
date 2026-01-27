# Guía de Desarrollo de Bots RAG

## Proceso de Desarrollo y Testing

Este documento describe el proceso sistemático para desarrollar, probar y evaluar bots basados en RAG.

---

## 1. Pipeline del Bot

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  ENTITY          │───>│  RAG             │───>│  LLM             │
│  DETECTION       │    │  RETRIEVAL       │    │  RESPONSE        │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

### Etapa 1: Entity Detection
- **Propósito**: Identificar entidades en la query (obra social, institución, etc.)
- **Componentes**: `detector.py`, `entities.yaml`
- **Output**: `EntityResult` con entidad detectada y filtro RAG

### Etapa 2: Query Rewriting + RAG Retrieval
- **Propósito**: Expandir query y recuperar chunks relevantes
- **Componentes**: `query_rewriter.py`, `retriever.py`, `indexer.py`
- **Output**: Lista de chunks con texto, metadata y similarity score

### Etapa 3: LLM Response
- **Propósito**: Generar respuesta basada en contexto RAG
- **Componentes**: `consulta_router.py`, `client_v2.py`
- **Output**: Respuesta final al usuario

---

## 2. Estructura de Tests por Etapa

### Tests Unitarios (sin dependencias externas)
```
tests/unit/
├── test_entity_detector.py    # Etapa 1
├── test_query_rewriter.py     # Etapa 2 (rewriting)
└── test_chunking.py           # Etapa 2 (chunking)
```

### Tests de Integración (requieren índice FAISS)
```
tests/integration/
└── test_rag_retrieval.py      # Etapa 2 (retrieval)
```

### Tests E2E (requieren LLM activo)
```
scripts/run_scenario.py --batch  # Etapa 3 completa
```

---

## 3. Comandos de Testing

```bash
# 1. Tests unitarios (rápidos, <1s)
pytest tests/unit/ -v

# 2. Tests de integración (requieren índice, ~15s)
pytest tests/integration/ -v

# 3. Test completo (requiere LLM, ~3-5 min)
python scripts/run_scenario.py --batch --scenario groq_consulta

# 4. Todos los tests automatizados
pytest tests/unit/ tests/integration/ -v
```

---

## 4. Proceso de Debugging

### Problema: RAG no encuentra chunks correctos

1. **Verificar datos en índice**:
```bash
python -c "
import pickle
with open('backend/faiss_index/documents.pkl', 'rb') as f:
    docs = pickle.load(f)
# Filtrar por obra social
for d in docs:
    if d.get('obra_social') == 'NOMBRE':
        print(d.get('chunk_id'), d.get('text')[:100])
"
```

2. **Verificar query rewriting**:
```bash
python -c "
from backend.app.rag.query_rewriter import rewrite_query
print(rewrite_query('tu query aquí', 'OBRA_SOCIAL'))
"
```

3. **Verificar retrieval directo**:
```bash
python -c "
from backend.app.rag.indexer import DocumentIndexer
from backend.app.rag.retriever import DocumentRetriever
indexer = DocumentIndexer(embedding_model='BAAI/bge-large-en-v1.5')
indexer.load_index('backend/faiss_index')
retriever = DocumentRetriever(indexer, embedding_model='BAAI/bge-large-en-v1.5')
results = retriever.retrieve('tu query', top_k=5, obra_social_filter='NOMBRE')
for text, meta, score in results:
    print(f'{meta[\"chunk_id\"]} ({score:.3f}): {text[:100]}')
"
```

### Problema: Entity detection falla

1. **Verificar normalización**:
```python
from backend.app.entities.detector import EntityDetector
d = EntityDetector()
result = d.detect("tu query con ENTIDAD?")
print(result.to_dict())
```

2. **Verificar aliases en config**:
```bash
cat config/entities.yaml
```

---

## 5. Agregar Nueva Obra Social

### Paso 1: Preparar documentos
```
data/obras_sociales_docs/nueva_os/
├── documento1.pdf
├── documento2.docx
└── ...
```

### Paso 2: Procesar a chunks
```bash
python backend/scripts/convert_docs_to_json_flat.py
```

### Paso 3: Reindexar FAISS
```bash
python scripts/reindex_faiss.py
```

### Paso 4: Agregar a entities.yaml
```yaml
entities:
  NUEVA_OS:
    canonical: "NUEVA_OS"
    type: "obra_social"
    rag_filter: "NUEVA_OS"
    aliases:
      - "nueva os"
      - "nuevaos"
```

### Paso 5: Actualizar tests
```bash
# Actualizar conteos en test_rag_retrieval.py
# Agregar casos de prueba para nueva OS
```

### Paso 6: Verificar
```bash
pytest tests/integration/test_rag_retrieval.py -v
python scripts/run_scenario.py --query "consulta NUEVA_OS" --scenario groq_consulta
```

---

## 6. Crear Nuevo Escenario

### Paso 1: Definir en scenarios.yaml
```yaml
scenarios:
  nuevo_escenario:
    name: "Nombre descriptivo"
    enabled: true
    llm:
      provider: "groq"  # o "ollama"
      model: "modelo-a-usar"
      parameters:
        temperature: 0.1
        max_tokens: 150
    mode:
      type: "consulta"  # o "agente"
      use_history: false
    prompt:
      system: "Prompt del sistema..."
```

### Paso 2: Crear archivo de queries de prueba
```json
// data/test_queries_escenario_nuevo.json
{
  "escenario": "Nombre del escenario",
  "queries": [
    {"id": 1, "query": "...", "obra_social": "...", "respuesta_esperada": "..."}
  ]
}
```

### Paso 3: Ejecutar evaluación
```bash
python scripts/run_scenario.py --batch --scenario nuevo_escenario \
    --queries-file data/test_queries_escenario_nuevo.json
```

---

## 7. Métricas de Evaluación

### Por Query
- **Tokens**: input, output, total
- **Latencia**: embedding, FAISS, LLM, total
- **Similarity**: top similarity del RAG
- **Match**: términos esperados vs obtenidos

### Por Escenario
- **Precisión**: % queries correctas
- **Costo**: USD total (Groq FREE = $0)
- **Latencia promedio**: ms por query

### Umbrales de Aceptación
```yaml
evaluation:
  thresholds:
    min_precision: 0.70      # 70% queries correctas
    max_latency_ms: 5000     # 5 segundos cloud
    max_latency_ms_local: 30000  # 30 segundos local
    max_words: 50            # Respuestas concisas
```

---

## 8. Checklist Pre-Producción

- [ ] Tests unitarios pasan (78+ tests)
- [ ] Tests de integración pasan (índice correcto)
- [ ] Test de 20 preguntas con >70% precisión
- [ ] Entity detection funciona con puntuación
- [ ] Query rewriter expande queries con tildes
- [ ] Costos dentro del presupuesto
- [ ] Latencia aceptable (<5s cloud, <30s local)
- [ ] Documentación actualizada

---

## 9. Archivos Clave

```
backend/
├── app/
│   ├── entities/detector.py      # Entity detection
│   ├── rag/
│   │   ├── query_rewriter.py     # Query expansion
│   │   ├── retriever.py          # FAISS retrieval
│   │   └── indexer.py            # FAISS indexing
│   └── scenarios/
│       └── consulta_router.py    # Pipeline principal
├── faiss_index/                  # Índice FAISS
│   ├── index.faiss
│   └── documents.pkl

config/
├── entities.yaml                 # Entidades y aliases
└── scenarios.yaml                # Configuración de escenarios

tests/
├── unit/                         # Tests sin dependencias
└── integration/                  # Tests con índice

scripts/
├── run_scenario.py               # Runner de escenarios
└── evaluate_rag_50.py            # Diagnóstico RAG
```
