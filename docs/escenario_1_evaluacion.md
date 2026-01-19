# ESCENARIO 1: CPU + Groq Gratuito + Modo Consulta

## Documento de Evaluación Formal

**Fecha:** 2026-01-18
**Estado:** Preparado para ejecución
**Prioridad:** ⭐⭐⭐⭐⭐ (escenario clave para mostrar rápido)

---

## 1. ESTRUCTURA DE EVALUACIÓN

### 1.1 Objetivo Específico

Validar la viabilidad técnica y económica de usar **Groq Cloud (free tier)** con **llama-3.3-70b-versatile** para responder consultas administrativas del Grupo Pediátrico en modo stateless.

**Objetivos medibles:**
1. Confirmar que el flujo entity detection → RAG filtrado → LLM funciona correctamente
2. Medir tokens reales consumidos por consulta típica
3. Medir latencia end-to-end
4. Verificar precisión de las respuestas
5. Evaluar si 100 queries/día del free tier son suficientes para el caso de uso

---

### 1.2 Suposiciones (qué se da por válido)

| # | Suposición | Validación previa |
|---|------------|-------------------|
| 1 | GROQ_API_KEY está configurada en el entorno | Verificar con `echo $GROQ_API_KEY` |
| 2 | El índice FAISS está construido y contiene documentos de IOSFA, ENSALUD, ASI | Verificar con health check |
| 3 | Los aliases de entidades en `entities.yaml` cubren las variantes comunes | Revisar configuración |
| 4 | Groq free tier permite al menos 100 requests/día | Documentación de Groq |
| 5 | La red tiene conectividad a `api.groq.com` | Verificar con ping/curl |
| 6 | SQLite está disponible para persistir métricas | Python stdlib |

---

### 1.3 Alcance

#### ✅ QUÉ EVALÚA este escenario:

1. **Detección de entidades** - Precisión del matching determinístico
2. **Filtrado RAG** - Correcta segmentación por obra social
3. **Calidad de respuesta** - Coherencia, precisión, concisión
4. **Tokens consumidos** - Input + output reales (reportados por Groq)
5. **Latencia** - Tiempo total desde query hasta respuesta
6. **Costo** - USD calculado según precios de Groq
7. **Comportamiento sin entidad** - Correcta respuesta de aclaración

#### ❌ QUÉ NO EVALÚA este escenario:

1. Memoria conversacional (modo agente)
2. Function calling
3. Múltiples turnos de conversación
4. Escalabilidad bajo carga concurrente
5. Comportamiento con GPU
6. Modelos alternativos (Ollama)
7. Integraciones externas (Telegram, n8n)

---

## 2. MÉTRICAS CONCRETAS

### 2.1 Métricas Observables

| Métrica | Tipo | Unidad | Cómo se mide | Umbral éxito |
|---------|------|--------|--------------|--------------|
| `entity_detected` | Booleano | sí/no | EntityDetector.detect() | Debe coincidir con esperado |
| `entity_confidence` | Categórico | exact/alias/none | Tipo de match encontrado | exact o alias |
| `rag_executed` | Booleano | sí/no | Flag en router | true si hay entidad |
| `rag_status` | Categórico | ok/empty/low_similarity/error | Estado del RAG | ok o empty (ver nota) |
| `rag_chunks_count` | Entero | cantidad | Chunks recuperados | ≥ 1 |
| `rag_top_similarity` | Float | 0.0-1.0 | Score coseno del mejor chunk | ≥ 0.65 |
| `llm_executed` | Booleano | sí/no | Flag en router | true si hay entidad |
| `tokens_input` | Entero | tokens | response.usage.prompt_tokens | < 500 típico |
| `tokens_output` | Entero | tokens | response.usage.completion_tokens | < 100 típico |
| `latency_total_ms` | Float | milisegundos | Tiempo end-to-end | < 3000 ms |
| `cost_total` | Float | USD | Cálculo según precios | < $0.0001 por query |
| `response_words` | Entero | palabras | Conteo en respuesta | ≤ 30 (según prompt) |
| `success` | Booleano | sí/no | Sin excepciones | true |

### 2.2 Métricas de Calidad (evaluación manual)

| Métrica | Escala | Criterio |
|---------|--------|----------|
| Precisión | 0-100 | ¿La información es correcta y verificable? |
| Completitud | 0-100 | ¿Responde lo que se preguntó? |
| Concisión | 0-100 | ¿Es breve sin perder información clave? |
| Alucinación | sí/no | ¿Inventó información no presente en el contexto? |

**Umbral de aprobación:** Score total ≥ 70 (promedio de precisión + completitud + concisión)

### 2.3 Distinción: Aprobación Técnica vs Viabilidad Operativa

> **⚠️ Nota importante (Ajuste 3):** Un escenario puede **aprobar técnicamente** (score ≥ 70, métricas dentro de umbrales) pero **fallar operativamente**.
>
> **Ejemplo:** El Escenario 1 podría:
> - ✅ Pasar todas las métricas de calidad
> - ✅ Tener latencia aceptable
> - ✅ Responder correctamente
> - ❌ Pero el free tier de 100 queries/día no alcanza para el uso real proyectado
>
> **Esto NO es un error del escenario.** Es una **conclusión válida** que indica:
> - El enfoque técnico funciona
> - Pero requiere tier pago para producción
>
> El informe final debe distinguir claramente:
> 1. **Viabilidad técnica:** ¿Funciona correctamente?
> 2. **Viabilidad operativa:** ¿Es sostenible para el caso de uso real?

---

## 3. FLUJO DE DECISIÓN DEL BOT

```
┌─────────────────────────────────────────────────────────────────┐
│                         QUERY ENTRANTE                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1: ENTITY DETECTION (determinístico, ~0.1ms)              │
│  ─────────────────────────────────────────────────              │
│  • Normalizar query (lowercase, sin acentos)                    │
│  • Buscar en orden de prioridad: IOSFA → ENSALUD → ASI → GRUPO  │
│  • Primero nombre canónico, luego aliases                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
              ¿Detectó entidad?             │
                    │                       │
            ┌───────┴───────┐               │
            │               │               │
           NO              SÍ               │
            │               │               │
            ▼               ▼               │
┌───────────────────┐ ┌─────────────────────────────────────────┐
│ RESPUESTA FIJA    │ │ PASO 2: RAG FILTRADO                    │
│ ────────────────  │ │ ────────────────────                    │
│ "¿Para qué obra   │ │ • Generar embedding de query            │
│ social es la      │ │ • Buscar en FAISS con filtro de OS      │
│ consulta..."      │ │ • Aplicar threshold ≥ 0.65              │
│                   │ │ • Retornar top 2 chunks                 │
│ rag_executed=NO   │ │ • Construir contexto                    │
│ llm_executed=NO   │ │                                         │
│ tokens=0          │ │ rag_executed=SÍ                         │
│ cost=$0           │ └─────────────────────────────────────────┘
└───────────────────┘                       │
        │                                   ▼
        │           ┌─────────────────────────────────────────┐
        │           │ PASO 3: LLM (Groq)                      │
        │           │ ────────────────────                    │
        │           │ • Construir prompt:                     │
        │           │   - system: Asistente administrativo    │
        │           │   - user: CONTEXTO + PREGUNTA           │
        │           │ • Llamar Groq API:                      │
        │           │   - model: llama-3.3-70b-versatile      │
        │           │   - max_tokens: 150                     │
        │           │   - temperature: 0.1                    │
        │           │ • Extraer respuesta                     │
        │           │ • Registrar tokens reales               │
        │           │                                         │
        │           │ llm_executed=SÍ                         │
        │           └─────────────────────────────────────────┘
        │                                   │
        │                                   ▼
        │           ┌─────────────────────────────────────────┐
        │           │ PASO 4: MÉTRICAS Y PERSISTENCIA         │
        │           │ ───────────────────────────────         │
        │           │ • Calcular latencia total               │
        │           │ • Calcular costo USD                    │
        │           │ • Guardar en SQLite (tabla queries)     │
        │           │ • Retornar resultado con métricas       │
        │           └─────────────────────────────────────────┘
        │                                   │
        └───────────────────┬───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RESPUESTA FINAL                            │
│  {                                                              │
│    "respuesta": "...",                                          │
│    "entity": {...},                                             │
│    "rag_executed": true/false,                                  │
│    "llm_executed": true/false,                                  │
│    "metrics": {...}                                             │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 Reglas de Decisión Explícitas

| Condición | RAG | LLM | rag_status | Respuesta |
|-----------|-----|-----|------------|-----------|
| No detecta entidad | ❌ | ❌ | n/a | Mensaje fijo de aclaración |
| Detecta entidad + RAG con resultados | ✅ | ✅ | `ok` | Respuesta basada en contexto |
| Detecta entidad + RAG vacío (no existe info) | ✅ | ✅ | `empty` | "No tengo esa información" |
| Detecta entidad + RAG bajo similarity | ✅ | ✅ | `low_similarity` | "No tengo esa información" |
| Detecta entidad + RAG falla técnica | ✅ (falla) | ❌ | `error` | Error controlado |
| Error en Groq API | ✅ | ❌ (falla) | ok/empty | Error controlado |

> **Nota Ajuste 1:** Diferenciar `rag_status` permite comparar entre escenarios si un "no tengo info" es por diseño (datos no existen) o por falla técnica (índice corrupto, error de conexión). Esto es crítico para el Escenario 7 (comparativo).

---

## 4. CASOS DE PRUEBA DEL ESCENARIO 1

### 4.1 Matriz de Casos de Prueba

| # | Query | Entidad Esperada | RAG Expected | LLM Expected | Criterio de Éxito |
|---|-------|------------------|--------------|--------------|-------------------|
| 1 | "¿Qué documentos necesito para una consulta en IOSFA?" | IOSFA | ✅ | ✅ | Responde con requisitos de IOSFA |
| 2 | "¿Cuál es el mail de Mesa Operativa de ASI?" | ASI | ✅ | ✅ | Devuelve email correcto de ASI |
| 3 | "¿Necesito orden médica para guardia?" | ❌ None | ❌ | ❌ | Pide aclaración de obra social |
| 4 | "Requisitos para internación programada en IOSFA" | IOSFA | ✅ | ✅ | Lista requisitos de internación |
| 5 | "¿Cuál es el teléfono de ENSALUD?" | ENSALUD | ✅ | ✅ | Devuelve teléfono correcto |
| 6 | "dame el mail de fuerzas armadas" | IOSFA (alias) | ✅ | ✅ | Detecta alias, responde IOSFA |
| 7 | "hola, en qué puedo ayudarte" | ❌ None | ❌ | ❌ | Pide aclaración (no es consulta válida) |
| 8 | "requisitos para grupo pediátrico" | GRUPO_PEDIATRICO | ✅ | ✅ | Responde protocolo general |

### 4.2 Detalle de Casos de Prueba

#### CASO 1: Consulta típica con entidad explícita
```yaml
input: "¿Qué documentos necesito para una consulta en IOSFA?"
expected:
  entity_detected: true
  entity: "IOSFA"
  entity_confidence: "exact"
  rag_executed: true
  llm_executed: true
  response_contains: ["credencial", "DNI", "orden médica"] # al menos uno
success_criteria:
  - Detecta IOSFA correctamente
  - Recupera chunks de IOSFA (no de otras OS)
  - Respuesta menciona documentos requeridos
  - tokens_total < 500
  - latency_total_ms < 3000
failure_criteria:
  - No detecta entidad
  - Mezcla información de otras obras sociales
  - Respuesta vacía o error
  - Alucinación (inventa requisitos)
```

#### CASO 2: Consulta con dato específico (email)
```yaml
input: "¿Cuál es el mail de Mesa Operativa de ASI?"
expected:
  entity_detected: true
  entity: "ASI"
  rag_executed: true
  llm_executed: true
  response_contains_email: true
success_criteria:
  - Detecta ASI
  - Respuesta contiene un email válido
  - Email es de ASI (no de otra OS)
failure_criteria:
  - Devuelve email de otra obra social
  - No encuentra el email
  - Inventa un email
```

#### CASO 3: Consulta sin entidad (debe pedir aclaración)
```yaml
input: "¿Necesito orden médica para guardia?"
expected:
  entity_detected: false
  rag_executed: false
  llm_executed: false
  response: "¿Para qué obra social es la consulta (IOSFA, ENSALUD, ASI) o es para el Grupo Pediátrico? Volvé a hacer la pregunta especificándolo."
  tokens_input: 0
  tokens_output: 0
  cost_total: 0
success_criteria:
  - NO detecta entidad
  - NO ejecuta RAG
  - NO ejecuta LLM
  - Responde con mensaje de aclaración exacto
  - Costo = $0
failure_criteria:
  - Intenta adivinar la obra social
  - Llama al LLM
  - Responde con información genérica
```

#### CASO 4: Consulta compleja (internación)
```yaml
input: "Requisitos para internación programada en IOSFA"
expected:
  entity_detected: true
  entity: "IOSFA"
  rag_executed: true
  llm_executed: true
success_criteria:
  - Detecta IOSFA
  - Respuesta específica de internación (no consulta ambulatoria)
  - Menciona documentación de internación
failure_criteria:
  - Confunde con requisitos de consulta
  - Mezcla información
```

#### CASO 5: Consulta de contacto
```yaml
input: "¿Cuál es el teléfono de ENSALUD?"
expected:
  entity_detected: true
  entity: "ENSALUD"
  rag_executed: true
  llm_executed: true
  response_contains_phone: true
success_criteria:
  - Detecta ENSALUD
  - Respuesta contiene número de teléfono
  - Teléfono es de ENSALUD
failure_criteria:
  - Devuelve teléfono de otra OS
  - No encuentra teléfono
```

#### CASO 6: Consulta con alias de entidad
```yaml
input: "dame el mail de fuerzas armadas"
expected:
  entity_detected: true
  entity: "IOSFA"
  entity_confidence: "alias"
  matched_term: "fuerzas armadas"
  rag_executed: true
  llm_executed: true
success_criteria:
  - Detecta "fuerzas armadas" como alias de IOSFA
  - Responde con información de IOSFA
failure_criteria:
  - No reconoce el alias
  - Pide aclaración innecesaria
```

#### CASO 7: Saludo (no es consulta)
```yaml
input: "hola, en qué puedo ayudarte"
expected:
  entity_detected: false
  rag_executed: false
  llm_executed: false
  response: "¿Para qué obra social es la consulta..."
success_criteria:
  - NO intenta responder como si fuera consulta
  - Pide aclaración
  - Costo = $0
failure_criteria:
  - Responde con saludo (gastando tokens)
  - Inventa respuesta
```

> **⚠️ Decisión de diseño del Escenario 1:** Este comportamiento es **intencional** para minimizar costo en modo consulta stateless. En escenarios con modo agente (4, 5, 6), el bot SÍ podría responder saludos y mantener conversación, ya que el objetivo cambia de "mínimo costo" a "experiencia conversacional".

#### CASO 8: Grupo Pediátrico (entidad institucional)
```yaml
input: "requisitos para grupo pediátrico"
expected:
  entity_detected: true
  entity: "GRUPO_PEDIATRICO"
  entity_type: "institucion"
  rag_executed: true
  llm_executed: true
success_criteria:
  - Detecta GRUPO_PEDIATRICO como institución
  - Responde con protocolo general
failure_criteria:
  - Confunde con obra social
  - No detecta entidad
```

---

## 5. FORMA DE DOCUMENTACIÓN

### 5.1 Tabla de Resultados (plantilla)

| # | Query | Entidad | Detectó | RAG | LLM | Tokens | Latencia | Costo | Precisión | Estado |
|---|-------|---------|---------|-----|-----|--------|----------|-------|-----------|--------|
| 1 | ¿Qué documentos...IOSFA? | IOSFA | ✅/❌ | ✅/❌ | ✅/❌ | X | Xms | $X.XXXX | X/100 | ✅/❌ |
| 2 | ¿Mail de ASI? | ASI | | | | | | | | |
| 3 | ¿Orden médica guardia? | - | | | | | | | | |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### 5.2 Resumen Cuantitativo (plantilla)

```
═══════════════════════════════════════════════════════════════
                    RESUMEN ESCENARIO 1
═══════════════════════════════════════════════════════════════

Queries ejecutadas:     X
Exitosas:               X (XX%)
Fallidas:               X (XX%)

TOKENS
───────────────────────────────────────────────────────────────
Promedio input:         XXX tokens
Promedio output:        XX tokens
Promedio total:         XXX tokens
Máximo total:           XXX tokens

LATENCIA
───────────────────────────────────────────────────────────────
Promedio:               XXX ms
Mínima:                 XXX ms
Máxima:                 XXX ms
P95:                    XXX ms

COSTOS
───────────────────────────────────────────────────────────────
Costo promedio/query:   $X.XXXXXX USD
Costo total prueba:     $X.XXXXXX USD
Proyección 100q/día:    $X.XX USD/día
Proyección mensual:     $X.XX USD/mes

CALIDAD
───────────────────────────────────────────────────────────────
Precisión promedio:     XX/100
Completitud promedio:   XX/100
Concisión promedio:     XX/100
Alucinaciones:          X de Y queries
Score total:            XX/100

ENTITY DETECTION
───────────────────────────────────────────────────────────────
Detecciones correctas:  X/Y (XX%)
Falsos positivos:       X
Falsos negativos:       X

RAG
───────────────────────────────────────────────────────────────
Chunks recuperados avg: X.X
Similarity promedio:    X.XX
Filtrado correcto:      X/Y (XX%)

RAG STATUS (Ajuste 1)
───────────────────────────────────────────────────────────────
ok (info encontrada):   X queries
empty (no existe):      X queries
low_similarity:         X queries
error (falla técnica):  X queries

VIABILIDAD (Ajuste 3)
───────────────────────────────────────────────────────────────
Técnica:                ✅ Aprobado / ❌ No aprobado
Operativa:              ✅ Viable / ⚠️ Requiere tier pago / ❌ No viable
Conclusión:             [Texto libre]

═══════════════════════════════════════════════════════════════
```

### 5.3 Observaciones Cualitativas (plantilla)

```markdown
## Observaciones

### Fortalezas detectadas
1.
2.
3.

### Debilidades detectadas
1.
2.
3.

### Comportamientos inesperados
1.
2.

### Casos límite encontrados
1.
2.
```

### 5.4 Decisiones Tomadas (plantilla)

```markdown
## Decisiones Post-Evaluación

| Decisión | Justificación | Impacto |
|----------|---------------|---------|
| | | |
| | | |
```

### 5.5 Ajustes Sugeridos (plantilla)

```markdown
## Ajustes Sugeridos

### Inmediatos (antes de siguiente escenario)
- [ ]
- [ ]

### Corto plazo (antes de producción)
- [ ]
- [ ]

### Largo plazo (mejoras futuras)
- [ ]
- [ ]
```

---

## 6. CHECKLIST PRE-EJECUCIÓN

Antes de ejecutar el Escenario 1, verificar:

- [ ] `GROQ_API_KEY` está configurada en el entorno
- [ ] Índice FAISS existe y tiene documentos
- [ ] Health check pasa para escenario `groq_consulta`
- [ ] Base de datos de métricas está accesible
- [ ] Conexión a internet disponible
- [ ] Scripts de ejecución funcionan (`python scripts/run_scenario.py --list`)

---

## 7. COMANDO DE EJECUCIÓN

```bash
# Health check primero
python scripts/run_scenario.py --health

# Ejecutar batch de pruebas
python scripts/run_scenario.py --batch --scenario groq_consulta

# O query individual
python scripts/run_scenario.py --scenario groq_consulta --query "¿Qué documentos necesito para IOSFA?"
```

---

## 8. ARCHIVOS RELACIONADOS

| Archivo | Propósito |
|---------|-----------|
| [config/scenarios.yaml](config/scenarios.yaml) | Configuración del escenario groq_consulta |
| [config/entities.yaml](config/entities.yaml) | Diccionario de entidades y aliases |
| [backend/app/scenarios/consulta_router.py](backend/app/scenarios/consulta_router.py) | Router de consultas |
| [backend/app/llm/client_v2.py](backend/app/llm/client_v2.py) | Cliente Groq |
| [backend/app/entities/detector.py](backend/app/entities/detector.py) | Detector de entidades |
| [backend/app/metrics/collector.py](backend/app/metrics/collector.py) | Colector de métricas |
| [backend/app/metrics/database.py](backend/app/metrics/database.py) | Persistencia SQLite |
| [scripts/run_scenario.py](scripts/run_scenario.py) | Script CLI de ejecución |

---

*Documento generado el 2026-01-18. Listo para revisión antes de ejecución.*
