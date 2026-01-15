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
**RAG**: FAISS + sentence-transformers/all-MiniLM-L6-v2 + cosine similarity
**Chunking**: Offline en 2 pasos (DOCX/PDF → JSON intermedio → JSON final)
**Backend**: FastAPI
**Bot**: n8n + Telegram (webhook HTTPS) O python-telegram-bot (polling)
**Agente**: Function calling con tool consulta_rag
**Túnel**: ngrok (para webhook mode)

---

## ⚙️ Configuración del LLM - NO modificar sin autorización

### Parámetros del bot por nivel de impacto

Esta tabla ordena TODOS los parámetros del bot por su impacto en el comportamiento.

| Parámetro | Impacto | Ubicación | Valor Actual | Qué Hace |
|-----------|---------|-----------|--------------|----------|
| **system_prompt** | 🔴 CRÍTICO | `backend/app/llm/client.py:73-118` | 40 líneas, 10 casos de uso | Define comportamiento completo del bot: saludos, despedidas, ambigüedad, brevedad, obras sociales |
| **user_prompt** | 🔴 CRÍTICO | `backend/app/llm/client.py:120-133` | Instrucciones por pregunta | Cómo usar contexto RAG, máximo palabras, terminar con pregunta |
| **historial** | 🔴 CRÍTICO | `scripts/evaluate_conversational_bot.py:697` | ACTIVADO | Mantiene memoria conversacional. Formato: `[{"role": "user/assistant", "content": "..."}]` |
| **pipeline_mode** | 🔴 CRÍTICO | `backend/app/main.py` | PIPELINE (RAG siempre) | PIPELINE: RAG ejecuta siempre. AGENTE: LLM decide si llamar RAG |
| **temperature** | 🟡 MEDIO | `backend/app/llm/client.py:172` | 0.1 | Control de creatividad. 0.0=determinista, 1.0=creativo. 0.1=muy preciso, menos alucinaciones |
| **num_predict** | 🟡 MEDIO | `backend/app/llm/client.py:171` | 120 tokens | Máximo de respuesta. 120 tokens ≈ 50 palabras. Cortar respuesta si muy larga |
| **num_ctx** | 🟡 MEDIO | `backend/app/llm/client.py:170` | 2048 tokens | Ventana contexto. Cuánto historial+RAG puede procesar. Más alto=más lento |
| **rag_top_k** | 🟡 MEDIO | `backend/app/rag/retriever.py` | 3 chunks | Cuántos chunks recupera RAG. Más chunks=más contexto pero más lento |
| **embedding_model** | 🟡 MEDIO | `backend/.env` | BAAI/bge-large-en-v1.5 | Modelo para embeddings. Afecta calidad de búsqueda RAG |
| **top_k** | 🟢 BAJO | `backend/app/llm/client.py:173` | 20 | Limita opciones de palabras. Menos opciones=más rápido, más determinista |
| **top_p** | 🟢 BAJO | `backend/app/llm/client.py:174` | 0.8 | Nucleus sampling. Corta cola de probabilidades. 0.8=conservador |
| **repeat_penalty** | 🟢 BAJO | `backend/app/llm/client.py:175` | 1.2 | Penaliza repeticiones. 1.0=sin penalidad, 1.2=evita repetir palabras |
| **num_thread** | 🟢 BAJO | `backend/app/llm/client.py:176` | 4 | Hilos CPU para paralelizar. Solo afecta velocidad, no comportamiento |
| **rag_filter** | 🟢 BAJO | `backend/app/rag/retriever.py` | obra_social si mencionada | Filtra chunks por obra social. Mejora precisión si obra social conocida |

**Estado actual del prompt (2026-01-14)**:
- 40 líneas (antes: 45 líneas)
- 10 casos de uso cubiertos:
  1. Saludos (solo primera vez, IGNORA contexto RAG)
  2. Despedidas
  3. Ambigüedad (repregunta)
  4. Fuera de scope (clima, deportes, noticias)
  5. Brevedad (máx 50 palabras)
  6. Múltiples obras sociales (pedir una a la vez)
  7. Cambio de tema (adaptarse sin confusión)
  8. Usuario incorrecto (corregir con amabilidad)
  9. Sobre el bot (explicar función)
  10. Pide humano (redirigir a bot primero)

**Cambios recientes (2026-01-14)**:
- ✅ Prompt optimizado: 45 → 40 líneas
- ✅ Agregada regla: En saludos → IGNORA contexto RAG
- ✅ Agregada regla: Fuera de scope → mensaje específico
- ✅ Prohibido inventar errores pasados ("confusiones anteriores")
- ✅ Solo disculparse si usuario corrige error REAL
- ✅ Brevedad aumentada: 40 → 50 palabras (para requisitos completos)

### Problemas detectados en última evaluación (2026-01-11 15:23)

1. **Saludo menciona ENSALUD sin que nadie lo pidiera** ✅ SOLUCIONADO
   - Causa: RAG recupera chunk de ENSALUD, LLM lo usa incorrectamente
   - Solución aplicada: Regla explícita "En saludos → IGNORA contexto RAG"

2. **Bot se disculpa por "confusiones anteriores" inexistentes** ✅ SOLUCIONADO
   - Causa: Historial mal interpretado
   - Solución aplicada: "Prohibido inventar errores pasados. Solo disculparse si usuario corrige error REAL"

3. **Pregunta del clima: respuesta inadecuada** ✅ SOLUCIONADO
   - Respuesta anterior: "Lo siento por las confusiones..."
   - Solución aplicada: Regla "FUERA DE SCOPE: Clima/deportes/noticias → 'Solo respondo enrolamiento del Grupo Pediátrico. ¿En qué puedo ayudarte?'"

4. **Tiempos LLM muy lentos**: 80s promedio (vs 1.8s anterior) ⏳ PENDIENTE
   - Causa: Historial activado + contexto largo
   - Impacto: Inaceptable para producción
   - Solución propuesta: Cambiar a modo agente (RAG como herramienta)

### Protocolo antes de modificar parámetros

1. ✅ Documentar valor actual en este archivo
2. ✅ Explicar razón del cambio
3. ✅ Ejecutar test corto: `python3 scripts/test_improvements.py` (3 preguntas, 2 min)
4. ✅ Si funciona → Ejecutar test completo: `python3 scripts/evaluate_conversational_bot.py` (30 preguntas, 15-20 min)
5. ✅ Comparar métricas antes/después
6. ✅ Documentar resultado

### Reportes de evaluación

Ubicación: `reports/conversational_evaluation_YYYY-MM-DD_HHMMSS.txt` y `.json`

**Último reporte**: `reports/conversational_evaluation_2026-01-11_144251.txt`
- 30 preguntas en 3 conversaciones
- Métricas: Precisión, Completitud, Concisión, Habilidades Conv., Performance
- Estado: 3/4 problemas SOLUCIONADOS con prompt optimizado (pendiente validar con test)

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
    'num_predict': 200       # Respuestas completas después de RAG (aumentado de 50)
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

**Pipeline de Chunking Offline (2 pasos)**:

1. **Paso 1**: `scripts/convert_docs_to_json.py`
   - DOCX/PDF → JSON intermedio (`*_chunks.json`)
   - Extrae texto, tablas, estructura

2. **Paso 2**: `scripts/clean_chunks_v2.py`
   - JSON intermedio → JSON final (`*_FINAL.json`)
   - Limpia, valida, estructura metadata
   - 1 chunk JSON = 1 embedding (sin chunking runtime)

**Indexer** (`app/rag/indexer.py`)
```python
# MIGRADO: Ya no procesa PDF/DOCX en runtime
# Ahora indexa directamente desde *_FINAL.json

def index_from_json(json_path):
    # Lee todos los *_FINAL.json
    # 1 chunk JSON = 1 embedding
    # Preserva tablas completas sin splitear
```

**Datos indexados**:
- ASI: 21 chunks
- ENSALUD: 1 chunk
- IOSFA: 3 chunks
- GRUPO_PEDIATRICO: Protocolo base (NO indexado en RAG, hardcoded en prompt)

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

## Telegram Integration

### Opción A: Bot Python directo (`telegram_bot.py`)

**Memoria conversacional**:
```python
from collections import deque
conversation_history = defaultdict(lambda: deque(maxlen=10))
```

**Payload al backend**:
```python
payload = {
    "pregunta": user_message,
    "obra_social": None,
    "historial": list(conversation_history[chat_id]),
    "use_agent": True  # OBLIGATORIO para modo agente
}
```

### Opción B: n8n + Telegram (Webhook Mode)

**Workflow**: `n8n/workflows/telegram_agente_hospital.json`

**Requisitos**:
- **ngrok**: Túnel HTTPS (Telegram requiere HTTPS para webhooks)
- **WEBHOOK_URL**: Variable de entorno para n8n

**Flujo**:
1. Telegram → ngrok (HTTPS) → n8n webhook
2. n8n → HTTP POST a `localhost:8000/query`
3. n8n → Envía respuesta a Telegram

**Setup**:
```bash
# Terminal 1: Backend
cd backend && python3 -m uvicorn app.main:app --reload

# Terminal 2: ngrok (obtener URL HTTPS)
cd ~ && ./ngrok http 5678

# Terminal 3: n8n (con URL de ngrok)
export WEBHOOK_URL=https://<ngrok-url>/
n8n start
```

**Nota**: La URL de ngrok cambia cada vez (plan gratuito). Necesitas actualizar `WEBHOOK_URL` cada sesión.

---

## Archivos Críticos

```
backend/app/
├── main.py                    # L215-265: Endpoint /query con rag_callback
├── models.py                  # L19: use_agent field
├── rag/
│   ├── entity_extractor.py    # L13: OBRAS_SOCIALES
│   ├── retriever.py           # L64: threshold cosine
│   └── indexer.py             # MIGRADO: index_from_json (lee *_FINAL.json)
└── llm/client.py              # L276-421: Agente function calling
                               # L399: num_predict=200 (post-RAG)
                               # L317-328: Ejemplos SIN conteo de palabras

data/obras_sociales_json/
├── asi/*_FINAL.json           # 21 chunks
├── ensalud/*_FINAL.json       # 1 chunk
├── iosfa/*_FINAL.json         # 3 chunks
└── grupo_pediatrico/*_FINAL.json  # NO indexado (protocolo base en prompt)

scripts/
├── convert_docs_to_json.py    # Paso 1: DOCX/PDF → JSON intermedio
├── clean_chunks_v2.py         # Paso 2: JSON intermedio → JSON final
├── index_data.py              # Reindexar FAISS desde JSON
└── process_all_step1.py       # Procesar todos los docs (paso 1)

n8n/workflows/
└── telegram_agente_hospital.json  # Workflow n8n + Telegram webhook

telegram_bot.py                # Bot Python directo (polling mode)
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

### ✅ Respuestas cortadas post-RAG
**Antes**: Respuestas se cortaban a ~200 caracteres (num_predict=50 muy bajo)
**Solución**: num_predict=200 en segunda llamada (post-RAG) - permite respuestas completas

### ✅ LLM muestra conteo de palabras
**Antes**: Bot respondía "DNI, credencial. ¿Qué tipo ingreso? (7 palabras)"
**Solución**: Eliminado "(X palabras)" de ejemplos en system prompt

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
**Ahora**: qwen2.5:3b → 30-40s queries simples, 180-200s con RAG
**Nota**: Lentitud por CPU sin GPU - no es problema de configuración

### ✅ RAG procesa PDF/DOCX en runtime
**Antes**: Indexer chunkeaba documentos en cada indexación
**Ahora**: Pipeline offline en 2 pasos → JSON → indexer lee JSON
**Beneficios**:
- Tablas preservadas completas
- Control humano del chunking
- Reindexación más rápida

---

## Datos

**Fuentes originales**: `data/obras_sociales/` (PDF/DOCX)
```
ensalud/*.docx
asi/2024-01-04_normas.docx
iosfa/*.docx
docs/checklist_general_grupo_pediatrico.docx
```

**Datos procesados**: `data/obras_sociales_json/` (JSON estructurado)
```
asi/*_FINAL.json           # 21 chunks indexados
ensalud/*_FINAL.json       # 1 chunk indexado
iosfa/*_FINAL.json         # 3 chunks indexados
grupo_pediatrico/*_FINAL.json  # NO indexado (protocolo base)
```

**GRUPO_PEDIATRICO**:
- Protocolo base del hospital (NO es una obra social)
- Aplica a TODOS los pacientes antes de consultar obra social específica
- Hardcoded en system prompt del agente
- NO indexado en RAG

**IMPORTANTE**: Documentos NO contienen info sobre copagos específicos por especialidad. Si agente dice montos/especialidades → está ALUCINANDO.

**FAISS Index**: `backend/faiss_index/` (25 documentos totales)

---

## Variables de Entorno

`backend/.env`:
```env
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
JSON_PATH=data/obras_sociales_json  # Path a JSONs procesados
TOP_K_RESULTS=5

# OBSOLETO (chunking ahora offline):
# CHUNK_SIZE=1000
# CHUNK_OVERLAP=100
# DATA_PATH=data/obras_sociales
# DOCS_PATH=docs
```

---

## Comandos

### Iniciar Sistema (Opción A: Bot Python)

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate
python3 -m uvicorn app.main:app --reload

# Terminal 2: Bot
python3 telegram_bot.py
```

### Iniciar Sistema (Opción B: n8n + ngrok)

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate
python3 -m uvicorn app.main:app --reload

# Terminal 2: ngrok
cd ~ && ./ngrok http 5678
# Copiar URL HTTPS que aparece

# Terminal 3: n8n
export WEBHOOK_URL=https://<ngrok-url>/
n8n start
# Abrir http://localhost:5678 y activar workflow
```

### Pipeline de Procesamiento

```bash
# Paso 1: DOCX/PDF → JSON intermedio
python scripts/convert_docs_to_json.py

# Paso 2: JSON intermedio → JSON final
python scripts/clean_chunks_v2.py

# Paso 3: Reindexar FAISS desde JSON
python scripts/index_data.py
```

### Testing

```bash
# Test directo
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "protocolo básico", "use_agent": true}'

# Health check
curl http://localhost:8000/health
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

- ✅ NO inventa obras sociales/copagos
- ✅ Llama RAG cuando necesita info
- ✅ "No tengo esa info" si RAG vacío
- ✅ Memoria conversacional (10 msgs)
- ⚠️ Respuestas post-RAG: ~400 chars (objetivo: < 100)
- ⚠️ Performance: 30-40s simple, 180-200s con RAG (CPU sin GPU)

---

## Resumen de Cambios Recientes (Enero 2026)

### Pipeline de Chunking Migrado
- **Antes**: Runtime chunking de PDF/DOCX en cada indexación
- **Ahora**: Pipeline offline 2 pasos (DOCX/PDF → JSON intermedio → JSON final)
- **Ventajas**: Tablas preservadas, control humano, reindexación rápida

### RAG System
- Migrado de `index_documents()` a `index_from_json()`
- 25 chunks indexados (ASI: 21, ENSALUD: 1, IOSFA: 3)
- GRUPO_PEDIATRICO NO indexado (protocolo base en prompt)

### Telegram Integration
- **Opción A**: Bot Python directo (polling)
- **Opción B**: n8n + webhook HTTPS (requiere ngrok)
- ngrok configurado: `~/ngrok http 5678`

### Fixes Aplicados
- `num_predict=200` en segunda llamada (respuestas completas post-RAG)
- Eliminado "(X palabras)" de ejemplos en prompt
- GRUPO_PEDIATRICO renombrado y clarificado (NO es obra social)

### Performance
- Queries simples: 30-40s
- Queries con RAG: 180-200s (limitación hardware, no config)
- Primera llamada: ~6s
- Segunda llamada (post-RAG): ~179s (bottleneck identificado)

---

## 🚀 Mejoras Futuras (Documentadas 2026-01-15)

### 1. Patrones de Uso (Prioridad: Alta, Dificultad: Fácil)

**Objetivo**: Saber qué preguntan más los usuarios y de qué obra social.

**Implementación**:
```python
# logs/usage_stats.json
{
  "2026-01-15": {
    "total_queries": 45,
    "por_obra_social": {"ENSALUD": 20, "ASI": 15, "IOSFA": 10},
    "por_tipo": {"protocolo": 25, "mail": 10, "telefono": 5, "copagos": 5}
  }
}
```

**Archivos a modificar**:
- `telegram_bot.py`: Agregar logging estructurado después de cada respuesta

**Tiempo estimado**: 1 hora

---

### 2. Preguntas Frecuentes (Prioridad: Media, Dificultad: Media)

**Objetivo**: Identificar top 10 preguntas más comunes para optimizar respuestas.

**Implementación**:
```python
# logs/frequent_questions.json
{
  "protocolo_internacion": {"count": 50, "ejemplo": "como interno un paciente"},
  "mail_ensalud": {"count": 30, "ejemplo": "dame el mail de ensalud"},
  "copago_consulta": {"count": 20, "ejemplo": "cuanto sale la consulta"}
}
```

**Opciones de clasificación**:
1. Keywords simples (más rápido, menos preciso)
2. LLM clasifica cada pregunta (más lento, más preciso)
3. Embeddings + clustering (balance)

**Archivos a modificar**:
- `telegram_bot.py`: Clasificar query antes de procesar
- Nuevo archivo: `backend/app/analytics/classifier.py`

**Tiempo estimado**: 2-3 horas

---

### 3. Feedback Automático (Prioridad: Media, Dificultad: Media)

**Objetivo**: Detectar cuando el bot no respondió bien para mejorar.

**Señales de feedback negativo**:
- Usuario repregunta lo mismo (no entendió)
- Usuario dice "no", "no me sirvió", "otra cosa"
- Usuario abandona conversación sin despedirse

**Señales de feedback positivo**:
- "Gracias", "Perfecto", "Ok"
- Usuario continúa con otra pregunta (flujo normal)

**Implementación**:
```python
# logs/feedback.json
[
  {
    "timestamp": "2026-01-15 13:41",
    "chat_id": "7187787641",
    "query": "qué es la denuncia?",
    "response": "La denuncia se refiere...",
    "feedback": "negative",  # repreguntó 3 veces
    "resolved": false
  }
]
```

**Archivos a modificar**:
- `telegram_bot.py`: Detectar patrones de repregunta
- Nuevo archivo: `backend/app/analytics/feedback.py`

**Tiempo estimado**: 3-4 horas

---

### 4. Dashboard de Analytics (Prioridad: Baja, Dificultad: Media)

**Objetivo**: Visualizar métricas en tiempo real.

**Opciones**:
1. Script Python que genera reporte diario
2. Endpoint FastAPI `/analytics` que devuelve JSON
3. Dashboard web simple (Streamlit o similar)

**Tiempo estimado**: 4-6 horas

---

### Orden de Implementación Sugerido

1. ✅ Reducir prompt (HECHO)
2. ✅ Reinicio de charlas (HECHO)
3. ⏳ Patrones de uso (próximo sprint)
4. ⏳ Preguntas frecuentes
5. ⏳ Feedback automático
6. ⏳ Dashboard
