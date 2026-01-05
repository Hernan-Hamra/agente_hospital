# 🚀 SETUP - Agente Hospitalario

## Paso 1: Instalar Ollama

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verificar instalación
ollama --version
```

## Paso 2: Descargar modelo llama3.1

```bash
# Descargar llama3.1 (4.7GB - demora ~5-15 min)
ollama pull llama3.1

# Verificar que se descargó
ollama list
```

## Paso 3: Configurar backend

```bash
cd /home/hernan/proyectos/agente_hospital/backend

# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Paso 4: Indexar documentos

```bash
# Desde la raíz del proyecto
cd /home/hernan/proyectos/agente_hospital

# Ejecutar indexación
python scripts/index_data.py
```

Este proceso:
- Leerá los PDFs/DOCX de `data/obras_sociales/`
- Generará embeddings
- Creará el índice FAISS
- Demora: ~5-10 minutos

## Paso 5: Iniciar backend

```bash
cd /home/hernan/proyectos/agente_hospital/backend

# Asegurate que el entorno esté activado
source venv/bin/activate

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:
```
🏥 AGENTE HOSPITALARIO - GRUPO PEDIÁTRICO
✅ Ollama disponible en http://localhost:11434
📦 Modelo: llama3.1
✅ Índice cargado: XXX chunks
🚀 Servidor listo - http://localhost:8000
```

## Paso 6: Probar el sistema

### Opción 1: Navegador
Visitá: http://localhost:8000/docs

### Opción 2: curl
```bash
# Health check
curl http://localhost:8000/health

# Consulta de prueba
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Qué documentos necesito para enrolar un paciente de ENSALUD Plan Quantum?",
    "obra_social": "ENSALUD"
  }'
```

---

## 🔧 Troubleshooting

### Ollama no responde
```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, iniciarlo manualmente
ollama serve
```

### Error al indexar
```bash
# Verificar que existan los archivos
ls -lh data/obras_sociales/*/

# Verificar permisos
chmod +x scripts/index_data.py
```

### Error de dependencias Python
```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 📊 Recursos del sistema durante ejecución

Con llama3.1 (8B) esperá:
- **RAM usada:** ~10-12 GB
- **CPU:** 50-80% durante consultas
- **Disco:** 4.7GB (modelo) + ~500MB (índice FAISS)

---

## ⚡ Próximos pasos (después de probar)

1. Ajustar parámetros en `backend/.env` si es necesario
2. Probar con llama3.2 para comparar velocidad
3. Integrar con n8n (futuro)
4. Conectar bot de Telegram (futuro)
