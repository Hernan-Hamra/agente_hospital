# Agente Hospitalario - Grupo Pediátrico

Sistema conversacional RAG con agente autónomo para personal administrativo del hospital Grupo Pediátrico.

Asiste en consultas sobre enrolamiento de pacientes y procedimientos de obras sociales con memoria conversacional.

## Stack Tecnológico

- **LLM**: Ollama (qwen2.5:3b con function calling)
- **RAG**: FAISS + sentence-transformers + cosine similarity
- **Backend**: FastAPI (Python)
- **Bot**: Telegram con memoria conversacional
- **Agente**: Function calling autónomo (decide cuándo usar RAG)

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
├── data/obras_sociales/     # Documentos DOCX de obras sociales
│   ├── ensalud/
│   ├── asi/
│   └── iosfa/
├── backend/
│   ├── app/
│   │   ├── main.py          # API endpoints + agente
│   │   ├── rag/             # RAG con cosine similarity
│   │   │   ├── retriever.py
│   │   │   └── entity_extractor.py
│   │   └── llm/
│   │       └── client.py    # Agente con function calling
│   └── .env
├── telegram_bot.py          # Bot con memoria conversacional
└── scripts/index_data.py    # Indexador FAISS
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
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
TOP_K_RESULTS=5

# Paths
DATA_PATH=data/obras_sociales
FAISS_INDEX_PATH=./faiss_index
```

### 4. Indexar Documentos

```bash
# Desde la raíz del proyecto
python scripts/index_data.py
```

### 5. Iniciar Sistema

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload
```

**Terminal 2 - Bot Telegram:**
```bash
source backend/venv/bin/activate
python3 telegram_bot.py
```

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

```bash
# 1. Agregar nuevo documento
cp ~/Downloads/nueva_normativa.docx data/obras_sociales/asi/

# 2. Reindexar
python scripts/index_data.py

# 3. Reiniciar backend (auto-detecta nuevo índice)
```

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

### Modelo incorrecto
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
# Reindexar
python scripts/index_data.py

# Verificar que existan archivos .docx en data/obras_sociales/
ls -R data/obras_sociales/
```

## Arquitectura Técnica

### Pipeline RAG
1. **Indexación**: Documentos → Chunks (1000 chars) → Embeddings → FAISS
2. **Consulta**: Query → Embedding → Cosine similarity → Top-K chunks → LLM

### Agente con Function Calling
1. User query → Agente analiza
2. **Si necesita RAG**: Llama `consulta_rag` tool → Backend ejecuta callback → RAG retrieval
3. Agente recibe contexto → Genera respuesta ultra-breve
4. **Si NO necesita RAG**: Responde directo desde protocolo básico

### Memoria Conversacional
- Deque de 10 mensajes (user + assistant)
- Se envía historial en cada request
- Agente mantiene contexto de conversación

## Próximos Pasos

- [ ] Añadir 127 obras sociales restantes
- [ ] Implementar caché de consultas frecuentes
- [ ] Dashboard de métricas y analytics
- [ ] Dockerización para deploy
- [ ] Integración con sistema hospitalario

## Licencia
Proyecto interno - Grupo Pediátrico
