# Agente Hospitalario - Grupo Pediátrico

Sistema conversacional RAG con agente autónomo para personal administrativo del hospital Grupo Pediátrico.

Asiste en consultas sobre enrolamiento de pacientes y procedimientos de obras sociales con memoria conversacional.

## Stack Tecnológico

- **LLM**: Ollama (qwen2.5:3b con function calling)
- **RAG**: FAISS + sentence-transformers + cosine similarity
- **Chunking**: Pipeline offline 2 pasos (DOCX/PDF → JSON intermedio → JSON final)
- **Backend**: FastAPI (Python)
- **Bot**: n8n + Telegram (webhook HTTPS) O python-telegram-bot (polling)
- **Agente**: Function calling autónomo (decide cuándo usar RAG)
- **Túnel**: ngrok (para webhook mode)

## Características Principales

- **Agente Autónomo**: Decide automáticamente cuándo buscar en documentos vs responder desde conocimiento
- **Memoria Conversacional**: Mantiene contexto de conversación (10 mensajes)
- **Respuestas Ultra-Breves**: Máximo 15 palabras, guiadas por preguntas
- **Prevención de Alucinaciones**: No inventa información (copagos, especialidades, montos)
- **Validación de Obras Sociales**: Solo responde sobre ENSALUD, ASI, IOSFA
- **Búsqueda Semántica**: Cosine similarity en embeddings
- **Telegram Bot**: Interfaz conversacional con historial

## Estructura del Proyecto

```
agente_hospital/
├── data/
│   ├── obras_sociales/      # Documentos originales DOCX/PDF
│   │   ├── ensalud/
│   │   ├── asi/
│   │   └── iosfa/
│   └── obras_sociales_json/ # Datos procesados (JSONs finales)
│       ├── asi/*_FINAL.json           # 21 chunks indexados
│       ├── ensalud/*_FINAL.json       # 1 chunk indexado
│       ├── iosfa/*_FINAL.json         # 3 chunks indexados
│       └── grupo_pediatrico/*_FINAL.json  # NO indexado (protocolo base)
├── backend/
│   ├── app/
│   │   ├── main.py          # API endpoints + agente
│   │   ├── rag/             # RAG con cosine similarity
│   │   │   ├── retriever.py
│   │   │   ├── entity_extractor.py
│   │   │   └── indexer.py   # index_from_json (lee *_FINAL.json)
│   │   └── llm/
│   │       └── client.py    # Agente con function calling
│   ├── faiss_index/         # Índice FAISS (25 documentos)
│   └── .env
├── scripts/
│   ├── convert_docs_to_json.py    # Paso 1: DOCX/PDF → JSON intermedio
│   ├── clean_chunks_v2.py         # Paso 2: JSON intermedio → JSON final
│   ├── index_data.py              # Paso 3: Reindexar FAISS
│   └── process_all_step1.py       # Procesar todos (paso 1)
├── n8n/workflows/
│   └── telegram_agente_hospital.json  # Workflow n8n + Telegram
└── telegram_bot.py          # Bot Python directo (polling mode)
```

## Instalación

### 1. Prerequisitos (Ubuntu/WSL)

```bash
# Instalar Python 3.10+
sudo apt update && sudo apt install python3 python3-pip python3-venv -y

# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo qwen2.5:3b (mejor para function calling)
ollama pull qwen2.5:3b
```

### 2. Configurar Backend

```bash
# Crear entorno virtual
cd backend
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Editá `backend/.env`:

```env
# LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG
TOP_K_RESULTS=5

# Paths
JSON_PATH=data/obras_sociales_json  # JSONs procesados
FAISS_INDEX_PATH=./faiss_index
```

**Nota**: `CHUNK_SIZE` y `CHUNK_OVERLAP` ya no se usan (chunking ahora es offline).

### 4. Procesar y Indexar Documentos

El sistema usa un pipeline de chunking offline en 2 pasos:

```bash
# Paso 1: DOCX/PDF → JSON intermedio
python scripts/convert_docs_to_json.py

# Paso 2: JSON intermedio → JSON final (limpieza y validación)
python scripts/clean_chunks_v2.py

# Paso 3: Indexar en FAISS desde JSONs finales
python scripts/index_data.py
```

**Nota**: Los archivos `*_FINAL.json` ya están procesados. Solo necesitas ejecutar el Paso 3 para reindexar.

### 5. Iniciar Sistema

#### Opción A: Con Bot Telegram directo (Python)

**Terminal 1 - Backend:**
```bash
cd backend # cd ~/proyectos/agente_hospital/backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload
```

**Terminal 2 - Bot Telegram:**
```bash
cd ~/proyectos/agente_hospital  # Raíz del proyecto
source venv/bin/activate
python3 telegram_bot.py
```

#### Opción B: Con n8n + Telegram (Webhook mode - Requiere HTTPS)

**IMPORTANTE**: El webhook de Telegram requiere HTTPS. Para desarrollo local necesitas ngrok.

**Terminal 1 - Backend:**
```bash
cd ~/proyectos/agente_hospital/backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload
```

**Terminal 2 - ngrok (túnel HTTPS):**
```bash
cd ~
./ngrok http 5678
```

Después de lanzar ngrok, **copiá la URL HTTPS** que aparece (ej: `https://xyz.ngrok-free.dev`)

**Terminal 3 - n8n:**
```bash
export WEBHOOK_URL=<URL_DE_NGROK>/
n8n start
# Luego accede a http://localhost:5678 y activa el workflow
```

**Ejemplo completo:**
```bash
export WEBHOOK_URL=https://ichthyotic-overbooming-makhi.ngrok-free.dev/
n8n start
```

**Nota**: La URL de ngrok cambia cada vez que lo reiniciás (versión gratuita). Necesitás actualizar `WEBHOOK_URL` cada sesión.

## Uso

### Telegram Bot

El bot mantiene memoria conversacional y responde de forma ultra-breve:

```
Usuario: hola
Bot: Hola! Soy un asistente administrativo del Grupo Pediátrico. ¿En qué puedo ayudarte?

Usuario: dame el protocolo
Bot: DNI, credencial, validar. ¿Qué tipo ingreso?

Usuario: guardia
Bot: Guardia: DNI + credencial. ¿Obra social?

Usuario: osde
Bot: No tengo OSDE. Solo ENSALUD/ASI/IOSFA

Usuario: asi
[Agente llama a RAG automáticamente]
Bot: ASI ingreso guardia: DNI, credencial, validar. ¿Algo más?
```

### API REST

#### GET /health
```bash
curl http://localhost:8000/health
```

#### POST /query (Modo Agente)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "protocolo básico",
    "use_agent": true,
    "historial": []
  }'
```

Respuesta:
```json
{
  "respuesta": "DNI, credencial, validar. ¿Qué tipo ingreso?",
  "fuentes": [],
  "obra_social_detectada": null
}
```

### Documentación Swagger

http://localhost:8000/docs

## Funcionamiento del Agente

El agente con function calling decide automáticamente:

1. **Pregunta general** → Responde directamente (protocolo básico)
2. **Pregunta específica de obra social** → Llama `consulta_rag` tool
3. **RAG sin resultados** → "No tengo esa info. ¿Algo más?"
4. **Obra social no cargada** → "No tengo OSDE. Solo ENSALUD/ASI/IOSFA"

**Herramientas disponibles:**
- `consulta_rag(obra_social, query)`: Busca en documentos indexados

**Reglas estrictas:**
- Máximo 15 palabras por respuesta
- NUNCA inventar información (copagos, montos, especialidades)
- SIEMPRE terminar con pregunta
- Usar RAG obligatorio si no sabe algo

## Obras Sociales Incluidas

1. **ENSALUD** - 10 planes + planes corporativos deportes
2. **ASI** - Múltiples planes (100, 200, 250, 300, 350, 400, 450, Evolution, Exclusive)
3. **IOSFA** - Checklist específico

## Actualización de Datos

### Agregar Nuevo Documento de Obra Social

**Protocolo sintético:**

```bash
# 1. Copiar archivo DOCX/PDF a la carpeta correspondiente
cp ~/Downloads/nueva_normativa.docx data/obras_sociales/asi/

# 2. Convertir a JSON intermedio (paso 1)
python scripts/convert_docs_to_json.py

# 3. Limpiar y generar JSON final (paso 2)
python scripts/clean_chunks_v2.py

# 4. Reindexar FAISS
python scripts/index_data.py

# 5. Verificar
curl http://localhost:8000/health
# Debe mostrar el nuevo total de documentos indexados
```

**Estructura de carpetas:**
```
data/obras_sociales/
├── asi/nueva_normativa.docx          # 1. Poner archivo aquí
├── ensalud/
└── iosfa/

data/obras_sociales_json/
├── asi/nueva_normativa_chunks.json   # 2. Generado por paso 1
├── asi/nueva_normativa_FINAL.json    # 3. Generado por paso 2 (ESTE se indexa)
```

**Nota**: Backend en `--reload` detecta automáticamente el nuevo índice FAISS.

## Configuración Telegram

1. Crear bot con BotFather: `/newbot`
2. Obtener token
3. Configurar en `telegram_bot.py`:
```python
TELEGRAM_TOKEN = "tu_token_aqui"
BACKEND_URL = "http://localhost:8000"
```

## Troubleshooting

### Ollama no disponible
```bash
curl http://localhost:11434/api/tags
# Si falla:
ollama serve
```

### Evaluacion de Modelo incorrecto
```bash
ollama list
ollama pull qwen2.5:3b
```

### Bot inventa información
- Verificar que `use_agent: True` esté activado
- Revisar que `OLLAMA_MODEL=qwen2.5:3b` en `.env`
- Reducir `num_predict` en `client.py` si respuestas muy largas

### RAG no encuentra documentos
```bash
# Verificar JSONs finales procesados
ls -R data/obras_sociales_json/*_FINAL.json

# Reindexar desde JSONs
python scripts/index_data.py

# Verificar índice FAISS
curl http://localhost:8000/health
# Debe mostrar: "documentos_indexados": 25
```

### n8n webhook "Bad request"
**Problema**: Telegram requiere HTTPS para webhooks

**Solución**:
```bash
# 1. Iniciar ngrok para crear túnel HTTPS
cd ~ && ./ngrok http 5678

# 2. Copiar URL HTTPS generada (ej: https://xyz.ngrok-free.dev)

# 3. Iniciar n8n con WEBHOOK_URL
export WEBHOOK_URL=https://<ngrok-url>/
n8n start

# 4. Activar workflow en http://localhost:5678
```

**Nota**: La URL de ngrok cambia cada vez (plan gratuito)

## Arquitectura Técnica

### Pipeline RAG

**Offline (Chunking en 2 pasos)**:
1. **Paso 1**: DOCX/PDF → JSON intermedio (extracción texto/tablas)
2. **Paso 2**: JSON intermedio → JSON final (limpieza, validación, metadata)
3. **Indexación**: JSON final → Embeddings → FAISS (1 chunk JSON = 1 embedding)

**Runtime (Consulta)**:
1. Query → Embedding
2. FAISS → Cosine similarity → Top-K chunks
3. Chunks → LLM (con function calling)

### Agente con Function Calling
1. User query → Agente analiza
2. **Si necesita RAG**: Llama `consulta_rag` tool → Backend ejecuta callback → RAG retrieval
3. Agente recibe contexto → Genera respuesta ultra-breve
4. **Si NO necesita RAG**: Responde directo desde protocolo básico

### Memoria Conversacional
- Deque de 10 mensajes (user + assistant)
- Se envía historial en cada request
- Agente mantiene contexto de conversación

## Estado Actual (Enero 2026)

### ✅ Completado
- Pipeline chunking offline (2 pasos) con control humano
- RAG migrado de PDF/DOCX a JSON (25 chunks indexados)
- Agente con function calling funcionando correctamente
- Integración n8n + Telegram con webhook HTTPS (ngrok)
- Bot Python directo con memoria conversacional
- Prevención de alucinaciones (num_predict ajustado)
- Cosine similarity threshold para RAG
- GRUPO_PEDIATRICO diferenciado (protocolo base vs obras sociales)

### ⚠️ Conocido
- **Performance**: 180-200s con RAG (limitación hardware CPU, no GPU)
- **ngrok URL**: Cambia cada sesión (plan gratuito)
- **Respuestas post-RAG**: Más largas de lo ideal (~400 chars vs objetivo 100)

### 🔄 En Desarrollo
- Optimización de respuestas ultra-breves post-RAG
- Testing con más obras sociales

## Próximos Pasos

- [ ] Añadir 127 obras sociales restantes
- [ ] Implementar caché de consultas frecuentes
- [ ] Dashboard de métricas y analytics
- [ ] Dockerización para deploy
- [ ] Integración con sistema hospitalario
- [ ] Evaluar Groq/API cloud para mejorar performance

## Licencia
Proyecto interno - Grupo Pediátrico
