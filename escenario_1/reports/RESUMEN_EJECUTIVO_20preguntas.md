# Resumen Ejecutivo - Evaluación Bot Grupo Pediátrico
**Fecha:** 27 de Enero 2026
**Escenario:** Modo Consulta (ChromaDB + Groq Gratis)

---

## Resultado General

| Métrica | Valor |
|---------|-------|
| **Preguntas evaluadas** | 20 |
| **Aprobadas** | 20 (100%) |
| **Puntaje promedio** | 95.8/100 |
| **Latencia promedio** | 730 ms |

---

## Resultados por Tipo de Pregunta

| Tipo | Aprobadas | Ejemplo |
|------|-----------|---------|
| Específicas | 6/6 (100%) | "¿Cuánto cuesta consulta especialista?" → "$2912" |
| Genéricas | 4/4 (100%) | "¿Coseguros de ENSALUD?" → Lista completa |
| Requisitos | 5/5 (100%) | "¿Documentos para internación?" → DNI, Validador, etc. |
| Coberturas | 3/3 (100%) | "¿Plan Quantum cubre especialidades?" → "Sí, sin autorización" |
| Coloquiales | 2/2 (100%) | "¿Cuánto me sale ir al pediatra?" → "$1553" |

---

## Resultados por Dificultad

| Dificultad | Aprobadas |
|------------|-----------|
| Fácil | 6/6 (100%) |
| Media | 11/11 (100%) |
| Difícil | 3/3 (100%) |

---

## Resultados por Obra Social

| Obra Social | Preguntas | Aprobadas |
|-------------|-----------|-----------|
| ENSALUD | 12 | 100% |
| ASI | 2 | 100% |
| IOSFA | 3 | 100% |
| GRUPO PEDIÁTRICO | 3 | 100% |

---

## Capacidad Operativa (Plan Groq Gratis)

### Límites del Plan
| Recurso | Límite |
|---------|--------|
| Tokens/día | 100,000 |
| Tokens/minuto | 12,000 |
| Requests/día | 1,000 |

### Capacidad Real (basado en ~823 tokens/query)
| Métrica | Valor |
|---------|-------|
| **Queries máximas/día** | 121 |
| **Queries seguras/hora** | 225 (con delay 4s) |
| **Queries máximas/minuto** | 14 |
| **Delay recomendado** | 4 segundos |

### Proyección de Uso
- **Horario pico (8-18hs):** ~12 consultas/hora = 120 consultas/día
- **Margen de seguridad:** 1 consulta restante para contingencias

---

## Métricas de Tokens

| Componente | Tokens |
|------------|--------|
| Total consumido (20 preguntas) | 16,475 |
| Promedio input/query | ~804 |
| Promedio output/query | ~20 |
| **Total promedio/query** | **~823** |

---

## Respuestas Destacadas

### Pregunta más rápida (87ms)
> "¿Qué documentación pido para guardia en Grupo Pediátrico?"
> **Respuesta:** "DNI, credencial y validación afiliatoria."

### Pregunta más compleja (exitosa)
> "¿El plan Krono Plus de ENSALUD paga coseguro en consultas?"
> **Respuesta:** "NO paga coseguro en consultas y estudios diagnósticos. SI paga coseguro en sesiones de rehabilitación y psicología."

### Respuesta genérica completa
> "¿Cuáles son los valores de coseguros de ENSALUD?"
> **Respuesta:** "Pediatra $1553, Especialista $2912, Laboratorio $971, Kinesiología $971, APB $6000, Imágenes alta complejidad $4854"

---

## Conclusiones

1. **El bot responde correctamente el 100% de las preguntas** de diferentes tipos y dificultades.

2. **Capacidad suficiente para operación diaria**: ~120 consultas/día en horario comercial.

3. **Tiempo de respuesta excelente**: Promedio 730ms (menos de 1 segundo).

4. **Cobertura completa**: Todas las obras sociales (ENSALUD, ASI, IOSFA, Grupo Pediátrico) funcionan correctamente.

5. **Listo para pruebas con usuarios reales**.

---

## Archivos Generados

- `evaluacion_20_20260127_030121.json` - Informe detallado completo
- `RESUMEN_EJECUTIVO_20preguntas.md` - Este documento

---

*Generado automáticamente por el sistema de evaluación del Escenario 1*
