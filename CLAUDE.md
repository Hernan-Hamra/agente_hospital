# Reglas para Claude en este proyecto

## Regla 1: SIEMPRE consultar antes de modificar archivos de datos

**NUNCA** modificar archivos JSON de chunks, índices FAISS, o datos de entrenamiento sin consultar primero al usuario.

Antes de cualquier modificación:
1. Informar qué archivo se va a modificar
2. Explicar qué cambios se harán
3. Esperar confirmación explícita del usuario

Esto aplica especialmente a:
- `data/obras_sociales_json/**/*.json` (chunks de obras sociales)
- `backend/faiss_index/` (índice FAISS)
- `data/chroma_db/` (base de datos Chroma)
- Cualquier archivo que alimente el RAG

## Regla 2: No modificar FAISS sin orden explícita

El índice FAISS actual funciona con 100% de precisión usando query rewriter.
NO reindexar ni modificar FAISS hasta que el usuario lo ordene explícitamente.

## Regla 3: Mantener backups

Antes de modificar cualquier archivo de datos, verificar que exista backup o crearlo.

## Estado actual del proyecto (2026-01-26)

### RAG Systems
- **FAISS**: 74 chunks viejos, bge-large-en-v1.5, CON query rewriter → 100%
- **Chroma**: 32 chunks nuevos, bge-large-en-v1.5, SIN query rewriter → 88%

### Backups disponibles
- `data/obras_sociales_json/asi/2024-01-04_normas_chunks_flat.json.backup`
- `data/obras_sociales_json/ensalud/2024-01-04_normativa_chunks_flat.json.backup`
