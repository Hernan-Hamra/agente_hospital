# Pendiente Resolver - Evaluación RAG

**Fecha**: 2026-01-21
**Estado**: ✅ RESUELTO - RAG funcionando con ~97% efectividad

---

## Estado Actual

| # | Query | Estado | Notas |
|---|-------|--------|-------|
| 1 | Documentos para consulta IOSFA | ✅ OK | - |
| 2 | Mail Mesa Operativa ASI | ✅ OK | - |
| 3 | Orden médica para guardia | ✅ OK | Pide aclaración correctamente |
| 4 | Internación IOSFA | ✅ OK | - |
| 5 | Teléfono ENSALUD | ✅ RESUELTO | Chunk CONTACTOS separado |
| 6 | Mail IOSFA | ✅ RESUELTO | Agregado consultas@iosfa.gob.ar + 0800-222-3300 |
| 7 | Hola | ✅ OK | Pide aclaración correctamente |
| 8 | Requisitos grupo pediátrico | ✅ OK | "Credencial ASI" es correcto (trabaja con ASI) |

---

## Mejoras Implementadas (2026-01-21)

1. **Script `convert_docs_to_json_flat.py` mejorado**:
   - Extrae contactos (emails/teléfonos) automáticamente con regex
   - Crea chunk "CONTACTOS" separado con alta prioridad
   - Detecta contexto del contacto (área/sector)

2. **IOSFA**: Agregados contactos al DOCX original
   - Mail: consultas@iosfa.gob.ar
   - Teléfono: 0800-222-3300 (días hábiles 8-16hs)

3. **Reindexación**: 86 chunks totales (antes 85)

---

## Arquitectura de Indexación Actual

```
Documento Original (.docx/.pdf)
        ↓
convert_docs_to_json_flat.py
        ↓
JSON con chunks (CONTACTOS + TABLAS + TEXTO)
        ↓
index_data.py (FAISS + bge-large-en-v1.5)
        ↓
Índice vectorial para RAG
```

**Limitación actual**: Reindexación completa (~2 min) al modificar cualquier obra social.

---

## Mejoras Futuras - Indexación Incremental

### Opción A: Reindexar Todo (ACTUAL)
- **Uso**: `python scripts/index_data.py`
- **Tiempo**: ~2 minutos para 86 chunks
- **Pros**: Simple, sin complejidad adicional
- **Contras**: No escala bien con muchas obras sociales
- **Recomendado**: Hasta ~100 chunks / 10 obras sociales

### Opción B: Filtro en Memoria
- **Concepto**: Mantener FAISS pero agregar campo `deleted: true` en metadata
- **Implementación**: Filtrar chunks "eliminados" en el retriever al buscar
- **Pros**:
  - No requiere migración de base de datos
  - Modificación mínima al código existente
- **Contras**:
  - Los chunks "eliminados" siguen ocupando espacio en el índice
  - Requiere reconstruir índice periódicamente para limpiar
  - **NO afecta calidad de respuestas** (solo filtra resultados)
- **Complejidad**: Media (~2-3 horas de desarrollo)

### Opción C: Migrar a ChromaDB
- **Concepto**: Reemplazar FAISS por ChromaDB (base vectorial con CRUD nativo)
- **Características de ChromaDB**:
  - Delete/Update por ID nativo
  - Persistencia automática
  - Filtros por metadata integrados
  - API similar a FAISS
- **Pros**:
  - Operaciones CRUD completas (Create, Read, Update, Delete)
  - No hay "basura" en el índice
  - Mejor para sistemas en producción
  - Gratis y local (igual que FAISS)
- **Contras**:
  - Requiere migración del código de indexación
  - Dependencia adicional (`pip install chromadb`)
  - Cambio en estructura de archivos (SQLite en vez de archivos FAISS)
- **Complejidad**: Alta (~4-6 horas de desarrollo)
- **Recomendado**: Cuando haya 50+ obras sociales o actualizaciones frecuentes

### Comparación de Opciones

| Aspecto | Opción A (Actual) | Opción B (Filtro) | Opción C (ChromaDB) |
|---------|-------------------|-------------------|---------------------|
| Calidad RAG | 100% | 100% | 100% |
| Tiempo update 1 OS | ~2 min | ~10 seg | ~1 seg |
| Espacio disco | Óptimo | Crece con deletes | Óptimo |
| Complejidad código | Baja | Media | Media |
| Escalabilidad | Baja | Media | Alta |
| Mantenimiento | Ninguno | Limpieza periódica | Ninguno |

### Decisión Actual
**Quedamos con Opción A** hasta que:
- Tengamos más de 10 obras sociales, o
- El tiempo de reindexación supere 5 minutos, o
- Necesitemos actualizaciones muy frecuentes (varias por día)

---

## Archivos Relevantes

| Archivo | Descripción |
|---------|-------------|
| `backend/scripts/convert_docs_to_json_flat.py` | Convierte DOCX/PDF a JSON chunks |
| `scripts/index_data.py` | Indexa JSONs en FAISS |
| `backend/faiss_index/` | Índice vectorial |
| `data/obras_sociales_json/` | JSONs de chunks |
| `scripts/evaluate_rag_quality.py` | Evaluación de calidad RAG |
| `docs/COMPARACION_TABLAS.md` | Comparación tablas vs chunks |
