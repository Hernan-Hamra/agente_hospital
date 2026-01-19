# Agente Hospitalario - Grupo Pediátrico

## Claude Rules

### Restricciones
NO sin permiso: refactorizar, renombrar, mover archivos, cambiar lógica, optimizar, eliminar código.

### Permitido
Explicar, detectar errores (sin corregir), escribir código SOLO si se pide.

### NO REGRESSION RULE
**Si funciona y no fue pedido cambiarlo → NO SE TOCA.**

---

## Stack Actual (2026-01-19)

| Componente | Tecnología |
|------------|------------|
| LLM Local | Ollama qwen2.5:3b |
| LLM Cloud | Groq llama-3.3-70b / llama-3.1-8b |
| RAG | FAISS + sentence-transformers/all-MiniLM-L6-v2 |
| Backend | FastAPI |
| Bot | python-telegram-bot (polling) |
| Métricas | SQLite |

---

## Archivos Críticos

```
backend/app/
├── main.py                    # Endpoints /query, /health
├── llm/
│   ├── client.py              # Cliente Ollama (function calling)
│   └── client_v2.py           # Cliente Groq (nuevo)
├── rag/
│   ├── retriever.py           # Búsqueda FAISS, threshold 0.65
│   └── indexer.py             # index_from_json()
├── entities/
│   └── detector.py            # Detección de obra social
├── scenarios/
│   └── consulta_router.py     # Router modo consulta
└── metrics/
    ├── collector.py           # Colector de métricas
    └── database.py            # SQLite

config/
├── scenarios.yaml             # Configuración 7 escenarios
└── entities.yaml              # Diccionario entidades + aliases

scripts/
├── run_scenario.py            # CLI para ejecutar escenarios
├── convert_docs_to_json.py    # Paso 1: DOCX/PDF → JSON
├── clean_chunks_v2.py         # Paso 2: JSON → JSON final
└── index_data.py              # Reindexar FAISS

telegram_bot.py                # Bot Telegram (polling)
```

---

## Parámetros LLM Críticos

| Parámetro | Valor | Ubicación |
|-----------|-------|-----------|
| temperature | 0.1 | client.py, client_v2.py |
| num_predict | 120-200 | client.py |
| max_tokens | 150 | client_v2.py (Groq) |
| rag_threshold | 0.65 | retriever.py |
| rag_top_k | 3 | retriever.py |

---

## Datos Indexados

| Obra Social | Chunks | Indexado |
|-------------|--------|----------|
| ASI | 21 | ✅ |
| ENSALUD | 1 | ✅ |
| IOSFA | 3 | ✅ |
| GRUPO_PEDIATRICO | - | ❌ (en prompt) |

**Total FAISS**: 25 chunks

---

## Comandos Rápidos

```bash
# Backend
cd backend && source venv/bin/activate
python3 -m uvicorn app.main:app --reload

# Bot Telegram
python3 telegram_bot.py

# Ejecutar escenario
python scripts/run_scenario.py --scenario groq_consulta --query "..."

# Health check
curl http://localhost:8000/health

# Reindexar
python scripts/index_data.py
```

---

## Debugging

```bash
# Ver modelo configurado
grep OLLAMA_MODEL backend/.env

# Ver logs de tool calls
# Buscar: 🔧 Tool call: consulta_rag

# Verificar Groq
echo $GROQ_API_KEY
```

---

## 7 Escenarios de Evaluación

| # | Nombre | LLM | Modo | Doc |
|---|--------|-----|------|-----|
| 1 | Groq gratis + Consulta | llama-3.3-70b | Consulta | `docs/escenario_1_evaluacion.md` |
| 2 | GPU local + Consulta | qwen2.5:14b | Consulta | `docs/SETUP_GPU.md` |
| 3 | GPU local + Agente | llama3.1:8b | Agente | Pendiente |
| 4 | Groq pago + Consulta | llama-3.1-8b | Consulta | Pendiente |
| 5 | Groq pago + Agente | llama-3.1-8b | Agente | Pendiente |
| 6 | Híbrido | Mixto | Ambos | Pendiente |
| 7 | Comparativo | Todos | Ambos | Pendiente |

---

## Referencias

- Historial completo: `docs/HISTORIAL.md`
- Guía de tests: `TESTING.md`
- Setup principal: `README.md`
