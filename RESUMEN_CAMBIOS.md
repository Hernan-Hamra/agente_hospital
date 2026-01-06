# RESUMEN DE CAMBIOS - Agente Hospital

## ✅ IMPLEMENTADO (Listo para probar)

### 1. PROMPT MEJORADO
- ✅ Protocolo básico del Grupo Pediátrico integrado (DNI, credencial, etc.)
- ✅ Solo 3 obras sociales: ENSALUD, ASI, IOSFA
- ✅ Saludos cortos (1 línea), sin repetir presentación
- ✅ Prohibido inventar obras sociales, URLs o datos
- ✅ Parámetros optimizados: `num_predict=512`, `temperature=0.3`

### 2. MEMORIA CONVERSACIONAL
- ✅ Recuerda últimos 5 intercambios por usuario
- ✅ Comando `/clear` para limpiar historial
- ✅ No repite saludos si ya saludó antes

---

## 🧪 CÓMO PROBAR

```bash
# Reiniciar servicios:
cd /home/hernan/proyectos/agente_hospital/backend
pkill -f uvicorn; python3 -m uvicorn app.main:app --reload &

cd /home/hernan/proyectos/agente_hospital
pkill -f telegram_bot; python3 telegram_bot.py &
```

**Tests:**
1. Escribir "hola" → debe responder 1 línea corta
2. Escribir "hola" de nuevo → NO debe repetir presentación completa
3. "¿Qué obras sociales tenés?" → Solo ENSALUD, ASI, IOSFA
4. "Necesito info de OSDE" → "Solo tengo ENSALUD, ASI, IOSFA"
5. Consulta de procedimiento → Protocolo básico + específico de obra social

---

## 🔍 DIAGNÓSTICO DE VELOCIDAD (Patricia vs Hernán)

Ejecutar en **ambas máquinas**:

```bash
# Ver CPU
lscpu | grep "Model name"

# Ver GPU (si tienen)
nvidia-smi

# Ver modelo Ollama
ollama list

# Monitorear recursos durante query
htop  # En otra terminal mientras consultan
```

**Posibles causas de lentitud:**
- Patricia tiene GPU → Hernán no
- CPU de Hernán más lenta
- Hernán tiene más datos indexados

**Solución rápida:** Usar modelo cuantizado
```bash
ollama pull llama3.2:3b-q4_0  # Más rápido
```

---

## 📁 ARCHIVOS MODIFICADOS

- `backend/app/llm/client.py` - Nuevo prompt + memoria
- `telegram_bot.py` - Historial conversacional
- `backend/app/models.py` - Campo historial
- `backend/app/main.py` - Pasar historial al LLM

Ver detalles completos en: `MEJORAS_IMPLEMENTADAS.md`
