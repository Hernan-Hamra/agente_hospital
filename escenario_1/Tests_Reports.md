# Tests y Reportes - Escenario 1

## Batería de Tests

| Nivel | Test | Preguntas | Consume API | Propósito |
|-------|------|-----------|-------------|-----------|
| Básico | Unitarios | 53 | No | Validar componentes individuales |
| Básico | RAG 50 | 50 | No | Validar retrieval sin LLM |
| Básico | Integración | 1 | Sí (Groq) | Validar pipeline E2E completo |
| Completo | Evaluación | 20 | Sí (Groq) | Reporte exhaustivo con métricas |

**Tests básicos:** Unitarios + RAG 50 + Integración = validación rápida del sistema
**Test completo:** Evaluación 20 preguntas = reporte detallado para análisis

---

## Tests Disponibles

### 1. Unitarios (53 tests) - No consume API
```bash
python escenario_1/tests/run_all.py
```
**Componentes testeados:**
- entity_detector (23): Detección de obras sociales en texto
- query_rewriter (18): Expansión y reescritura de queries
- retriever (12): Búsqueda en ChromaDB con filtros

**Métricas:** passed/failed por módulo

---

### 2. RAG 50 (50 preguntas) - No consume API
```bash
python escenario_1/tests/test_rag_50.py
```
**Cobertura:**
- ASI: 12 preguntas (contactos, protocolos)
- ENSALUD: 23 preguntas (coseguros, planes, contactos)
- IOSFA: 7 preguntas (documentación, requisitos)
- GRUPO_PEDIATRICO: 8 preguntas (PMI, exenciones)

**Métricas:** % acierto por categoría, % acierto por obra social, similarity score

---

### 3. Evaluación (20 preguntas) - Consume Groq
```bash
python escenario_1/evaluate.py
```
**Pipeline:** query → entity → RAG → LLM → respuesta

**Métricas:**
- tokens_input, tokens_output por query
- latencia RAG (ms), latencia LLM (ms), latencia total
- % respuestas correctas
- límites Groq calculados

---

### 4. Integración (1 test E2E) - Consume Groq
```bash
python escenario_1/tests/test_integracion.py
```
**Pipeline:** query → entity → RAG → LLM → respuesta + evaluación

**Métricas (puntaje /100):**
- Completitud (40 pts): términos esperados encontrados
- Sin errores (20 pts): ausencia de términos prohibidos
- Brevedad (20 pts): respuesta dentro de límite de palabras
- Uso RAG (10 pts): uso correcto del contexto
- Velocidad (10 pts): tiempo de respuesta

---

## Reportes Generados

| Reporte                            | Test        | Contenido principal |
|----------------------------------  |----------- -|---------------------|
| `reporte_unitarios_{fecha}.json`   | Unitarios   | passed/failed por módulo |
| `reporte_rag50_{fecha}.json`       | RAG 50      | % acierto por categoría y obra social |
| `reporte_evaluacion_{fecha}.json`  | Evaluación  | tokens, latencias, % correctas |
| `reporte_integracion_{fecha}.json` | Integración | puntaje detallado por criterio |

---

## Límites Groq (Plan Free)

| Límite | Valor | Impacto |
|--------|-------|---------|
| Tokens/día | 100,000 | **125 queries/día** (a 800 tokens/query) |
| Tokens/minuto | 12,000 | 15 queries/minuto |
| Requests/día | 1,000 | No limitante |
| Delay recomendado | 4 seg | Entre queries |
