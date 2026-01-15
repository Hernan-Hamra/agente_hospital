# Análisis de Costos - Groq LLM
**Fecha**: 2026-01-15
**Modelo usado**: llama-3.3-70b-versatile

---

## 1. Conversación Analizada (8 mensajes)

| # | Usuario | Bot | RAG | Tokens Est. |
|---|---------|-----|-----|-------------|
| 1 | "Dame el protocolo básico" | Respuesta directa | ❌ | ~400 |
| 2 | "Como enrolo para internación" | Respuesta directa | ❌ | ~450 |
| 3 | "Qué es la denuncia?" | Respuesta con RAG | ✅ | ~1,200 |
| 4 | "Como la notifico?" | Respuesta con RAG | ✅ | ~1,400 |
| 5 | "La denuncia quien la hace?" | Respuesta con RAG | ✅ | ~1,600 |
| 6 | "Le aviso al médico?" | Respuesta directa | ❌ | ~800 |
| 7 | "Ensalud" | Respuesta con RAG | ✅ | ~1,200 |
| 8 | "Si" (teléfono) | ERROR 429 | ✅ | ~1,000 |

**Total conversación**: ~8,050 tokens

---

## 2. Desglose de Tokens por Mensaje

### Sin RAG (respuesta directa)
```
System prompt:     ~250 tokens
Historial (avg):   ~200 tokens
Mensaje usuario:   ~30 tokens
Tool definition:   ~100 tokens
Respuesta:         ~50 tokens
─────────────────────────────
TOTAL:            ~630 tokens/mensaje
```

### Con RAG (2 llamadas al LLM)
```
Primera llamada:
  System prompt:    ~250 tokens
  Historial:        ~200 tokens
  Mensaje usuario:  ~30 tokens
  Tool definition:  ~100 tokens
  Decisión tool:    ~20 tokens
  ───────────────────────────
  Subtotal:        ~600 tokens

Segunda llamada (post-RAG):
  System prompt:    ~250 tokens
  Historial:        ~200 tokens
  Contexto RAG:     ~500 tokens (3 chunks)
  Mensaje usuario:  ~30 tokens
  Respuesta:        ~80 tokens
  ───────────────────────────
  Subtotal:        ~1,060 tokens

TOTAL CON RAG:    ~1,660 tokens/mensaje
```

---

## 3. Límites de Groq (Plan Gratuito)

| Límite | Valor | Fuente |
|--------|-------|--------|
| Requests/minuto | 30 RPM | [Groq Docs](https://console.groq.com/docs/rate-limits) |
| Tokens/minuto | 6,000 TPM | [Groq Community](https://community.groq.com/t/what-are-the-rate-limits-for-the-groq-api-for-the-free-and-dev-tier-plans/42) |
| Tokens/día | ~100,000 | Estimado de uso |

### ¿Por qué se agotó tan rápido?

Con la conversación de 8 mensajes:
- 4 mensajes sin RAG: 4 × 630 = 2,520 tokens
- 4 mensajes con RAG: 4 × 1,660 = 6,640 tokens
- **Total**: ~9,160 tokens

**Problema**: El límite de 6,000 tokens/minuto se alcanzó en ~4 mensajes con RAG.

---

## 4. Estimación de Capacidad (Plan Gratuito)

| Escenario | Mensajes/min | Mensajes/día | Conversaciones/día* |
|-----------|--------------|--------------|---------------------|
| Solo respuestas directas | ~9 | ~150 | ~15 |
| 50% con RAG | ~5 | ~80 | ~8 |
| 100% con RAG | ~3 | ~50 | ~5 |

*Asumiendo 10 mensajes por conversación

---

## 5. Precios Groq (Plan Pago)

| Modelo | Input ($/1M tokens) | Output ($/1M tokens) |
|--------|---------------------|----------------------|
| llama-3.3-70b-versatile | $0.59 | $0.79 |
| llama-3.1-8b-instant | $0.05 | $0.08 |

Fuente: [Groq Pricing](https://groq.com/pricing)

### Costo por mensaje estimado

| Tipo mensaje | Tokens | Costo (70b) | Costo (8b) |
|--------------|--------|-------------|------------|
| Sin RAG | 630 | $0.0005 | $0.00004 |
| Con RAG | 1,660 | $0.0012 | $0.00010 |

### Costo por conversación (10 mensajes, 50% RAG)

| Modelo | Costo/conversación |
|--------|-------------------|
| llama-3.3-70b | ~$0.008 |
| llama-3.1-8b | ~$0.0007 |

---

## 6. Proyección Mensual

### Escenario: 100 conversaciones/día

| Modelo | Costo/día | Costo/mes |
|--------|-----------|-----------|
| llama-3.3-70b | $0.80 | **$24/mes** |
| llama-3.1-8b | $0.07 | **$2.10/mes** |

### Escenario: 500 conversaciones/día

| Modelo | Costo/día | Costo/mes |
|--------|-----------|-----------|
| llama-3.3-70b | $4.00 | **$120/mes** |
| llama-3.1-8b | $0.35 | **$10.50/mes** |

### Escenario: 1000 conversaciones/día

| Modelo | Costo/día | Costo/mes |
|--------|-----------|-----------|
| llama-3.3-70b | $8.00 | **$240/mes** |
| llama-3.1-8b | $0.70 | **$21/mes** |

---

## 7. Recomendaciones

### Corto plazo (pruebas)
- Usar **llama-3.1-8b-instant** para desarrollo (~13x más barato)
- Implementar retry con backoff para rate limits
- Limitar historial a 5 mensajes (menos tokens)

### Producción
1. **Bajo volumen** (<100 conv/día): llama-3.1-8b → $2/mes
2. **Medio volumen** (100-500 conv/día): llama-3.1-8b → $2-10/mes
3. **Alto volumen** (>500 conv/día): Evaluar llama-3.3-70b para mejor calidad → $120-240/mes

### Optimizaciones para reducir costos
1. **Reducir prompt** ✅ HECHO (40% menos tokens)
2. **Reducir historial**: De 10 a 5 mensajes (-30% tokens)
3. **Cache de respuestas**: Preguntas frecuentes sin llamar al LLM
4. **Modelo híbrido**: 8b para preguntas simples, 70b para complejas

---

## 8. Configuración Actual

```env
# backend/.env
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile  # Cambiar a llama-3.1-8b-instant para ahorrar
```

### Para cambiar a modelo más económico:
```bash
# En backend/.env cambiar:
GROQ_MODEL=llama-3.1-8b-instant
```

---

## Fuentes
- [Groq Pricing](https://groq.com/pricing)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Community - Free Tier](https://community.groq.com/t/is-there-a-free-tier-and-what-are-its-limits/790)
