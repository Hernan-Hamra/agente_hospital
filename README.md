# Agente Hospitalario - Grupo Pediátrico

Sistema conversacional para personal administrativo del hospital Grupo Pediátrico. Asiste en consultas sobre enrolamiento de pacientes y procedimientos de obras sociales.

## Escenarios Actuales

| Escenario         | Descripción   | RAG      | LLM          | Memoria |
|-------------------|---------------|----------|--------------|---------|
| **escenario_1**   | Modo Consulta | ChromaDB | Groq (cloud) | No      |
| **escenario_2**   | Bot SQL       | No       | No           | No      |
| **escenario_3**   | Modo Agente   | ChromaDB | Groq (cloud) | Sí      |

### Escenario 1: Bot LLM Modo Consulta
- **RAG**: ChromaDB con bge-large-en-v1.5
- **LLM**: Groq API (cloud, rápido)
- **Query Rewriter**: Mejora precisión de búsqueda
- **Tests**: 12 tests (retriever, entity, query rewriter)
- **Evaluación**: 20 preguntas de prueba

### Escenario 2: Bot SQL Sin LLM
- **Base de datos**: SQLite con obras sociales
- **Sin LLM**: Respuestas directas por SQL
- **Tests**: 2 tests (basic, restricciones)
- **Uso**: Consultas estructuradas de admisión

### Escenario 3: Bot LLM Modo Agente
- **RAG**: ChromaDB compartido con escenario_1
- **LLM**: Groq API con function calling
- **Memoria**: Mantiene contexto conversacional
- **Tests**: 13 tests (basic, retriever)

## Estructura del Proyecto

```
agente_hospital/
├── escenario_1/          # Bot LLM Modo Consulta
│   ├── bot.py            # Bot Telegram
│   ├── evaluate.py       # Evaluación 20 preguntas
│   ├── rag/              # Retriever ChromaDB
│   ├── llm/              # Cliente Groq
│   └── tests/            # 12 tests
├── escenario_2/          # Bot SQL sin LLM
│   ├── bot.py            # Bot Telegram
│   ├── data/             # obras_sociales.db
│   └── tests/            # 2 tests
├── escenario_3/          # Bot LLM Modo Agente
│   ├── bot.py            # Bot con memoria
│   ├── rag/              # Retriever compartido
│   ├── llm/              # Cliente Groq + tools
│   └── tests/            # 13 tests
├── shared/
│   └── data/
│       ├── chroma_db/              # ChromaDB (escenario_1 y 3)
│       └── obras_sociales_json/    # Chunks JSON fuente
├── venv/                 # Entorno virtual
└── pytest.ini            # Configuración tests
```

## Instalación y Uso

### Requisitos
```bash
# Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuración
Crear `.env` en la raíz:
```env
GROQ_API_KEY=tu_api_key_groq
TELEGRAM_BOT_TOKEN=tu_token_telegram
```

### Ejecutar Escenarios
```bash
# Escenario 1: Bot Consulta
source venv/bin/activate
python escenario_1/bot.py

# Escenario 2: Bot SQL
python escenario_2/bot.py

# Escenario 3: Bot Agente
python escenario_3/bot.py
```

### Tests
```bash
# Todos los tests
pytest

# Por escenario
pytest escenario_1/tests/
pytest escenario_2/tests/
pytest escenario_3/tests/
```

## Obras Sociales Incluidas

- **ENSALUD** - 10 planes + planes corporativos deportes
- **ASI** - Múltiples planes (100, 200, 250, 300, 350, 400, 450, Evolution, Exclusive)
- **IOSFA** - Checklist específico

---

## Historial del Experimento

Esta sección documenta las pruebas y experimentos realizados durante el desarrollo.

### Experimento: LLM Local en CPU (Enero 2025)

Se probó correr un LLM local usando **Ollama** con el modelo **qwen2.5:3b** en CPU (sin GPU).

**Resultado**: Tiempos de respuesta de **180-200 segundos** por consulta con RAG. Inaceptable para uso en producción.

**Stack probado**:
- **LLM**: Ollama (qwen2.5:3b con function calling)
- **RAG**: FAISS + sentence-transformers + cosine similarity
- **Backend**: FastAPI
- **Bot**: n8n + Telegram (webhook HTTPS con ngrok)

**Lecciones aprendidas**:
- LLM local en CPU es inviable para chatbots interactivos
- Migración a Groq (cloud) redujo latencia a ~2-3 segundos
- FAISS fue reemplazado por ChromaDB por mejor integración

### Experimento: n8n + Telegram Webhook

Se probó usar n8n como orquestador con webhook HTTPS (requería ngrok).

**Problemas**:
- URL de ngrok cambia cada sesión (plan gratuito)
- Complejidad innecesaria para el caso de uso
- Difícil debugging del flujo

**Solución**: Bot Python directo con python-telegram-bot (polling mode)

### Arquitectura Deprecada

El código viejo incluía:
- `backend/` - API FastAPI con agente function calling
- `backend/faiss_index/` - Índice FAISS (25 documentos)
- `scripts/` - Pipeline chunking offline (DOCX/PDF → JSON → FAISS)
- `n8n/workflows/` - Workflow Telegram
- `telegram_bot.py` - Bot original

Todo esto fue movido o eliminado en la refactorización de Febrero 2026.

---

## Escenarios Explorados (No Registrados)

Durante el desarrollo se exploraron otros enfoques que no quedaron como escenarios formales:

### Escenario 4-5: Variantes de Agente
- Pruebas con diferentes configuraciones de memoria
- Experimentos con prompts más restrictivos
- Ajustes de temperature y tokens

### Escenario 6: Híbrido SQL + RAG
- Intento de combinar consultas SQL para datos estructurados con RAG para texto libre
- Descartado por complejidad sin beneficio claro

### Escenario 7: Multi-agente
- Exploración de arquitectura con múltiples agentes especializados
- No implementado por scope del proyecto

### Otros Experimentos
- **Diferentes modelos de embedding**: Probados varios antes de elegir bge-large-en-v1.5
- **Chunking strategies**: Diferentes tamaños y overlaps
- **Similarity thresholds**: Ajustes de cosine similarity para RAG
- **Prompt engineering**: Iteraciones para respuestas ultra-breves

---

## Licencia

Proyecto interno - Grupo Pediátrico
