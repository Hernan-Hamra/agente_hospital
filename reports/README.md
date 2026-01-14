# 📊 Reportes de Evaluación

Esta carpeta contiene los reportes de evaluación conversacional del bot hospitalario.

## 📁 Archivos Generados

Cada evaluación genera 2 archivos:

```
conversational_evaluation_2026-01-11_143052.txt     # Reporte legible
conversational_evaluation_2026-01-11_143052.json    # Reporte estructurado
```

## 🚀 Cómo Ejecutar

```bash
# Desde la raíz del proyecto
source backend/venv/bin/activate
python3 scripts/evaluate_conversational_bot.py
```

## 📊 Contenido del Reporte

### 1. Métricas Globales
- Precisión (25%)
- Completitud (20%)
- Concisión (15%)
- Habilidades Conversacionales (30%)
- Performance (10%)

### 2. Evaluación por Conversación
- **Conversación 1**: Usuario Nuevo (10 preguntas)
- **Conversación 2**: Usuario Avanzado (10 preguntas)
- **Conversación 3**: Flujo Completo (10 preguntas)

### 3. Detalles por Pregunta
- Pregunta y tipo
- Tiempos (RAG + LLM)
- Chunks RAG recuperados
- **Comparación con originales** (PDF/DOCX → JSON intermedio → Chunk)
- Respuesta del bot
- Evaluación detallada
- Puntaje individual

### 4. Análisis de Causas
- Problemas detectados (ranking)
- Causa raíz
- Impacto en enroladores
- Soluciones propuestas

### 5. Conclusiones
- Estado general (EXCELENTE/BUENO/NECESITA MEJORA)
- Fortalezas
- Áreas de mejora
- Plan de acción

## 🎯 Criterios de Evaluación

| Métrica | Peso | Objetivo | Qué Mide |
|---------|------|----------|----------|
| Precisión | 25% | ≥85% | Info correcta |
| Completitud | 20% | ≥80% | Info completa |
| Concisión | 15% | ≥70% | Respuestas breves |
| Habilidades Conv. | 30% | ≥75% | Saludos, reppreguntas, contexto |
| Performance | 10% | ≥80% | Tiempos aceptables |

## 📝 Tipos de Preguntas Evaluadas

- **Saludo inicial**: ¿Saluda apropiadamente?
- **Consulta básica**: ¿Responde correctamente?
- **Pregunta seguimiento**: ¿Mantiene contexto?
- **Pregunta ambigua**: ¿Pide clarificación?
- **Consulta tabla**: ¿Recupera tablas correctamente?
- **Pregunta compleja**: ¿Diferencia procedimientos?
- **Out of scope**: ¿Rechaza educadamente?
- **Multi-obra social**: ¿No mezcla información?
- **Reformulación**: ¿Reformula si no entendió?
- **Despedida**: ¿Se despide apropiadamente?

## 🔍 Trazabilidad

Cada respuesta incluye:

```
PDF/DOCX Original
    ↓
JSON Intermedio (_INTERMEDIO.json)
    ↓
JSON Final (chunk en _chunks_flat.json)
    ↓
RAG Recuperado
    ↓
Respuesta Bot
```

## 📈 Ejemplo de Uso

```bash
# Ver último reporte
cat reports/conversational_evaluation_latest.txt

# Ver métricas en JSON
cat reports/conversational_evaluation_latest.json | jq '.metricas_globales'

# Filtrar solo problemas
cat reports/conversational_evaluation_latest.txt | grep "⚠️"
```

## 🎯 Umbrales de Calidad

- **EXCELENTE**: Puntaje ≥ 80/100
- **BUENO**: Puntaje 70-79/100
- **NECESITA MEJORA**: Puntaje < 70/100
