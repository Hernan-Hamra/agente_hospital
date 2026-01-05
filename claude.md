# Agente Hospitalario - Grupo Pediátrico

## Objetivo
Sistema RAG + LLM local para asistir al personal administrativo del hospital con consultas sobre enrolamiento de pacientes y procedimientos de obras sociales.

## Stack Tecnológico
- **Backend**: Python + FastAPI
- **LLM**: Ollama local (llama3.2:3b)
- **RAG**: FAISS + sentence-transformers
- **Documentos**: 130 obras sociales (actualmente 3: ENSALUD, ASI, IOSFA)

## Arquitectura

### Flujo de Consulta
1. Usuario envía pregunta en lenguaje natural
2. **EntityExtractor** detecta obra social y tipo de consulta (con fuzzy matching para typos)
3. **RAG Retriever** busca chunks relevantes en FAISS (threshold: 0.5)
4. **LLM** genera respuesta usando contexto recuperado
5. Respuesta estructurada con fuentes

### Componentes Clave

#### 1. Entity Extraction (`app/rag/entity_extractor.py`)
- Detecta obra social automáticamente (9 obras sociales configuradas)
- Fuzzy matching para tolerar typos: "ennsalud" → "ENSALUD"
- Detecta tipo de consulta: enrolamiento, autorización, internación, etc.
- Detecta urgencia: urgente vs programado

#### 2. RAG Retriever (`app/rag/retriever.py`)
- FAISS index con 72 chunks (500 chars, overlap 50)
- Threshold de similitud: **0.5** (bajado de 0.6 para mejor recall)
- Filtra por obra social cuando se especifica
- Retorna top 5 chunks más relevantes

#### 3. LLM Client (`app/llm/client.py`)
- Modelo: llama3.2 (3B params, ~1:53 min por respuesta)
- System prompt con reglas estrictas:
  - NO inventar información
  - Usar SOLO contexto provisto
  - Distinguir entre presentación personal y consultas procedimentales
- Formato estructurado: documentación → pasos → observaciones

#### 4. API Endpoints (`app/main.py`)
- `POST /query`: Consulta principal
  - Request: `{pregunta: str, obra_social?: str}`
  - Response: `{respuesta: str, fuentes: [], obra_social_detectada: str}`
- `GET /health`: Health check del sistema

## Indexación de Documentos

```bash
cd backend
source venv/bin/activate
python scripts/index_data.py
```

- Procesa PDFs y DOCX desde `data/obras_sociales/`
- Genera embeddings con `sentence-transformers/all-MiniLM-L6-v2`
- Guarda en `faiss_index/` (index.faiss + documents.pkl)

## Ejecución

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Servidor: http://localhost:8000
- Docs interactivos: http://localhost:8000/docs

## Problemas Conocidos y Mejoras Pendientes

### Crítico
1. **LLM pequeño alucina**: llama3.2 (3B) inventa información
   - Solución: cambiar a mistral:7b-instruct o llama3.1:8b
2. **Chunks muy pequeños**: 500 chars puede partir contexto
   - Solución: aumentar a 1000 chars, semantic chunking

### Medio
3. **Sin memoria de conversación**: cada pregunta es independiente
4. **Respuestas lentas**: 1:53 min promedio
5. **Faltan 127 obras sociales**: solo 3 indexadas

### Mejoras Futuras
- Threshold de relevancia dinámico
- Re-ranker post-RAG
- Few-shot examples en prompt
- Validación de respuesta pre-envío
- Sistema de templates para consultas comunes
- Integración n8n + Telegram

## Configuración Actual

### Threshold RAG
```python
# retriever.py línea 62
if similarity < 0.5:  # Bajado de 0.6
    continue
```

### Obras Sociales Detectadas
- ENSALUD, ASI, IOSFA, OSDE, SWISS_MEDICAL, GALENO, OMINT, MEDICUS, SANCOR

### Embeddings
- Modelo: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensión: 384
- Chunks indexados: 72

## Testing

Consulta de ejemplo:
```json
{
  "pregunta": "como enrolo a un paciente para la obra social ensalud"
}
```

Respuesta esperada:
- Detecta ENSALUD automáticamente
- Recupera 5-10 chunks relevantes (similarity > 0.5)
- Lista documentación: DNI, credencial, número de socio
- Incluye fuentes con relevancia

## Próximos Pasos
1. Probar con mistral:7b-instruct (mejor calidad)
2. Agregar 127 obras sociales restantes
3. Aumentar chunk_size a 1000
4. Implementar historial de conversación
5. Agregar validación de respuesta
