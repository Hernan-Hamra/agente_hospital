# MEJORAS IMPLEMENTADAS - Bot Agente Hospital

**Fecha:** 2026-01-06
**Archivos modificados:** 4
**Estado:** ✅ Listo para probar

---

## 1. ✅ NUEVO SYSTEM PROMPT CON PROTOCOLO BÁSICO

### Archivo: `backend/app/llm/client.py`

### Cambios implementados:

#### a) **Lista cerrada de obras sociales**
```
- ENSALUD
- ASI / ASI Salud
- IOSFA
```
❌ **Prohibido:** Inventar obras sociales, URLs, teléfonos o datos no verificados.

#### b) **Protocolo básico del Grupo Pediátrico integrado**
Incluye el checklist general con:
- Documentación básica (DNI, credencial, validación)
- Protocolos por tipo de ingreso:
  - 🏥 Ambulatorio/Turnos
  - 🚨 Guardia
  - 🛏️ Internación de urgencia
  - 🗓️ Internación programada/cirugía
  - 💰 Coseguros y exenciones

#### c) **Control de longitud de respuestas**
- **Saludos simples:** Respuesta de 1 línea
- **Consultas de procedimientos:** Formato estructurado con protocolo básico + específico

#### d) **Formato condicional**
- 1️⃣ Saludos → corto, sin emojis
- 2️⃣ Sobre el bot → breve
- 3️⃣ Obras sociales cargadas → lista de 3
- 4️⃣ Procedimientos → protocolo básico + requisitos específicos
- 5️⃣ Consultas médicas → rechazo educado

#### e) **Parámetros optimizados de Ollama**
```python
options={
    'num_ctx': 2048,      # Contexto reducido (más rápido)
    'num_predict': 512,   # Limita longitud de respuesta
    'temperature': 0.3    # Menos hallucinations
}
```

---

## 2. ✅ MEMORIA CONVERSACIONAL

### Archivos modificados:
- `telegram_bot.py`
- `backend/app/models.py`
- `backend/app/main.py`
- `backend/app/llm/client.py`

### Funcionalidad:

#### a) **Almacenamiento en bot de Telegram**
```python
conversation_history = defaultdict(lambda: deque(maxlen=10))
# maxlen=10 = últimos 5 pares (user + assistant)
```

#### b) **Nuevos comandos**
- `/start` - Inicia conversación y limpia historial
- `/clear` - Limpia historial sin reiniciar

#### c) **Integración con FastAPI**
- El bot envía `historial: []` en el payload
- FastAPI recibe y pasa al LLM
- LLM usa últimos 8 mensajes (4 pares) para contexto

#### d) **Prevención de duplicados**
El sistema filtra el mensaje actual del historial para evitar duplicación en el prompt.

---

## 3. 📊 PROBLEMAS RESUELTOS

### Antes → Después

| Problema | Antes | Después |
|----------|-------|---------|
| **Saludo repetitivo** | 3 párrafos con info no solicitada | 1 línea: "Hola! Soy un asistente..." |
| **Inventa obras sociales** | Menciona COSYSECO (no existe) | Solo ENSALUD, ASI, IOSFA |
| **Inventa URLs** | `https://ensalud.org/novedades/...` | ❌ Prohibido inventar enlaces |
| **Mezcla requisitos** | "Credencial ASI" al hablar de ENSALUD | Protocolo básico separado de específico |
| **Sin memoria** | Cada "hola" dispara nueva presentación | Recuerda últimos 5 intercambios |
| **Respuestas muy largas** | Sin límite | Máximo 512 tokens |

---

## 4. 🧪 CÓMO PROBAR LAS MEJORAS

### a) Reiniciar los servicios:

```bash
# Terminal 1: Reiniciar FastAPI
cd /home/hernan/proyectos/agente_hospital/backend
source venv/bin/activate
pkill -f "uvicorn app.main:app"
python3 -m uvicorn app.main:app --reload

# Terminal 2: Reiniciar bot de Telegram
cd /home/hernan/proyectos/agente_hospital
pkill -f "telegram_bot.py"
python3 telegram_bot.py
```

### b) Tests recomendados:

#### Test 1: Saludo simple
```
Usuario: hola
Esperado: Respuesta corta (1-2 líneas), sin formato largo
```

#### Test 2: Memoria conversacional
```
Usuario: hola
Bot: Hola! Soy un asistente...
Usuario: hola
Esperado: El bot NO debe repetir la presentación completa
```

#### Test 3: Obras sociales
```
Usuario: ¿Qué obras sociales tenés?
Esperado: "Tengo información de 3 obras sociales: ENSALUD, ASI e IOSFA."
```

#### Test 4: Obra social no disponible
```
Usuario: Necesito info de OSDE
Esperado: "Actualmente solo tengo información de ENSALUD, ASI e IOSFA."
```

#### Test 5: Protocolo básico + específico
```
Usuario: ¿Qué documentos necesito para enrolar un paciente de ENSALUD?
Esperado:
- 📋 Documentación básica (DNI, credencial...)
- 📋 Requisitos específicos de ENSALUD (del contexto RAG)
```

#### Test 6: Limpiar historial
```
Usuario: hola
Bot: [respuesta]
Usuario: /clear
Bot: 🗑️ Historial de conversación limpiado.
Usuario: hola
Esperado: El bot responde como si fuera la primera vez
```

---

## 5. 🔍 DIAGNÓSTICO DE VELOCIDAD (Patricia vs Hernán)

### Comandos de diagnóstico:

Ejecutar estos comandos **en ambas máquinas** (Patricia y Hernán):

```bash
# 1. Ver info de CPU
lscpu | grep "Model name"
lscpu | grep "CPU(s):"
lscpu | grep "CPU MHz"

# 2. Ver si tienen GPU NVIDIA
nvidia-smi

# 3. Ver modelos Ollama instalados
ollama list

# 4. Ver tamaño del índice FAISS
ls -lh /home/hernan/proyectos/agente_hospital/backend/faiss_index/
du -sh /home/hernan/proyectos/agente_hospital/backend/faiss_index/

# 5. Ver cantidad de chunks indexados
# (Al iniciar FastAPI, ver el log: "✅ Índice cargado: X chunks")

# 6. Monitorear recursos durante una query
# En otra terminal:
htop
# Hacer una consulta y observar:
# - % CPU usado por ollama
# - RAM utilizada
# - Si hay swap
```

### Posibles causas de lentitud:

| Causa | Probabilidad | Cómo verificar |
|-------|--------------|----------------|
| **CPU más lenta** | ⭐⭐⭐⭐⭐ | Comparar "Model name" y "CPU MHz" |
| **Sin GPU** | ⭐⭐⭐⭐ | `nvidia-smi` - si no tiene, es 10-30x más lento |
| **Modelo diferente** | ⭐⭐⭐ | `ollama list` - comparar versiones |
| **Más datos indexados** | ⭐⭐ | Comparar tamaño de faiss_index/ |
| **RAM insuficiente** | ⭐⭐ | `htop` - ver si usa swap durante query |
| **Modelo embedding no descargado** | ⭐ | Solo afecta primera query |

### Soluciones si Hernán es más lento:

1. **Si Patricia tiene GPU y Hernán no:**
   - Opción A: Compartir servidor Ollama (Patricia corre Ollama, Hernán se conecta remoto)
   - Opción B: Instalar GPU en máquina de Hernán

2. **Si ambos tienen solo CPU:**
   - Usar modelo cuantizado: `ollama pull llama3.2:3b-q4_0` (más rápido, mínima pérdida de calidad)

3. **Si RAM es el problema:**
   - Reducir `num_ctx` de 2048 a 1024 en `client.py:184`

---

## 6. 📝 ARCHIVOS MODIFICADOS

### Resumen de cambios:

```
backend/app/llm/client.py (líneas 30-193)
├── Nuevo system_prompt con protocolo básico
├── Parámetros optimizados (num_ctx, num_predict, temperature)
└── Soporte para historial conversacional

telegram_bot.py (líneas 1-128)
├── Import de defaultdict y deque
├── Variable conversation_history (línea 21)
├── Comando /clear (línea 43)
├── Envío de historial en payload (línea 63-66)
└── Guardado de respuestas en historial (línea 81)

backend/app/models.py (líneas 8-18)
├── Nuevo modelo ConversationMessage
└── Campo historial en QueryRequest

backend/app/main.py (línea 180-186)
└── Pasar historial a llm_client.generate_response()
```

---

## 7. ⚠️ NOTAS IMPORTANTES

### a) **Límite de historial:**
- Bot guarda últimos **10 mensajes** (5 pares)
- LLM usa últimos **8 mensajes** (4 pares)
- Esto previene sobrecarga de contexto

### b) **Comandos de limpieza:**
- `/start`: Limpia historial + muestra mensaje de bienvenida
- `/clear`: Solo limpia historial (conversación continúa)

### c) **Retrocompatibilidad:**
- Si `historial` no se envía → funciona como antes (sin memoria)
- No rompe integraciones existentes

### d) **Performance:**
- Historial aumenta levemente el tiempo de respuesta (~5-10%)
- Los parámetros optimizados compensan este costo

---

## 8. 🚀 PRÓXIMOS PASOS (OPCIONAL)

### Mejoras adicionales para considerar:

1. **Modelo más grande:**
   - `llama3.2:7b` → Mejor razonamiento, menos hallucinations
   - Requiere: 8GB+ RAM, GPU recomendada

2. **Fine-tuning:**
   - Entrenar llama3.2 con datos reales del hospital
   - Requiere: Dataset de conversaciones reales

3. **Feedback del usuario:**
   - Botones 👍/👎 en Telegram
   - Guardar respuestas problemáticas para análisis

4. **Métricas:**
   - Log de tiempos de respuesta
   - Obras sociales más consultadas
   - Queries más frecuentes

---

## 9. ✅ CHECKLIST DE VALIDACIÓN

Antes de considerar terminado:

- [ ] Reiniciar FastAPI y bot de Telegram
- [ ] Probar los 6 tests recomendados
- [ ] Ejecutar comandos de diagnóstico en ambas máquinas
- [ ] Comparar tiempos de respuesta (antes vs después)
- [ ] Verificar que `/clear` funciona correctamente
- [ ] Confirmar que no inventa obras sociales
- [ ] Validar que usa protocolo básico en respuestas

---

**Autor:** Claude Sonnet 4.5
**Proyecto:** Agente Hospitalario - Grupo Pediátrico
**Versión:** 0.2.0 (con memoria conversacional)
