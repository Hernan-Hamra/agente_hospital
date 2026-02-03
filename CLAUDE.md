# Reglas para Claude en este proyecto

## Regla 1: SIEMPRE consultar antes de modificar archivos de datos

**NUNCA** modificar archivos JSON de chunks, índices o datos de entrenamiento sin consultar primero al usuario.

Antes de cualquier modificación:
1. Informar qué archivo se va a modificar
2. Explicar qué cambios se harán
3. Esperar confirmación explícita del usuario

Esto aplica especialmente a:
- `shared/data/chroma_db/` (base de datos ChromaDB compartida)
- `shared/data/obras_sociales_json/**/*.json` (chunks de obras sociales)
- `escenario_2/data/obras_sociales.db` (base de datos SQL)
- Cualquier archivo que alimente el RAG

## Regla 2: No modificar ChromaDB sin orden explícita

El índice ChromaDB actual funciona correctamente con query rewriter.
NO reindexar ni modificar ChromaDB hasta que el usuario lo ordene explícitamente.

## Regla 3: Mantener backups

Antes de modificar cualquier archivo de datos, verificar que exista backup o crearlo.

## Estructura del proyecto (2026-02-03)

```
agente_hospital/
├── escenario_1/     # Bot LLM Modo Consulta (sin memoria)
├── escenario_2/     # Bot SQL sin LLM
├── escenario_3/     # Bot LLM Modo Agente (con memoria)
├── shared/
│   └── data/
│       ├── chroma_db/          # ChromaDB compartido (escenario_1 y escenario_3)
│       └── obras_sociales_json/ # Chunks JSON fuente
├── _deprecated/     # Código viejo (backend/, FAISS, etc.)
└── data/            # Datos misceláneos
```

### Escenarios

| Escenario | Descripción | RAG | LLM | Memoria |
|-----------|-------------|-----|-----|---------|
| escenario_1 | Modo Consulta | ChromaDB | Groq | No |
| escenario_2 | Bot SQL | No | No | No |
| escenario_3 | Modo Agente | ChromaDB | Groq | Sí |

### Tests por escenario

- `escenario_1/tests/`: 12 tests (retriever, entity, query rewriter)
- `escenario_2/tests/`: 2 tests (basic, restricciones)
- `escenario_3/tests/`: 13 tests (basic, retriever)

### RAG System (ChromaDB)
- **Ubicación**: `shared/data/chroma_db/`
- **Modelo**: bge-large-en-v1.5
- **Chunks**: 32+ documentos
- **Query Rewriter**: Sí, mejora la precisión

### Deprecated
- FAISS index (movido a `_deprecated/backend/faiss_index/`)
- Backend original (movido a `_deprecated/backend/`)
