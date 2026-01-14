# 🧪 Guía de Tests - Agente Hospitalario

Sistema de tests organizado profesionalmente para el bot hospitalario RAG.

## 📊 Estado Actual

| Tipo | Tests | Estado | Tiempo |
|------|-------|--------|--------|
| **Unit** | 15/15 | ✅ 100% | 0.14s |
| **Integration** | 15/15 | ✅ 100% | 12.18s |
| **System** | 0/0 | ⏳ Disponible | N/A |

**Total**: 30 tests ejecutados, 30 pasados (100%)

---

## 🚀 Ejecución Rápida

```bash
# Tests rápidos (unitarios)
./run_tests.sh unit

# Tests de integración (requieren FAISS)
./run_tests.sh integration

# Tests de sistema (requieren Ollama)
./run_tests.sh system

# Todos los tests
./run_tests.sh all
```

---

## 📁 Estructura

```
tests/
├── unit/                     # Componentes aislados
│   └── test_chunking.py      # 15 tests (división de textos, overlap, tablas)
│
├── integration/              # Componentes conectados
│   └── test_rag_retrieval.py # 15 tests (búsquedas FAISS, similarity)
│
└── system/                   # End-to-end
    └── test_evaluation.py    # 5 casos de prueba con scoring
```

---

## 🔬 Tests Unitarios (15 tests)

**Archivo**: `tests/unit/test_chunking.py`
**Tiempo**: 0.14 segundos
**Requiere**: Nada (aislado)

### Qué testea:
- ✅ División de textos en chunks de 1800 chars
- ✅ Overlap de 300 chars entre chunks
- ✅ Preservación de metadata
- ✅ Conversión de tablas a texto
- ✅ Validación de tamaños
- ✅ Edge cases (texto vacío, espacios, tamaños exactos)

### Ejemplo:
```bash
pytest tests/unit/test_chunking.py -v
```

---

## 🔗 Tests de Integración (15 tests)

**Archivo**: `tests/integration/test_rag_retrieval.py`
**Tiempo**: 12.18 segundos
**Requiere**: Índice FAISS actualizado

### Qué testea:
- ✅ Integridad del índice FAISS (82 chunks)
- ✅ Búsquedas por obra social (ASI, IOSFA, ENSALUD)
- ✅ Búsqueda en tablas (59 tablas de ENSALUD)
- ✅ Búsqueda sin filtro
- ✅ Ranking por similarity (scores > 0.80)
- ✅ Edge cases (query vacía, obra social inexistente)

### Ejemplo:
```bash
# Asegurate de tener el índice actualizado
python3 scripts/index_data.py

# Ejecutar tests
pytest tests/integration/test_rag_retrieval.py -v
```

### Tests críticos:
- `test_search_contact_table`: Busca email de ASI (similarity > 0.86)
- `test_search_consulta_docs`: Busca requisitos IOSFA (similarity > 0.87)
- `test_search_tables`: Verifica que encuentra tablas de ENSALUD

---

## 🌐 Tests de Sistema (5 casos)

**Archivo**: `tests/system/test_evaluation.py`
**Tiempo**: ~3-5 minutos
**Requiere**: Ollama corriendo + índice FAISS

### Qué testea:
- ⏳ Casos de prueba end-to-end con scoring
- ⏳ Evaluación de completitud (40 pts)
- ⏳ Ausencia de errores (20 pts)
- ⏳ Brevedad (20 pts)
- ⏳ Uso correcto de RAG (10 pts)
- ⏳ Velocidad (10 pts)

### Casos de prueba:
1. Documentación consulta IOSFA (Fácil)
2. Documentación prácticas IOSFA (Fácil)
3. Diferencia guardia vs turno IOSFA (Media)
4. Email Mesa Operativa ASI (Fácil)
5. Internaciones programadas IOSFA (Media)

### Ejemplo:
```bash
# Iniciar Ollama primero
ollama serve

# En otra terminal
./run_tests.sh system
```

---

## 📝 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `pytest.ini` | Configuración de pytest |
| `run_tests.sh` | Script helper para ejecutar tests |
| `tests/README.md` | Documentación detallada de tipos de tests |
| `TESTING.md` | Esta guía rápida |

---

## 🎯 Criterios de Calidad

### Tests Unitarios
- ✅ Cobertura > 80% de funciones críticas
- ✅ Tiempo total < 10 segundos
- ✅ Sin dependencias externas

### Tests de Integración
- ✅ Similarity scores > 0.85 en búsquedas exactas
- ✅ Top-3 debe incluir resultado correcto
- ✅ Tiempo total < 1 minuto

### Tests de Sistema
- ⏳ Puntaje promedio > 70/100
- ⏳ 80% de casos aprobados
- ⏳ Tiempo RAG < 5 segundos

---

## 🛠️ Comandos Útiles

```bash
# Ejecutar un test específico
pytest tests/unit/test_chunking.py::TestChunkCreation::test_short_text_single_chunk -v

# Ejecutar con output detallado
pytest tests/unit/ -v -s

# Ejecutar con cobertura
pytest tests/ --cov=backend/app --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html

# Ejecutar solo tests lentos
pytest tests/ -m slow

# Ejecutar solo tests rápidos (exclude lentos)
pytest tests/ -m "not slow"
```

---

## 📦 Dependencias

Tests requieren:
- `pytest` - Framework de testing
- `pytest-cov` - Cobertura de código

Instalar con:
```bash
source backend/venv/bin/activate
pip install pytest pytest-cov
```

---

## ✅ Próximos Pasos

1. **Ejecutar tests antes de cada commit**
   ```bash
   ./run_tests.sh unit && ./run_tests.sh integration
   ```

2. **Ejecutar tests de sistema antes de deploy**
   ```bash
   ./run_tests.sh system
   ```

3. **Agregar más tests según necesidad**:
   - `test_table_extraction.py` (Unit)
   - `test_embeddings.py` (Unit)
   - `test_indexing.py` (Integration)
   - `test_bot_e2e.py` (System)

---

## 📞 Soporte

Para más detalles sobre cada tipo de test, ver: [tests/README.md](tests/README.md)

Para ejecutar evaluación automática legacy (sin pytest):
```bash
python3 scripts/evaluate_bot.py
```
