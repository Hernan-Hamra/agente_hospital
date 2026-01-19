# Setup para Máquina con GPU (Escenario 2)

Este documento describe cómo configurar el Escenario 2 (Ollama GPU) en una máquina con RTX 3060 12GB.

## Requisitos

- **GPU**: NVIDIA RTX 3060 (12GB VRAM) o superior
- **CUDA**: 11.8+
- **Python**: 3.10+
- **Ollama**: Última versión

## Paso 1: Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verificar que detecta la GPU:
```bash
ollama --version
nvidia-smi
```

## Paso 2: Descargar Modelo Recomendado

Para 12GB de VRAM, recomendamos `llama3.1:8b`:

```bash
ollama pull llama3.1:8b
```

Alternativas:
- `qwen2.5:7b` - Buen balance velocidad/calidad
- `mistral:7b` - Rápido, buena calidad
- `llama3.2:3b` - Si hay problemas de memoria

Verificar modelo:
```bash
ollama list
ollama run llama3.1:8b "Hola, ¿funcionás?"
```

## Paso 3: Clonar/Copiar el Proyecto

```bash
git clone <repo> agente_hospital
# o copiar desde la otra máquina
```

## Paso 4: Configurar Entorno

```bash
cd agente_hospital/backend
python -m venv venv
source venv/bin/activate  # Linux
pip install -r requirements.txt
```

## Paso 5: Configurar .env

Crear/editar `backend/.env`:

```env
# Ollama GPU
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# RAG
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
FAISS_INDEX_PATH=./faiss_index
TOP_K_RESULTS=3

# Sin Groq (opcional en esta máquina)
# GROQ_API_KEY=
```

## Paso 6: Verificar Configuración

Editar `config/scenarios.yaml` si es necesario:

```yaml
ollama_gpu_consulta:
  enabled: true
  llm:
    provider: "ollama"
    model: "llama3.1:8b"        # Ajustar según modelo descargado
    host: "http://localhost:11434"
```

## Paso 7: Ejecutar Test

```bash
# Activar entorno
cd backend
source venv/bin/activate

# Verificar health
python ../scripts/run_scenario.py --health

# Ejecutar query de prueba
python ../scripts/run_scenario.py \
  --scenario ollama_gpu_consulta \
  --query "¿Qué documentos necesito para IOSFA?"

# Ejecutar batch completo
python ../scripts/run_scenario.py \
  --batch \
  --scenario ollama_gpu_consulta
```

## Métricas Esperadas (RTX 3060 12GB)

| Métrica | Valor Esperado |
|---------|----------------|
| Latencia primera query | 3-8 segundos |
| Latencia queries siguientes | 1-3 segundos |
| Tokens/segundo | 30-50 |
| VRAM usada | ~8-10 GB |

## Troubleshooting

### GPU no detectada
```bash
# Verificar CUDA
nvidia-smi
nvcc --version

# Reinstalar Ollama con soporte GPU
curl -fsSL https://ollama.com/install.sh | sh
```

### Out of Memory
```bash
# Usar modelo más pequeño
ollama pull llama3.2:3b

# Editar scenarios.yaml
# model: "llama3.2:3b"
```

### Ollama no responde
```bash
# Reiniciar servicio
sudo systemctl restart ollama

# Verificar logs
journalctl -u ollama -f
```

## Comparación con Groq

Una vez configurado, ejecutar comparación:

```bash
# Necesita GROQ_API_KEY configurado
python ../scripts/run_scenario.py \
  --compare \
  --query "¿Qué documentos necesito para IOSFA?"
```

Esto ejecutará la misma query en ambos escenarios y mostrará comparación de tokens, latencia y costo.
