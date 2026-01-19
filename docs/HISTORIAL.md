# Historial de Evolución - Agente Hospitalario

## Timeline

### 2026-01-05 - Inicio del proyecto
- Commit inicial
- Estructura base del proyecto
- RAG con FAISS + sentence-transformers
- LLM: Ollama con llama3.1

### 2026-01-05 - Mejoras RAG y Telegram
- Implementación de cosine similarity para RAG
- Primera integración con Telegram
- Threshold de similarity: 0.65

### 2026-01-06 - Agente con Function Calling
- Migración de pipeline a modo agente
- Implementación de `consulta_rag` como tool
- Prevención de alucinaciones (temperature 0.1, num_predict limitado)
- Cambio de modelo: llama3.1 → qwen2.5:3b (mejor function calling)

### 2026-01-10 - Pipeline JSON Offline
- Migración de chunking runtime a pipeline offline en 2 pasos
- Paso 1: DOCX/PDF → JSON intermedio
- Paso 2: JSON intermedio → JSON final
- Integración n8n + Telegram con webhook HTTPS
- Configuración ngrok para túnel HTTPS

### 2026-01-14 - Optimización de Prompts
- Prompt reducido: 45 → 40 líneas
- 10 casos de uso cubiertos en system prompt
- Fixes: saludos sin RAG, fuera de scope, no inventar errores
- Documentación de parámetros por impacto

### 2026-01-15 - Integración Groq
- Cliente LLM v2 con soporte Groq cloud
- Bot Telegram por long polling (alternativa a webhook)
- Informe ejecutivo para dirección (4 escenarios evaluados)
- Arquitectura de 7 escenarios definida

### 2026-01-18 - Sistema de Escenarios
- Configuración YAML para escenarios (`config/scenarios.yaml`)
- Detector de entidades (`backend/app/entities/`)
- Sistema de métricas (`backend/app/metrics/`)
- Router de consultas (`backend/app/scenarios/`)
- Documento de evaluación formal para Escenario 1

### 2026-01-19 - Limpieza de Documentación
- Eliminación de docs obsoletos (SETUP.md, PIPELINE_COMPLETO.md)
- Reorganización de estructura de documentación
- Reducción de claude.md para optimizar tokens

---

## Problemas Resueltos (Histórico)

| Fecha | Problema | Solución |
|-------|----------|----------|
| 2026-01-06 | Bot inventaba copagos y montos | Temperature 0.1 + prompt "NUNCA inventes" |
| 2026-01-06 | Respuestas cortadas post-RAG | num_predict=200 en segunda llamada |
| 2026-01-06 | Bot mostraba "(7 palabras)" | Eliminar conteo de ejemplos en prompt |
| 2026-01-06 | Confusión guardia vs turno | Prompt explícito "Guardia: NO orden" |
| 2026-01-06 | Respondía sobre OSDE sin datos | Lista explícita de obras sociales |
| 2026-01-10 | Chunking perdía tablas | Pipeline offline preserva tablas completas |
| 2026-01-14 | Saludo mencionaba ENSALUD | Regla "En saludos → IGNORA contexto RAG" |
| 2026-01-14 | Bot se disculpaba sin razón | Prohibir inventar errores pasados |
| 2026-01-15 | Latencia 180-200s en CPU | Integración Groq cloud (<2s) |

---

## Cambios de Modelo LLM

| Fecha | Modelo Anterior | Modelo Nuevo | Razón |
|-------|-----------------|--------------|-------|
| 2026-01-06 | llama3.1:8b | qwen2.5:3b | Mejor function calling, más rápido |
| 2026-01-15 | qwen2.5:3b (solo) | + Groq llama-3.3-70b | Latencia cloud <2s vs 180s local |

---

## Arquitectura de 7 Escenarios (2026-01-15)

| # | Escenario | LLM | Modo | Estado |
|---|-----------|-----|------|--------|
| 1 | CPU + Groq gratis + Consulta | Groq llama-3.3-70b | Consulta | Doc listo |
| 2 | GPU local + Consulta | Ollama qwen2.5:14b | Consulta | Pendiente |
| 3 | GPU local + Agente | Ollama llama3.1:8b | Agente | Pendiente |
| 4 | Groq pago + Consulta | Groq llama-3.1-8b | Consulta | Pendiente |
| 5 | Groq pago + Agente | Groq llama-3.1-8b | Agente | Pendiente |
| 6 | Híbrido (GPU + Groq fallback) | Mixto | Ambos | Pendiente |
| 7 | Comparativo final | Todos | Ambos | Pendiente |

---

## Métricas de Referencia

### Performance por Configuración

| Config | Latencia Simple | Latencia RAG | Tokens/s |
|--------|-----------------|--------------|----------|
| CPU + qwen2.5:3b | 30-40s | 180-200s | ~5 |
| Groq llama-3.3-70b | <1s | <2s | ~100 |
| GPU RTX 3060 (estimado) | 4-6s | 6-8s | 30-50 |

### Índice FAISS

| Fecha | Chunks Totales | ASI | ENSALUD | IOSFA |
|-------|----------------|-----|---------|-------|
| 2026-01-10 | 25 | 21 | 1 | 3 |

---

## Mejoras Futuras Documentadas

### Prioridad Alta
- [ ] Patrones de uso (logging estructurado)
- [ ] Completar evaluación de 7 escenarios

### Prioridad Media
- [ ] Preguntas frecuentes (clustering)
- [ ] Feedback automático (detección de repregunta)
- [ ] Añadir más obras sociales

### Prioridad Baja
- [ ] Dashboard de analytics
- [ ] Dockerización
- [ ] Integración con sistema hospitalario
