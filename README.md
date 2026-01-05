
# agente_hospital
Agente Hospitalario - Grupo Pediátrico  Sistema conversacional RAG para personal administrativo del hospital Grupo Pediátrico.  Asiste en consultas sobre enrolamiento de pacientes y procedimientos de obras sociales.
=======
# Agente Hospitalario - Grupo Pediátrico

Sistema conversacional RAG para personal administrativo del hospital Grupo Pediátrico.

Asiste en consultas sobre enrolamiento de pacientes y procedimientos de obras sociales.

## Stack Tecnológico

- **LLM**: Ollama (Llama 3.2 local)
- **RAG**: FAISS + sentence-transformers
- **Backend**: FastAPI (Python)
- **Orquestación**: n8n (futuro)
- **Canal**: Telegram (futuro)

## Estructura del Proyecto

```
agente_hospital/
├── data/obras_sociales/     # Documentos PDF/DOCX de obras sociales
│   ├── ensalud/
│   ├── asi/
│   └── iosfa/
├── docs/                     # Documentación general del hospital
├── backend/                  # API FastAPI + RAG
│   ├── app/
│   │   ├── main.py          # Endpoints
│   │   ├── rag/             # Sistema RAG
│   │   └── llm/             # Cliente Ollama
│   └── requirements.txt
└── scripts/                  # Scripts de utilidad
    └── index_data.py        # Indexar documentos
```

## Instalación

### 1. Prerequisitos (Ubuntu)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo LLM
ollama pull llama3.2
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

### 3. Indexar Documentos

```bash
# Desde la raíz del proyecto
python scripts/index_data.py
```

Esto leerá todos los PDF/DOCX de `data/obras_sociales/` y generará el índice FAISS.

### 4. Iniciar Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Uso

### API REST

El backend expone los siguientes endpoints:

#### GET /health
```bash
curl http://localhost:8000/health
```

Respuesta:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "ollama_disponible": true,
  "indice_cargado": true,
  "documentos_indexados": 245
}
```

#### POST /query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Qué documentos necesito para enrolar un paciente de ENSALUD?",
    "obra_social": "ENSALUD"
  }'
```

Respuesta:
```json
{
  "respuesta": "📋 Documentación requerida - ENSALUD\n\n1. DNI del paciente\n2. Credencial vigente...",
  "fuentes": [
    {
      "archivo": "2024-01-04_normativa.pdf",
      "fragmento": "Requisitos de enrolamiento...",
      "relevancia": 0.892
    }
  ],
  "obra_social_detectada": "ENSALUD"
}
```

### Documentación Interactiva

Visitá http://localhost:8000/docs para la documentación Swagger interactiva.

## Actualización de Datos

Cuando recibás un PDF actualizado de una obra social:

```bash
# 1. Guardar versión anterior (opcional)
cp data/obras_sociales/ensalud/2024-01-04_normativa.pdf \
   docs/originales/ensalud_backup.pdf

# 2. Copiar nuevo archivo
cp ~/Downloads/nueva_normativa.pdf \
   data/obras_sociales/ensalud/2024-06-15_normativa.pdf

# 3. Reindexar
python scripts/index_data.py

# 4. Reiniciar backend (si está corriendo)
# El backend detectará automáticamente el nuevo índice
```

## Obras Sociales Incluidas

Actualmente indexadas (demo):

1. **ENSALUD** - 10 planes + planes corporativos deportes
2. **ASI** - Múltiples planes (100, 200, 250, 300, 350, 400, 450, Evolution, Exclusive)
3. **IOSFA** - Checklist específico

## Configuración Avanzada

Editá `backend/.env` para modificar parámetros:

```env
# LLM
OLLAMA_MODEL=llama3.2          # Cambiar modelo (mistral, llama2, etc.)

# RAG
CHUNK_SIZE=500                 # Tamaño de chunks
CHUNK_OVERLAP=50               # Overlap entre chunks
TOP_K_RESULTS=5                # Cantidad de resultados a recuperar

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Troubleshooting

### Ollama no disponible

```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, iniciá Ollama
ollama serve
```

### Modelo no encontrado

```bash
# Listar modelos instalados
ollama list

# Descargar modelo
ollama pull llama3.2
```

### Índice no cargado

```bash
# Reindexar documentos
python scripts/index_data.py
```

### Error de dependencias Python

```bash
# Reinstalar dependencias
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Próximos Pasos

- [ ] Integración con n8n
- [ ] Bot de Telegram
- [ ] Añadir 127 obras sociales restantes
- [ ] Dashboard de métricas
- [ ] Dockerización (cuando esté listo para deploy)

## Licencia
Proyecto demo interno - Grupo Pediátrico

