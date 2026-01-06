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

**LLM**: Ollama qwen2.5:3b (function calling)
**RAG**: FAISS + sentence-transformers/all-MiniLM-L6-v2
**Backend**: FastAPI
**Bot**: python-telegram-bot (memoria conversacional)
**Agente**: Function calling con tool consulta_rag

---

## Agente con Function Calling

**Archivo**: `backend/app/llm/client.py`

**Método**: `generate_response_agent(query, historial, rag_callback)`

**Herramienta disponible**:
```python
consulta_rag(obra_social: str, query: str)
# Busca en documentos de ENSALUD/ASI/IOSFA
```

**Parámetros críticos** (L357-358, L398-399):
```python
# Primera llamada (sin RAG)
options={
    'temperature': 0.1,      # Muy determinista, menos alucinaciones
    'num_predict': 40        # Max 15 palabras (~3 tokens/palabra)
}

# Segunda llamada (post-RAG)
options={
    'temperature': 0.1,
    'num_predict': 50        # Max 20 palabras
}
```

**System Prompt** (L292-329):
- MÁXIMO 15 PALABRAS por respuesta
- SI NO SABÉS → USA consulta_rag OBLIGATORIO
- NUNCA inventes copagos, montos, especialidades
- Si RAG vacío → "No tengo esa info. ¿Algo más?"

**Protocolo básico (conocimiento built-in)**:
```
Guardia: DNI + credencial (NO orden)
Turno: orden + DNI + credencial
Internación: orden autorizada + presupuesto
```

**Obras sociales cargadas**: ENSALUD, ASI, IOSFA
Si preguntan por otra → "No tengo [X]. Solo ENSALUD/ASI/IOSFA"

---

## RAG Config

**Indexer** (`app/rag/indexer.py:50,72`)
```python
chunk_size = 1000
chunk_overlap = 100  # Actualizado de 50
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
# L13: Obras sociales (ENSALUD, ASI, IOSFA + otras)

# L116-117: Fuzzy matching typos
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

## Telegram Bot

**Archivo**: `telegram_bot.py`

**Memoria conversacional**:
```python
from collections import deque
conversation_history = defaultdict(lambda: deque(maxlen=10))
```

**Payload al backend** (L67-71):
```python
payload = {
    "pregunta": user_message,
    "obra_social": None,
    "historial": list(conversation_history[chat_id]),
    "use_agent": True  # OBLIGATORIO para modo agente
}
```

---

## Archivos Críticos

```
backend/app/
├── main.py                    # L215-265: Endpoint /query con rag_callback
├── models.py                  # L19: use_agent field
├── rag/
│   ├── entity_extractor.py    # L13: OBRAS_SOCIALES
│   ├── retriever.py           # L64: threshold cosine
│   └── indexer.py             # L50: chunk_size
└── llm/client.py              # L276-421: Agente function calling

telegram_bot.py                # L67: use_agent: True
scripts/index_data.py          # Reindexar FAISS
```

---

## Problemas Resueltos

### ✅ Alucinaciones
**Antes**: Inventaba copagos, especialidades, montos
**Solución**:
- System prompt: "NUNCA inventes"
- Temperature 0.1
- num_predict 40
- Si RAG vacío → "No tengo esa info"

### ✅ Respuestas largas cortadas
**Antes**: 400+ caracteres, texto se cortaba
**Solución**: Límite 15 palabras, num_predict 40

### ✅ Confusión guardia/turno
**Antes**: Decía "orden" para guardia
**Solución**: Prompt explícito "Guardia: NO orden"

### ✅ Invención de obras sociales
**Antes**: Respondía sobre OSDE sin tenerla
**Solución**: Lista explícita + mensaje error

### ✅ Sin memoria conversacional
**Antes**: Cada mensaje sin contexto
**Solución**: Deque(maxlen=10) + historial en request

### ✅ Lento (1:53 min/query)
**Antes**: llama3.2 muy lento
**Ahora**: qwen2.5:3b → 30-40s queries simples

---

## Datos

**Ubicación**: `data/obras_sociales/`
```
ensalud/*.docx
asi/2024-01-04_normas.docx
iosfa/*.docx
```

**IMPORTANTE**: Documentos NO contienen info sobre copagos específicos por especialidad. Si agente dice montos/especialidades → está ALUCINANDO.

**FAISS Index**: `backend/faiss_index/`

---

## Variables de Entorno

`backend/.env`:
```env
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
TOP_K_RESULTS=5
```

---

## Comandos

```bash
# Backend
cd backend && source venv/bin/activate
python3 -m uvicorn app.main:app --reload

# Bot
python3 telegram_bot.py

# Reindexar
python scripts/index_data.py

# Test
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "protocolo básico", "use_agent": true}'
```

---

## Debugging

### Ver tool calls
Buscar en logs backend:
```
🔧 Tool call: consulta_rag({'obra_social': 'ASI', 'query': '...'})
📚 Ejecutando RAG: ...
```

### Ver respuestas largas
```
📝 Longitud de respuesta: 307 caracteres  ← MAL (debe ser < 100)
```

### Verificar modelo
```bash
grep OLLAMA_MODEL backend/.env
# Debe ser: qwen2.5:3b
```

---

## Métricas de Éxito

- ✅ Respuestas < 15 palabras (< 100 chars)
- ✅ NO inventa obras sociales/copagos
- ✅ Llama RAG cuando necesita info
- ✅ "No tengo esa info" si RAG vacío
- ✅ Memoria conversacional (10 msgs)
- ✅ < 40s queries simples, < 100s con RAG
