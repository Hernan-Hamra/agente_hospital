# Estrategia de Tests - Agente Hospitalario

## Pipeline del Bot (3 Etapas)

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  1. ENTITY       │───>│  2. RAG          │───>│  3. LLM          │
│     DETECTION    │    │     RETRIEVAL    │    │     RESPONSE     │
└──────────────────┘    └──────────────────┘    └──────────────────┘
     detector.py            retriever.py          consulta_router.py
     query_rewriter.py      indexer.py            client_v2.py
```

---

## Etapa 1: Entity Detection

### Componentes
- `backend/app/entities/detector.py` - Detección de obra social (ASI, ENSALUD, IOSFA, GRUPO_PEDIATRICO)
- `backend/app/rag/query_rewriter.py` - Expansión de queries con sinónimos

### Tests Actuales (Creados 2026-01-22)
| Archivo | Estado | Tests |
|---------|--------|-------|
| `tests/unit/test_entity_detector.py` | ✅ NUEVO | 23 tests |
| `tests/unit/test_query_rewriter.py` | ✅ NUEVO | 23 tests |

### Estructura de Tests
```
tests/unit/test_entity_detector.py (23 tests)
├── TestEntityDetectionCanonical (4) - ASI, ENSALUD, IOSFA, GRUPO_PEDIATRICO
├── TestEntityDetectionAliases (3) - lowercase, mixed case, aliases
├── TestEntityDetectionWithPunctuation (4) - ¿?, ¡!, comas, paréntesis
├── TestNoEntityDetection (3) - saludos, preguntas generales
├── TestEdgeCases (4) - "básica", múltiples entidades, vacío
├── TestEntityResultDataclass (3) - to_dict, tipos
└── TestRagFilter (2) - filtros RAG

tests/unit/test_query_rewriter.py (23 tests)
├── TestNormalization (3) - tildes, lowercase
├── TestQueryExpansion (6) - cuánto/cuanto, coseguros, médicos
├── TestNoExpansion (2) - patrones desconocidos
├── TestObraSocialContext (4) - ENSALUD, ASI, IOSFA, duplicados
├── TestQueryVariations (2) - variaciones de query
├── TestCriticalQueries (3) - queries que fallaban antes
└── TestEdgeCases (3) - vacío, None, desconocido
```

### Problemas Corregidos
- ✅ **FIX**: Query rewriter ahora normaliza tildes ("cuánto" → "cuanto" para matching)
- ✅ **FIX**: Entity detector maneja puntuación ("ENSALUD?" → ENSALUD)

---

## Etapa 2: RAG Retrieval

### Componentes
- `backend/app/rag/indexer.py` - Indexación FAISS
- `backend/app/rag/retriever.py` - Búsqueda semántica
- `backend/scripts/convert_docs_to_json_flat.py` - Chunking

### Tests Actuales
| Archivo | Estado | Notas |
|---------|--------|-------|
| `tests/unit/test_chunking.py` | ⚠️ 14/15 | 1 fallo por cambio en tablas de contacto |
| `tests/integration/test_rag_retrieval.py` | ⚠️ 11/15 | 4 fallos por cambios en índice |
| `scripts/evaluate_rag_50.py` | ✅ | Manual, 50 queries exhaustivas |
| `scripts/evaluate_rag_quality.py` | ✅ | Manual, 28 queries diagnósticas |

### Tests a Actualizar
```
tests/unit/test_chunking.py
└── TestTableToText::test_simple_table_conversion
    # ACTUALIZAR: Las tablas de contacto ahora son oraciones
    # Antes: assert "TABLA #1" in texto
    # Ahora: assert "El mail de" in texto

tests/integration/test_rag_retrieval.py
└── TestIndexIntegrity
    # ACTUALIZAR: Nuevos conteos de chunks
    # - Total: 82 → 92
    # - ASI: 13 → 14
    # - IOSFA: 1 → 2
    # - ENSALUD: 68 → 69
    # - GRUPO_PEDIATRICO: 0 → 7
```

### Problemas Conocidos
- **CRÍTICO**: RAG no encuentra bien valores en tablas de coseguros
- **CAUSA**: Query rewriter no normaliza tildes

---

## Etapa 3: LLM Response

### Componentes
- `backend/app/scenarios/consulta_router.py` - Router principal
- `backend/app/llm/client_v2.py` - Cliente LLM (Groq/Ollama)

### Tests Actuales
| Archivo | Estado | Notas |
|---------|--------|-------|
| `tests/system/test_evaluation.py` | ⚠️ NO CORRER | Requiere LLM activo |
| `scripts/evaluate_bot.py` | ⚠️ 5 casos | Duplicado de test_evaluation |
| `scripts/evaluate_conversational_bot.py` | ✅ | 30 casos conversacionales |
| `scripts/run_scenario.py --batch` | ✅ | 20 preguntas Escenario 1 |

### Tests Necesarios
```
tests/unit/test_consulta_router.py
├── TestConsultaRouter
│   ├── test_no_entity_returns_fixed_message (mock detector)
│   ├── test_with_entity_calls_rag (mock retriever)
│   └── test_llm_response_format (mock llm)
```

---

## Matriz de Cobertura Actual (Actualizada 2026-01-22)

| Etapa | Unit Tests | Integration | E2E | Estado |
|-------|------------|-------------|-----|--------|
| Entity Detection | **23** | 0 | 20 | ✅ COMPLETO |
| Query Rewriter | **23** | 0 | - | ✅ NUEVO |
| RAG Retrieval | 16 | **16** | 78 (manual) | ✅ ACTUALIZADO |
| LLM Response | 0 | 0 | 20 | ⚠️ E2E ONLY |

**Total: 78 tests automatizados pasando**

---

## Organización Propuesta de Archivos

```
tests/
├── unit/
│   ├── test_chunking.py          # ✅ Existente (actualizar 1 test)
│   ├── test_entity_detector.py   # 🆕 CREAR
│   ├── test_query_rewriter.py    # 🆕 CREAR
│   └── test_consulta_router.py   # 🆕 CREAR (con mocks)
│
├── integration/
│   ├── test_rag_retrieval.py     # ✅ Existente (actualizar conteos)
│   └── test_rag_quality.py       # 🆕 MOVER desde scripts/
│
└── e2e/
    ├── test_escenario1_groq.py   # 🆕 CREAR (20 preguntas)
    └── test_escenarios.py        # 🆕 CREAR (parametrizado)

scripts/
├── evaluate_rag_50.py            # Mantener como diagnóstico manual
└── run_scenario.py               # Mantener como runner de escenarios
```

---

## Archivos a Eliminar/Deprecar

| Archivo | Acción | Razón |
|---------|--------|-------|
| `scripts/evaluate_bot.py` | DEPRECAR | Duplicado de test_evaluation |
| `scripts/evaluate_conversational_bot.py` | EVALUAR | Modo agente (no usado) |
| `scripts/test_improvements.py` | INTEGRAR | Mover a tests/unit/ |
| `tests/system/test_evaluation.py` | MOVER | Mover a tests/e2e/ |

---

## Próximos Pasos

1. **URGENTE**: Corregir query_rewriter para normalizar tildes
2. **ALTO**: Crear tests unitarios de entity_detector
3. **MEDIO**: Actualizar conteos en test_rag_retrieval.py
4. **BAJO**: Reorganizar archivos de test

---

## Comandos de Ejecución

```bash
# Tests unitarios (rápidos, sin dependencias externas)
pytest tests/unit/ -v

# Tests de integración (requieren índice FAISS)
pytest tests/integration/ -v

# Tests e2e (requieren LLM + índice)
pytest tests/e2e/ -v --scenario groq_consulta

# Evaluación manual completa (20 preguntas)
python scripts/run_scenario.py --batch --scenario groq_consulta

# Diagnóstico RAG (50 preguntas)
python scripts/evaluate_rag_50.py
```
