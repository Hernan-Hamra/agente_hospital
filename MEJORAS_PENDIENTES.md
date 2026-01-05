# Mejoras Pendientes - Agente Hospitalario

## CRÍTICO - Problemas actuales

### 1. LLM inventa información (alucinaciones)
**Problema**: llama3.2 (3B) es demasiado pequeño y creativo
**Soluciones**:
- [ ] Cambiar a modelo más grande: `mistral:7b-instruct` o `llama3.1:8b-instruct`
- [ ] Agregar ejemplos (few-shot) en el prompt
- [ ] Implementar validación de respuesta antes de enviar

### 2. No detecta entidades automáticamente
**Problema**: Usuario debe especificar obra social manualmente
**Solución**: ✅ IMPLEMENTADO - EntityExtractor
- [x] Detecta obra social del texto
- [x] Detecta tipo de consulta
- [x] Detecta urgencia
**Falta agregar**:
- [ ] Más obras sociales al diccionario (actualmente solo 8)
- [ ] Detección de errores de tipeo (fuzzy matching)
- [ ] Sinónimos y variaciones

### 3. Contexto irrelevante causa problemas
**Problema**: RAG recupera fragmentos sin relación y LLM los usa
**Soluciones**:
- [ ] Implementar threshold de relevancia (descartar chunks con score < 0.5)
- [ ] Re-ranker después del RAG (filtrar mejor)
- [ ] Validar que el contexto sea coherente con la pregunta

---

## MEDIO - Mejoras de calidad

### 4. Chunks muy pequeños pierden contexto
**Problema**: 500 caracteres puede partir tablas/listas
**Solución**:
- [ ] Probar chunk_size=1000 (duplicar tamaño)
- [ ] Usar "semantic chunking" (dividir por secciones, no por caracteres)
- [ ] Preservar estructura de tablas

### 5. No hay memoria de conversación
**Problema**: Cada pregunta es independiente
**Solución**:
- [ ] Implementar historial de conversación
- [ ] Pasar últimos 3-5 mensajes al LLM
- [ ] Mantener contexto de la obra social seleccionada

### 6. Respuestas muy largas
**Problema**: El LLM genera texto excesivo
**Solución**:
- [ ] Agregar `max_tokens` en la llamada a Ollama
- [ ] Prompt: "Respondé en máximo 200 palabras"
- [ ] Formato bullet points obligatorio

---

## BAJO - Mejoras de UX

### 7. Tiempo de respuesta lento (2 minutos)
**Opciones**:
- [ ] Cambiar a modelo más chico pero mejor: `qwen2.5:3b-instruct`
- [ ] Cachear respuestas frecuentes
- [ ] GPU (si es posible)

### 8. No hay feedback de progreso
**Solución**:
- [ ] WebSocket para streaming de respuesta
- [ ] Mensaje "Buscando en documentos..."  → "Generando respuesta..."

### 9. No loguea consultas
**Solución**:
- [ ] Guardar cada consulta en un archivo JSON
- [ ] Métricas: tiempo de respuesta, obra social, satisfacción

---

## ARQUITECTURA - Cambios estructurales

### 10. Separar retrieval de generation
**Problema**: RAG + LLM en un solo flujo
**Solución**:
- [ ] Paso 1: Retrieval (FAISS) → validar relevancia
- [ ] Paso 2: Solo si hay contexto relevante → LLM
- [ ] Si no hay contexto: respuesta prefabricada

### 11. Agregar validación de respuesta
**Antes de enviar al usuario**:
- [ ] Verificar que no mencione nombres de pacientes del contexto
- [ ] Verificar que no invente obras sociales
- [ ] Verificar que no contradiga el contexto

### 12. Sistema de templates para respuestas comunes
**Problema**: Reinventar la rueda en cada consulta
**Solución**:
- [ ] Template "Enrolamiento genérico" con variables
- [ ] Template "Documentación requerida" con variables
- [ ] Solo usar LLM para casos complejos

---

## DATOS - Calidad de información

### 13. Agregar metadatos más ricos
**Actualmente**: solo archivo + obra_social
**Agregar**:
- [ ] Fecha del documento (importante para vigencia)
- [ ] Versión/actualización
- [ ] Sección del documento (enrolamiento, derivaciones, etc.)
- [ ] Tipo de plan (si aplica)

### 14. Chunking inteligente
**Problema**: Chunks arbitrarios rompen contexto
**Solución**:
- [ ] Dividir por secciones lógicas (headers, listas)
- [ ] Mantener headers como contexto en cada chunk
- [ ] Chunks de tamaño variable según estructura

### 15. Agregar más obras sociales
**Actualmente**: 3 obras sociales (ENSALUD, ASI, IOSFA)
**Objetivo**: 130 obras sociales
- [ ] Script para procesar lotes de PDFs
- [ ] Validación automática de extracción
- [ ] Tests de calidad por obra social

---

## PROMPTS - Mejoras críticas

### 16. Agregar Few-Shot Examples
**En vez de solo instrucciones, mostrar ejemplos**:

```
Ejemplo 1:
Pregunta: "Hola"
Contexto: [irrelevante]
Respuesta: "Hola! Soy un asistente administrativo..."

Ejemplo 2:
Pregunta: "Qué necesito para ASI?"
Contexto: [DNI, credencial, ...]
Respuesta: "📋 Documentación requerida: DNI del paciente, ..."
```

### 17. Prompt de validación post-generación
**Después de generar respuesta**:
```
¿Esta respuesta menciona información que NO está en el contexto? SI/NO
¿Esta respuesta es útil para la pregunta? SI/NO
Si NO a cualquiera: RECHAZAR y regenerar
```

### 18. System prompt más estricto
```
NUNCA inventes:
- Nombres de pacientes
- Fechas específicas
- Números de teléfono
- Procedimientos no mencionados

Si no tenés información suficiente:
- Decí "No tengo información sobre [X] en mi base de datos"
- Sugerí contactar a la obra social
```

---

## TESTING - Asegurar calidad

### 19. Suite de tests automáticos
- [ ] 50 consultas de prueba con respuestas esperadas
- [ ] Test: "Hola" → NO debe mencionar pacientes
- [ ] Test: "Enrolar ASI" → DEBE incluir DNI
- [ ] Test: "Horario hospital" → "No tengo esa información"

### 20. Benchmarking de modelos
**Probar con diferentes modelos**:
- [ ] llama3.2:3b (actual - rápido pero impreciso)
- [ ] mistral:7b-instruct (balance)
- [ ] llama3.1:8b (lento pero preciso)
- [ ] qwen2.5:3b-instruct (rápido y preciso?)

---

## Priorización sugerida

**Semana 1** (Crítico):
1. Cambiar a `mistral:7b-instruct` o volver a `llama3.1:8b-instruct`
2. Agregar threshold de relevancia en RAG (0.5)
3. Agregar 100 obras sociales más al EntityExtractor
4. Agregar few-shot examples al prompt

**Semana 2** (Calidad):
5. Implementar validación de respuesta
6. Aumentar chunk_size a 1000
7. Agregar memoria de conversación (últimos 3 mensajes)

**Semana 3** (Escalabilidad):
8. Procesar y indexar las 130 obras sociales
9. Suite de tests automáticos
10. Logging de consultas

**Futuro**:
- Semantic chunking
- Re-ranker
- Sistema de templates
- Métricas y dashboard
