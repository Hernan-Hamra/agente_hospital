# 🧪 Tests del Agente Hospitalario

Estructura organizada de tests para el sistema RAG hospitalario.

## 📁 Estructura de carpetas

```
tests/
├── unit/           # Tests unitarios (componentes aislados)
├── integration/    # Tests de integración (componentes conectados)
├── system/         # Tests de sistema completo (end-to-end)
└── README.md       # Este archivo
```

---

## 🔬 Tipos de tests

### 1. **Unit Tests** (`tests/unit/`)

**Qué testean**: Componentes individuales de forma aislada

**Ejemplos**:
- `test_chunking.py` - Verifica que el chunking divide correctamente los textos
- `test_embeddings.py` - Verifica que los embeddings se generan correctamente
- `test_table_extraction.py` - Verifica extracción de tablas de PDF/DOCX

**Características**:
- ✅ Rápidos (< 1 segundo cada uno)
- ✅ No requieren índice FAISS
- ✅ No requieren LLM
- ✅ Mockean dependencias externas

**Cuándo correrlos**: Después de cada cambio en el código de procesamiento

---

### 2. **Integration Tests** (`tests/integration/`)

**Qué testean**: Múltiples componentes trabajando juntos

**Ejemplos**:
- `test_rag_retrieval.py` - Verifica búsqueda en FAISS con embeddings reales
- `test_indexing.py` - Verifica proceso completo de indexación
- `test_llm_context.py` - Verifica que el LLM recibe contexto correcto del RAG

**Características**:
- ⏱️ Moderadamente lentos (5-30 segundos)
- 📦 Requieren índice FAISS
- 🔍 Requieren modelo de embeddings
- ❌ No requieren LLM completo (pueden mockear respuestas)

**Cuándo correrlos**: Antes de commitear cambios importantes

---

### 3. **System Tests** (`tests/system/`)

**Qué testean**: El sistema completo end-to-end

**Ejemplos**:
- `test_bot_e2e.py` - Prueba el bot completo (Telegram → RAG → LLM → Respuesta)
- `test_evaluation.py` - Evaluación automática con casos de prueba reales

**Características**:
- 🐢 Lentos (1-5 minutos)
- 🤖 Requieren Ollama corriendo
- 📦 Requieren índice FAISS
- 🌐 Pueden requerir servicios externos (Telegram, n8n)

**Cuándo correrlos**: Antes de deploy a producción

---

## 🚀 Cómo ejecutar los tests

### Tests unitarios (rápidos)
```bash
# Todos los tests unitarios
pytest tests/unit/ -v

# Un test específico
pytest tests/unit/test_chunking.py -v
```

### Tests de integración
```bash
# Requieren índice FAISS actualizado
pytest tests/integration/ -v
```

### Tests de sistema (completos)
```bash
# Requieren Ollama corriendo
pytest tests/system/ -v
```

### Todos los tests
```bash
pytest tests/ -v
```

---

## 📊 Tests actuales

### ✅ Disponibles

| Test | Tipo | Archivo | Descripción |
|------|------|---------|-------------|
| Verificación RAG | Integration | `test_rag_retrieval.py` | Verifica búsquedas en índice FAISS |
| Evaluación Bot | System | `test_evaluation.py` | 5 casos de prueba con scoring |
| Chunking | Unit | `test_chunking.py` | Verifica división de textos |

### 🔜 Por implementar

- `test_table_extraction.py` (Unit) - Verificar extracción de tablas PDF
- `test_embeddings.py` (Unit) - Verificar generación de embeddings
- `test_indexing.py` (Integration) - Verificar indexación completa
- `test_bot_e2e.py` (System) - Prueba end-to-end completa

---

## 🎯 Criterios de calidad

### Tests unitarios
- ✅ Cobertura > 80% de funciones críticas
- ✅ Tiempo total < 10 segundos
- ✅ Sin dependencias externas

### Tests de integración
- ✅ Similarity scores > 0.85 en búsquedas exactas
- ✅ Top-3 debe incluir resultado correcto
- ✅ Tiempo total < 1 minuto

### Tests de sistema
- ✅ Puntaje promedio > 70/100 en evaluación
- ✅ 80% de casos de prueba aprobados
- ✅ Tiempo de respuesta RAG < 5 segundos

---

## 📝 Notas

- Los tests usan `pytest` como framework
- Configuración en `pytest.ini` (raíz del proyecto)
- Coverage reports con `pytest-cov`
- Los tests de integración/sistema requieren `backend/venv` activado
