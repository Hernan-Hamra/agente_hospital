# Bot de Consultas para Admisión - Propuesta Completa

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Problema a Resolver](#2-problema-a-resolver)
3. [Solución Propuesta](#3-solución-propuesta)
4. [Funcionalidades](#4-funcionalidades)
5. [Casos de Uso Cubiertos](#5-casos-de-uso-cubiertos)
6. [Demostración](#6-demostración)
7. [Sistema de Mejora Continua](#7-sistema-de-mejora-continua)
8. [Arquitectura Técnica](#8-arquitectura-técnica)
9. [Datos Requeridos](#9-datos-requeridos)
10. [Costos](#10-costos)
11. [Requisitos de Implementación](#11-requisitos-de-implementación)
12. [Plan de Implementación](#12-plan-de-implementación)
13. [Limitaciones](#13-limitaciones)
14. [Próximos Pasos](#14-próximos-pasos)

---

## 1. Resumen Ejecutivo

**Bot de Telegram para el equipo de Admisión** que responde consultas sobre obras sociales de forma instantánea.

| Aspecto             | Detalle                                      |
|---------------------|----------------------------------------------|
| Tecnología          | Búsqueda estructurada en base de datos (sin IA) |
| Tiempo de respuesta | < 100 ms                                     |
| Disponibilidad      | 24/7                                         |
| Escalabilidad       | Hasta 200+ obras sociales                    |
| Usuarios            | Equipo de admisión                           |

---

## 2. Problema a Resolver

### Situación actual
- El equipo de admisión consulta información de obras sociales múltiples veces al día
- La información está dispersa en:
  - Manuales impresos
  - Archivos compartidos
  - Conocimiento de compañeros
  - Consultas telefónicas a las obras sociales
- Cada consulta interrumpe el flujo de trabajo
- Riesgo de información desactualizada

### Impacto
- Tiempo perdido buscando información
- Errores por datos desactualizados
- Dependencia del conocimiento individual
- Inconsistencia en procedimientos

---

## 3. Solución Propuesta

### ¿Qué es?
Un bot de Telegram que centraliza toda la información de obras sociales en un solo lugar, accesible al instante desde el celular o computadora.

### ¿Qué hace?
- Responde consultas sobre documentación, teléfonos, mails, plazos y coseguros
- Muestra alertas cuando hay restricciones temporales (falta de pago, convenio suspendido)
- Registra todas las consultas para análisis, y mejora continua

### ¿Cómo funciona?
```
Empleado escribe: "internación ensalud"
                    ↓
Bot responde (instantáneo):
┌─────────────────────────────────────────────┐
│ 🏥 INTERNACIÓN - ENSALUD                    │
│                                             │
│ 📄 Documentación: DNI, Carnet de afiliación │
│ 📧 Mail denuncia: auditoria@ensalud.org     │
│ ⏰ Plazo: Dentro de las 24 horas            │
│ 📞 Teléfono: 11-66075765                    │
│                                             │
│ ⚠️ Internación programada requiere          │
│    autorización PREVIA.                     │
└─────────────────────────────────────────────┘
```

### Escalabilidad
- Diseñado para crecer de 3 obras sociales iniciales hasta 200+
- Agregar una nueva obra social = cargar sus datos en la base
- Sin límite de usuarios simultáneos

### ¿Por qué sin IA?

| Aspecto         | Bot SQL (este)       | Bot con IA             |
|-----------------|----------------------|------------------------|
| Precisión       | 100% (datos exactos) | ~90% (puede alucinar)  |
| Velocidad       | < 100 ms             | 1-3 segundos           |
| Costo operación | Mínimo               | Mayor (API de IA)      |

Para datos estructurados y conocidos → Bot SQL es la mejor opción.

---

## 4. Funcionalidades

### 4.1 Consultas básicas (todos los usuarios)
| Comando            | Descripción                        |
|--------------------|------------------------------------|
| `ambulatorio [OS]` | Info de ingreso ambulatorio/turnos |
| `internación [OS]` | Info de internación                |
| `guardia [OS]`     | Info de guardia                    |
| `traslados [OS]`   | Info de traslados                  |
| `coseguros [OS]`   | Valores de coseguros por plan      |

### 4.2 Comandos de supervisor (requieren código)

Los comandos de supervisor requieren un **código PIN** que provee Hernán. Esto permite que cualquier usuario autorizado pueda ejecutarlos sin necesidad de configuración especial.

| Comando                         | Descripción                  |
|---------------------------------|------------------------------|
| `/restriccion:PIN:OS:"MENSAJE"` | Agregar restricción temporal |
| `/quitar_restriccion:PIN:OS`    | Quitar restricción           |
| `/restricciones:PIN`            | Ver restricciones activas    |
| `/reporte:PIN`                  | Ver reporte semanal + CSV    |

**Ejemplo de uso:**
```
/restriccion:7842:ENSALUD:"Pagos pendientes desde enero. Solo se permite GUARDIA."
```

**Seguridad:**
- El código es un PIN numérico de 4 dígitos (ej: 7842)
- Patricia decide a quién compartir el código
- Si se filtra, Hernán lo cambia en minutos

### 4.3 Reporte de problemas (todos los usuarios)
| Comando                                | Descripción                         |
|----------------------------------------|-------------------------------------|
| `/reportar "descripción del problema"` | Reportar dato faltante o incorrecto |

**Notificación automática:** Cuando un usuario reporta un problema, se envía automáticamente un mail a Hernán con el detalle para su corrección.

---

## 5. Casos de Uso Cubiertos

### Por tipo de ingreso

| Tipo            | Información disponible                                 |
|-----------------|--------------------------------------------------------|
| **Ambulatorio** | Documentación, validador, portal, teléfono, coseguro   |
| **Internación** | Documentación, mail denuncia, plazo, portal, censo     |
| **Guardia**     | Documentación, validador, coseguro (generalmente exento) |
| **Traslados**   | Documentación, teléfono gestión                        |
| **Coseguros**   | Valores por plan y tipo de prestación                  |

### Casos especiales

| Situación                     | Comportamiento del bot                         |
|-------------------------------|------------------------------------------------|
| Restricción por falta de pago | Muestra alerta ⛔ + indica qué está permitido  |
| Convenio suspendido           | Muestra alerta ⛔ de bloqueo total             |
| Dato no encontrado            | Indica qué información falta                   |
| Consulta incompleta           | Pide obra social o tipo de ingreso             |

---

## 6. Demostración

### Ejemplos de consultas exitosas

```
👤 Empleado: ambulatorio ensalud
🤖 Bot:
🏥 AMBULATORIO - ENSALUD - Seguridad Social

📄 Documentación: DNI, Carnet de afiliación
🔗 Portal: https://ensalud.org/novedades/soy-prestador/
📞 Teléfono: 11-66075765
💰 Coseguro: Según plan (ver /coseguros ensalud)

⚠️ Especialidades quirúrgicas requieren autorización previa.
```

```
👤 Empleado: coseguros ensalud
🤖 Bot:
💰 COSEGUROS - ENSALUD

📋 Por plan:
• Delta Plus: Consulta $1456 | Especialista $2912
• Quantum: Consulta $1820 | Especialista $3640

🆓 Exentos de coseguro:
• HIV
• Oncología
• Internación de guardia
```

### Ejemplos con restricciones

```
👤 Empleado: internación ensalud
🤖 Bot:
⛔ ATENCIÓN: ENSALUD tiene pagos pendientes.
   Solo se permite ingreso por GUARDIA.

🏥 INTERNACIÓN - ENSALUD
[resto de la información normal]
```

### Ejemplos de consultas incompletas

```
👤 Empleado: hola
🤖 Bot:
Necesito más información para ayudarte.
Por favor indicá:
• Obra social (ENSALUD, ASI, IOSFA, etc.)
• Tipo de ingreso (ambulatorio, internación, guardia, traslados)

Ejemplo: "internación ensalud"
```

---

## 7. Sistema de Mejora Continua

El sistema tiene 3 componentes que trabajan juntos:

### 7.1 LOGS (Automático)

Cada consulta se registra automáticamente en la base de datos:

| Campo         | Descripción                | Ejemplo               |
|---------------|----------------------------|-----------------------|
| `fecha`       | Timestamp de la consulta   | 2026-02-03 14:30:00   |
| `user_id`     | ID de Telegram del usuario | 123456789             |
| `texto`       | Texto exacto del usuario   | "internacion ensalud" |
| `obra_social` | OS detectada (o NULL)      | ENSALUD               |
| `tipo_ingreso`| Tipo detectado (o NULL)    | internacion           |
| `exito`       | 1 = exitosa, 0 = fallida   | 1                     |

**¿Cuándo es exitosa una consulta?**
- ✅ Se detectó obra social
- ✅ Se detectó tipo de ingreso
- ✅ Se encontró el dato en la base

**¿Cuándo falla?**
- ❌ No se detectó obra social
- ❌ No se detectó tipo de ingreso
- ❌ Combinación no existe en la base

### 7.2 REPORTES DE USUARIO

Los empleados pueden reportar problemas directamente en el bot:

```
👤 Empleado: /reportar "ensalud cambió el mail de denuncia a nuevo@ensalud.org"
🤖 Bot: ✅ Reporte enviado. Gracias por ayudar a mantener la info actualizada.
```

El reporte queda registrado y **se envía automáticamente un mail a Hernán** para su corrección.

**Flujo del reporte:**
```
Empleado detecta error → /reportar → Se guarda en tabla reportes
                                   → Mail automático a Hernán
                                   → Hernán corrige dato en BD
                                   → Empleado ve info correcta
```

### 7.3 MÉTRICAS (desde los logs)

| Métrica                 | Fórmula                                 | Objetivo 1er mes |
|-------------------------|-----------------------------------------|------------------|
| **Tasa de éxito**       | exitosas / total × 100                  | > 85%            |
| **Adopción del equipo** | usuarios únicos / total empleados × 100 | > 80%            |
| **Consultas semanales** | COUNT consultas por semana              | > 100            |
| **Reportes procesados** | cerrados / totales × 100                | 100%             |

*Nota: Los objetivos asumen capacitación completa y datos bien cargados.*

### Reporte semanal

El supervisor puede solicitar `/reporte:PIN` y obtiene:

```
👤 Supervisor: /reporte:7842

🤖 Bot:
📊 REPORTE SEMANAL (27 ene - 3 feb)

📈 Uso general:
• Consultas totales: 156
• Consultas exitosas: 142 (91%)
• Consultas fallidas: 14 (9%)

👥 Adopción:
• Usuarios únicos: 8/12 (67%)

❌ Top 5 consultas fallidas:
1. "cama ensalud" (4 veces) → Agregar "cama" como sinónimo
2. "osde internacion" (3 veces) → OS no cargada
3. "swiss ambulatorio" (2 veces) → OS no cargada

📝 Reportes pendientes: 2

📎 Archivo adjunto: reporte_2026-02-03.csv
```

**Archivo CSV descargable:** El bot envía además un archivo CSV que se puede abrir en Excel con:
- Hoja 1: Resumen de métricas
- Hoja 2: Detalle de consultas fallidas
- Hoja 3: Reportes de usuarios pendientes

### Ciclo de mejora

```
┌─────────────────────────────────────────────────────────────┐
│                    CICLO DE MEJORA                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    LOGS ──────────► MÉTRICAS ──────────► ACCIONES          │
│      │                  │                    │              │
│      │                  │                    ▼              │
│      │                  │           ┌───────────────┐       │
│      │                  │           │ Agregar       │       │
│      │                  │           │ sinónimos     │       │
│      │                  │           │ Cargar nuevas │       │
│      │                  │           │ OS            │       │
│      │                  │           │ Corregir      │       │
│      │                  │           │ datos         │       │
│      │                  │           └───────────────┘       │
│      │                  │                    │              │
│      ▼                  ▼                    ▼              │
│  ┌────────┐       ┌──────────┐        ┌───────────┐        │
│  │Consulta│       │ Reporte  │        │ Bot       │        │
│  │fallida │       │ semanal  │        │ mejorado  │        │
│  └────────┘       └──────────┘        └───────────┘        │
│      │                                       ▲              │
│      │         REPORTES USUARIO              │              │
│      │              │                        │              │
│      └──────────────┴────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Arquitectura Técnica

```
┌─────────────────────────────────────────────────────────────┐
│                     TELEGRAM                                │
│                        │                                    │
│                        ▼                                    │
│              ┌─────────────────┐                            │
│              │   Bot Python    │                            │
│              │  (bot.py)       │                            │
│              └────────┬────────┘                            │
│                       │                                     │
│         ┌─────────────┼─────────────┐                       │
│         ▼             ▼             ▼                       │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                  │
│  │Normalizer │ │  Query    │ │  Logger   │                  │
│  │           │ │  Engine   │ │           │                  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                  │
│        │             │             │                        │
│        └─────────────┼─────────────┘                        │
│                      ▼                                      │
│              ┌───────────────┐                              │
│              │   SQLite DB   │                              │
│              │               │                              │
│              │ • obras_sociales                             │
│              │ • requisitos                                 │
│              │ • coseguros                                  │
│              │ • sinonimos                                  │
│              │ • restricciones                              │
│              │ • consultas_log                              │
│              │ • reportes                                   │
│              └───────────────┘                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente       | Función                                           |
|------------------|---------------------------------------------------|
| **Bot**          | Recibe mensajes de Telegram, orquesta respuesta   |
| **Normalizer**   | Traduce sinónimos ("turnos" → "ambulatorio")      |
| **Query Engine** | Busca en BD, aplica restricciones, formatea       |
| **Logger**       | Registra cada consulta para métricas              |
| **SQLite**       | Base de datos local, sin dependencias externas    |

---

## 9. Datos Requeridos

Para cargar cada obra social se necesita:

### Información básica
| Campo            | Ejemplo                      |
|------------------|------------------------------|
| Código           | ENSALUD                      |
| Nombre completo  | ENSALUD - Seguridad Social   |
| Tipo             | Sindical / Prepaga / Estatal |

### Por tipo de ingreso
| Campo            | Ambulatorio | Internación | Guardia | Traslados |
|------------------|-------------|-------------|---------|-----------|
| Documentación    | ✅          | ✅          | ✅      | ✅        |
| Validador/Portal | ✅          | ✅          | ✅      | -         |
| Mail denuncia    | -           | ✅          | -       | -         |
| Plazo denuncia   | -           | ✅          | -       | -         |
| Teléfono         | ✅          | ✅          | ✅      | ✅        |
| Coseguro         | ✅          | -           | ✅      | -         |
| Notas especiales | ✅          | ✅          | ✅      | ✅        |

### Coseguros (si aplica)
| Campo           | Ejemplo                              |
|-----------------|--------------------------------------|
| Plan            | Delta Plus                           |
| Tipo prestación | Consulta / Especialista / Práctica   |
| Valor           | $1456                                |
| Exentos         | HIV, Oncología                       |

---

## 10. Costos

### Costo de desarrollo (ABSORBIDO - Fase 0)

| Concepto                        | Horas | Valor mercado  | Costo cliente |
|---------------------------------|-------|----------------|---------------|
| Análisis del problema           | 4 hs  | $160.000       | $0            |
| Diseño de arquitectura          | 4 hs  | $160.000       | $0            |
| Desarrollo bot base (Python)    | 12 hs | $480.000       | $0            |
| Base de datos (SQLite schema)   | 4 hs  | $160.000       | $0            |
| Demo funcional con datos prueba | 6 hs  | $240.000       | $0            |
| Documentación técnica           | 4 hs  | $160.000       | $0            |
| Tests y validación              | 6 hs  | $240.000       | $0            |
| **TOTAL FASE 0**                | **40 hs** | **$1.600.000** | **$0**    |

**El desarrollo del bot está 100% absorbido.** El cliente ahorra ~$1.600.000 ARS (~$1.090 USD).
Solo paga por la carga y validación de datos (Fases 1-3) bajo el modelo **Tiempo y Materiales**.
Ver sección 15.4 para detalles del modelo de cotización.

### Costo de normalización de datos (único, primer mes)

Para cargar las ~200 obras sociales se necesita:

| Tarea                  | Descripción                                           | Costo                 |
|------------------------|-------------------------------------------------------|-----------------------|
| **Extracción con LLM** | Usar IA para extraer datos estructurados de PDFs/docs | Costo de API (tokens) |
| **Control manual**     | Validar y corregir datos extraídos                    | Horas de trabajo      |

**Proceso de normalización:**
```
Documentos dispersos          →    Tablas estructuradas
(PDFs, mails, manuales)            (mismo formato para todas)

┌──────────────────┐    ┌──────────────┐    ┌──────────────┐
│ PDF normativa OS │───►│ LLM extrae   │───►│ Supervisor   │
│ Mail de auditoría│    │ campos clave │    │ valida datos │
│ Manual interno   │    └──────────────┘    └──────────────┘
└──────────────────┘           │                    │
                               ▼                    ▼
                        ┌──────────────────────────────┐
                        │   Base de datos uniforme     │
                        │   (misma estructura para     │
                        │    todas las OS)             │
                        └──────────────────────────────┘
```

**¿Por qué es necesario?**
- Cada OS envía su información en formatos diferentes
- La normalización permite que una sola query sirva para cualquier OS
- Sin esto, habría que programar lógica diferente para cada OS

### Costo de operación mensual

| Componente    | Detalle                                              |
|---------------|------------------------------------------------------|
| Servidor      | Puede correr en cualquier PC encendida o VPS básico  |
| Base de datos | SQLite (incluido, sin costo)                         |
| API de IA     | No usa IA en operación                               |
| Telegram      | Gratis                                               |

### Opciones de hosting

| Opción          | Características                               |
|-----------------|-----------------------------------------------|
| PC del hospital | Sin costo adicional, requiere estar encendida |
| VPS básico      | DigitalOcean, Linode, etc.                    |
| Railway/Render  | Sin mantenimiento                             |

---

## 11. Requisitos de Implementación

### Técnicos
| Requisito | Detalle           |
|-----------|-------------------|
| Python    | 3.10 o superior   |
| RAM       | 512 MB mínimo     |
| Disco     | 100 MB            |
| Internet  | Conexión estable  |

### De datos
| Requisito                 | Responsable                 |
|---------------------------|-----------------------------|
| Información de cada OS    | Equipo de admisión / Enlace |
| Validación de datos       | Supervisor                  |
| Actualización periódica   | Supervisor                  |

### Organizacionales
| Requisito            | Detalle                              |
|----------------------|--------------------------------------|
| Token de Telegram    | Crear bot con @BotFather             |
| Definir supervisores | Quiénes pueden cargar restricciones  |
| Capacitación         | 30 minutos con el equipo             |

---

## 12. Plan de Implementación

### Fase 0: Desarrollo de solución (COMPLETADA - NO SE COBRA)

**Estado: ✅ Finalizada (40 horas invertidas)**
- [x] Análisis del problema (4 hs)
- [x] Diseño de arquitectura (4 hs)
- [x] Desarrollo del bot base - código Python (12 hs)
- [x] Base de datos SQLite - schema (4 hs)
- [x] Demo funcional con datos de prueba (6 hs)
- [x] Documentación técnica (4 hs)
- [x] Tests y validación (6 hs)

**Costo para el cliente: $0** (absorbido por Hernán con Claude Pro)
**Valor de mercado: $1.600.000 ARS (~$1.090 USD)**

---

### Fase 1: Carga de datos y validación (4 semanas)

**Semanas 1-4: Relevamiento, extracción y validación**
- [ ] Recolectar documentos de cada OS (PDFs, mails, manuales)
- [ ] Extraer datos con LLM hacia formato estructurado
- [ ] Cargar en tablas normalizadas (misma estructura para todas)
- [ ] Validación con supervisor
- [ ] **Ajustes de código:** Adaptaciones según necesidades específicas (10 hs)
- [ ] **Correcciones de datos:** Ajustar según feedback del supervisor

**Objetivo:** Tener TODAS las obras sociales cargadas y validadas.

---

### Fase 2: Prueba piloto (2 semanas)

**Semanas 5-6: Prueba con usuarios reales**
- [ ] Prueba con 2-3 usuarios piloto
- [ ] Monitoreo de consultas fallidas
- [ ] Ajustar sinónimos según uso real
- [ ] **Correcciones:** Corregir errores detectados en uso real
- [ ] Validar que los datos sean correctos

**Objetivo:** Detectar y corregir problemas antes del despliegue masivo.

---

### Fase 3: Implementación / Producción (2 semanas)

**Semanas 7-8: Despliegue completo**
- [ ] Desplegar para todo el equipo de admisión
- [ ] Capacitación grupal (30 min)
- [ ] Entregar código de supervisor a Patricia
- [ ] Activar logs y métricas
- [ ] Primer reporte semanal
- [ ] **Correcciones:** Ajustes finales post-capacitación

**Objetivo:** Bot en producción con todo el equipo usándolo.

---

### Fase 4: Mantenimiento (mensual, continuo)

**Abono mensual**
- [ ] Revisión de métricas y reportes semanales
- [ ] Cargar nuevas OS según demanda
- [ ] Agregar sinónimos según consultas fallidas
- [ ] **Correcciones:** Actualizar datos cuando cambian
- [ ] Soporte y corrección de bugs

**Objetivo:** Mantener el bot actualizado y funcionando correctamente.

---

## 13. Limitaciones

| Limitación                   | Implicancia                                                          |
|------------------------------|----------------------------------------------------------------------|
| Solo responde datos cargados | Si no está en la BD, dice "no tengo información"                     |
| Formato semi-estructurado    | Mejor resultado con "internación ensalud" que con preguntas largas   |
| Sin interpretación           | No entiende contexto complejo ni preguntas ambiguas                  |
| Actualización manual         | Los datos deben cargarse manualmente cuando cambian                  |

### Mitigaciones
- Los sinónimos permiten variaciones ("turnos" = "ambulatorio")
- El sistema de reportes permite identificar datos faltantes
- Las métricas muestran qué consultas fallan para mejorar

---

## 14. Próximos Pasos

### Fase 0: ✅ COMPLETADA
- Demo funcional lista
- Documentación lista

### Inmediatos (antes de Fase 1)
1. **Aprobación** - Validar esta propuesta con Patricia
2. **Demo en vivo** - Mostrar funcionamiento con casos reales
3. **Definir alcance** - Cuántas OS cargar

### Fase 1: Carga de datos (4 semanas)
4. **Relevamiento** - Recolectar docs de cada OS
5. **Extracción** - Extraer y estructurar datos (LLM)
6. **Validación** - Supervisor valida datos
7. **Correcciones** - Ajustar según feedback

### Fase 2: Prueba piloto (2 semanas)
8. **Piloto** - Probar con 2-3 usuarios
9. **Correcciones** - Ajustar según uso real

### Fase 3: Implementación (2 semanas)
10. **Capacitación** - Sesión de 30 min con todo el equipo
11. **Producción** - Despliegue completo
12. **Correcciones** - Ajustes finales

### Fase 4: Mantenimiento (continuo)
13. **Soporte** - Abono mensual con correcciones incluidas

---

## 15. Propuesta Comercial

### 15.1 Timeline (Gantt)

```
                ANTES  1    2    3    4    5    6    7    8    ...
                ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────
FASE 0: DESARROLLO (absorbido)
└─ ✅ Completado ████

FASE 1: CARGA DE DATOS (4 semanas)
├─ Relevamiento      ████
├─ Extracción        ████████████████
├─ Validación             ████████████████
├─ Correcciones           ████████████████

FASE 2: PRUEBA PILOTO (2 semanas)
├─ Prueba 2-3 usuarios              ████████
├─ Correcciones                          ████

FASE 3: IMPLEMENTACIÓN (2 semanas)
├─ Deploy                                     ████
├─ Capacitación                                   ████
├─ Correcciones                                   ████

FASE 4: MANTENIMIENTO (mensual)
└─ Soporte + Correcciones                             ████████...
```

**Fase 0:** Ya completada (demo funcional) - NO SE COBRA
**Fases 1-3:** 8 semanas de implementación
**Fase 4:** Abono mensual continuo

### 15.2 Esfuerzo Estimado por Fase

> **Modelo T&M:** Las horas indicadas son estimaciones para referencia. La facturación será por horas reales trabajadas.

#### Fase 0: Desarrollo de solución (ABSORBIDO)

| Tarea                           | Estado        | Horas Hernán | Costo cliente |
|---------------------------------|---------------|--------------|---------------|
| Análisis del problema           | ✅ Completado | 4            | $0            |
| Diseño de arquitectura          | ✅ Completado | 4            | $0            |
| Desarrollo bot base (Python)    | ✅ Completado | 12           | $0            |
| Base de datos (SQLite schema)   | ✅ Completado | 4            | $0            |
| Demo funcional con datos prueba | ✅ Completado | 6            | $0            |
| Documentación técnica           | ✅ Completado | 4            | $0            |
| Tests y validación              | ✅ Completado | 6            | $0            |
| **Subtotal Fase 0**             |               | **40**       | **$0**        |

*Absorbido por Hernán (incluye costo Claude Pro $100 USD/mes)*
*Valor de mercado: 40 hs × $40.000 = $1.600.000 ARS (~$1.090 USD) - NO SE COBRA*

---

#### Fase 1: Carga de datos y validación (4 semanas)

| Tarea                        | Responsable      | Horas Hernán   | Horas Cliente  |
|------------------------------|------------------|----------------|----------------|
| Relevamiento docs            | Cliente + Hernán | 4              | 8              |
| Extracción LLM (~0.5 hs/OS)  | Hernán           | **0.5 × N**    | -              |
| Validación datos             | Cliente + Hernán | 4              | **0.25 × N**   |
| **Ajustes de código**        | Hernán           | 10             | -              |
| **Correcciones datos**       | Hernán           | 4              | -              |
| **Subtotal Fase 1**          |                  | **22 + 0.5×N** | **8 + 0.25×N** |

*N = cantidad de obras sociales*
*Ajustes de código: adaptaciones según necesidades específicas detectadas durante la carga*

---

#### Fase 2: Prueba piloto (2 semanas)

| Tarea                   | Responsable | Horas Hernán | Horas Cliente |
|-------------------------|-------------|--------------|---------------|
| Coordinación piloto     | Ambos       | 4            | 2             |
| Soporte usuarios piloto | Hernán      | 4            | 2             |
| **Correcciones** (incluidas) | Hernán  | 4            | 2             |
| **Subtotal Fase 2**     |             | **12**       | **6**         |

---

#### Fase 3: Implementación / Producción (2 semanas)

| Tarea                        | Responsable      | Horas Hernán | Horas Cliente |
|------------------------------|------------------|--------------|---------------|
| Deploy servidor              | Hernán           | 4            | -             |
| Capacitación equipo          | Hernán           | 2            | 4 (asistir)   |
| Config supervisores          | Hernán + Cliente | 2            | 2             |
| Activar métricas             | Hernán           | 2            | -             |
| **Correcciones** (incluidas) | Hernán           | 2            | -             |
| **Subtotal Fase 3**          |                  | **12**       | **6**         |

---

#### Fase 4: Mantenimiento (mensual - abono)

| Tarea                        | Responsable | Horas/mes |
|------------------------------|-------------|-----------|
| Revisión métricas            | Hernán      | 2         |
| Carga nuevas OS              | Hernán      | 2         |
| Ajuste sinónimos             | Hernán      | 2         |
| **Correcciones** (incluidas) | Hernán      | 2         |
| **TOTAL MENSUAL**            |             | **8**     |

### 15.3 Estimación de Horas (200 OS)

> **Modelo T&M:** Las horas a continuación son estimaciones. El pago final será por horas reales trabajadas.

| Concepto                       | Cálculo estimado | Horas estimadas |
|--------------------------------|------------------|-----------------|
| **FASE 0 (desarrollo)**        |                  |                 |
| Horas Hernán                   | 40 hs            | ~~40 hs~~       |
| **Costo cliente Fase 0**       |                  | **$0**          |
|                                |                  |                 |
| **FASE 1 (carga datos)**       |                  |                 |
| Horas fijas (setup, ajustes)   | ~22 hs           | ~22 hs          |
| Horas por OS (~200)            | ~0.5 × 200       | ~100 hs         |
| **Subtotal estimado Fase 1**   |                  | **~122 hs**     |
|                                |                  |                 |
| **FASE 2 (piloto)**            |                  |                 |
| Horas estimadas                | ~12 hs           | **~12 hs**      |
|                                |                  |                 |
| **FASE 3 (implementación)**    |                  |                 |
| Horas estimadas                | ~12 hs           | **~12 hs**      |
|                                |                  |                 |
| **TOTAL ESTIMADO IMPLEMENTACIÓN** |               | **~146 hs**     |
|                                |                  |                 |
| **FASE 4 (mantenimiento)**     |                  |                 |
| Estimado por mes               | ~8 hs            | **~8 hs/mes**   |

*Fase 0 (40 hs de desarrollo) = $0 para el cliente - absorbido por Hernán.*
*Valor absorbido: ~$1.600.000 ARS (~$1.090 USD)*

### 15.4 Modelo de Cotización: Tiempo y Materiales (T&M)

#### ¿Qué es Tiempo y Materiales?

Este proyecto se cotiza bajo el modelo **Tiempo y Materiales (T&M)**:

| Aspecto              | Descripción                                                        |
|----------------------|--------------------------------------------------------------------|
| **Qué se paga**      | Horas reales trabajadas × tarifa hora                              |
| **Estimación**       | Se provee un total estimado basado en el alcance inicial           |
| **Variaciones**      | Si el scope cambia o hay imprevistos, las horas se ajustan         |
| **Transparencia**    | Se reportan las horas trabajadas al finalizar cada fase            |
| **Riesgo**           | El cliente asume el riesgo de desviaciones sobre la estimación     |

**¿Por qué este modelo?**
- Permite flexibilidad ante cambios de alcance o imprevistos
- No penaliza por requerimientos adicionales descubiertos durante la implementación
- El cliente paga por el trabajo real, sin márgenes de "colchón" por riesgo

#### Tarifa hora

| Concepto          | Valor                  |
|-------------------|------------------------|
| **Tarifa hora**   | $40.000 ARS (~$27 USD) |

*La tarifa incluye costos de LLM (Claude Pro) y procesamiento de datos.*

#### Estimación para 200 obras sociales

> **⚠️ IMPORTANTE:** Los valores a continuación son **estimaciones** basadas en el alcance conocido. El costo final puede variar según las horas reales trabajadas.

| Fase                           | Horas estimadas | Costo estimado ARS | Costo estimado USD |
|--------------------------------|-----------------|--------------------|--------------------|
| **Fase 0** (desarrollo)        | ~~40 hs~~       | ~~$1.600.000~~     | ~~$1.090~~         |
| **Costo cliente Fase 0**       | -               | **$0**             | **$0**             |
|                                |                 |                    |                    |
| **Fase 1** (carga datos)       | ~122 hs         | ~$4.880.000        | ~$3.320            |
| **Fase 2** (piloto)            | ~12 hs          | ~$480.000          | ~$330              |
| **Fase 3** (implementación)    | ~12 hs          | ~$480.000          | ~$330              |
| **TOTAL ESTIMADO**             | **~146 hs**     | **~$5.840.000**    | **~$3.980**        |
|                                |                 |                    |                    |
| **Fase 4** (mantenimiento/mes) | ~8 hs           | ~$320.000          | ~$220              |

*Fase 0: 40 horas de desarrollo = $0 para el cliente (absorbido por Hernán).*
*El cliente ahorra ~$1.600.000 ARS (~$1.090 USD) en desarrollo.*

#### Factores que pueden afectar la estimación

| Factor                                    | Impacto posible                 |
|-------------------------------------------|--------------------------------|
| Cantidad real de OS distinta a 200        | ±horas proporcionales          |
| Documentos de OS incompletos o dispersos  | +horas de relevamiento         |
| Cambios de requerimientos durante el proyecto | +horas de ajuste           |
| Validación más rápida de lo esperado      | -horas                         |
| Menos correcciones necesarias             | -horas                         |

#### Otros costos (opcionales)

| Concepto        | Costo                                   |
|-----------------|-----------------------------------------|
| **Hosting VPS** | ~$5-10 USD/mes (o servidor propio = $0) |
| **Telegram**    | Gratis                                  |

---

### 15.5 Modalidad de Pago: Horas Reales Trabajadas

#### Cómo funciona

1. **Al final de cada fase**, se reportan las horas reales trabajadas
2. **Se factura** por las horas efectivamente trabajadas × tarifa hora
3. **Sin sorpresas:** El cliente recibe el detalle de horas antes de pagar

#### Estimación de pagos (referencia)

> **Nota:** Estos montos son estimaciones. El pago real será por horas trabajadas.

| Fase   | Trabajo                       | Horas estimadas | Pago estimado  |
|--------|-------------------------------|-----------------|----------------|
| Fase 1 | Carga de datos                | ~122 hs         | ~$4.880.000    |
| Fase 2 | Prueba piloto                 | ~12 hs          | ~$480.000      |
| Fase 3 | Implementación/Producción     | ~12 hs          | ~$480.000      |
|        | **TOTAL ESTIMADO**            | **~146 hs**     | **~$5.840.000**|

#### Flujo de trabajo y facturación

```
FASE 1 (4 semanas)           FASE 2 (2 sem)    FASE 3 (2 sem)    FASE 4...
├────────────────────────────┼─────────────────┼─────────────────┼────────
│                            │                 │                 │
│  Carga de datos            │  Piloto         │  Producción     │  Mantenimiento
│                            │                 │                 │
│                       PAGO 1            PAGO 2            PAGO 3    ABONO
│                  (horas reales     (horas reales     (horas reales  mensual
│                   × $40.000)        × $40.000)        × $40.000)
```

#### Reporte de horas

Al finalizar cada fase, Hernán entrega:

| Dato                     | Ejemplo                                   |
|--------------------------|-------------------------------------------|
| Período                  | 1 feb - 28 feb 2026                       |
| Horas trabajadas         | 118 hs                                    |
| Detalle por tarea        | Extracción: 85 hs, Validación: 20 hs, etc.|
| Obras sociales cargadas  | 180 de 200                                |
| Monto a facturar         | 118 × $40.000 = $4.720.000                |

#### Condiciones

1. **Pago por horas reales:** Se factura únicamente por el trabajo efectivamente realizado
2. **Transparencia:** Detalle de horas disponible antes de cada facturación
3. **Sin penalidad:** Si una fase toma menos horas, se paga menos
4. **Ajuste automático:** Si hay más trabajo del estimado, las horas adicionales se facturan a la misma tarifa
5. **Mantenimiento:** A partir de la Fase 4, se establece un abono mensual estimado en ~8 hs/mes (~$320.000)

---

### 15.6 Funcionalidades Fuera de Alcance (Desarrollos Adicionales)

El bot base incluye todo lo documentado. Las siguientes funcionalidades **NO están incluidas** y serían desarrollos adicionales facturados por separado:

#### Integraciones externas

| Funcionalidad                                | Descripción                                      |
|----------------------------------------------|--------------------------------------------------|
| Integración con sistema de turnos            | Conexión con software de turnos del hospital     |
| Integración con historia clínica             | Acceso a datos del paciente desde el bot         |
| API de obras sociales en tiempo real         | Validación online directa con cada OS            |
| Conexión con facturación/nomenclador         | Consulta de códigos y valores                    |

#### Canales adicionales

| Funcionalidad                                | Descripción                                      |
|----------------------------------------------|--------------------------------------------------|
| Bot en WhatsApp                              | Mismo bot pero en WhatsApp Business              |
| App móvil dedicada                           | Aplicación nativa Android/iOS                    |

#### Módulos avanzados

| Funcionalidad                                | Descripción                                      |
|----------------------------------------------|--------------------------------------------------|
| Dashboard web para supervisores              | Panel con gráficos, reportes visuales, filtros   |
| Sistema de autorizaciones previas            | Gestión de solicitudes y aprobaciones            |
| Notificaciones automáticas                   | Alertas de vencimientos, renovaciones            |
| Bot para pacientes                           | Consultas de cobertura para afiliados            |
| Reportes avanzados con gráficos              | Exportación a PDF con visualizaciones            |

#### Cómo se manejan

- Se cotizan por separado según complejidad
- Se pueden agregar en cualquier momento (Fase 4 en adelante)
- Las nuevas tablas de BD se crean sin modificar el bot base
- Se mantiene compatibilidad con lo existente

**Nota:** Si durante el soporte mensual surge una necesidad que requiere desarrollo adicional, se cotiza aparte y se acuerda antes de implementar.

### 15.7 Responsabilidades

| Parte               | Compromiso                                          | Entregable                         |
|---------------------|-----------------------------------------------------|------------------------------------|
| **Hernán**          | ~~Desarrollo~~ ✅, extracción, deploy, soporte      | Bot funcionando con datos cargados |
| **Patricia/Enlace** | Proveer docs de cada OS                             | PDFs, mails, manuales por OS       |
| **Supervisor**      | Validar datos, gestionar restricciones              | Datos verificados, alertas activas |
| **Equipo Admisión** | Usar bot, reportar errores                          | Feedback, uso real                 |

### 15.8 Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUJO DE IMPLEMENTACIÓN                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CLIENTE                    HERNÁN                                  │
│  ───────                    ──────                                  │
│                                                                     │
│  1. Provee docs OS ────────► 2. Extrae con LLM                     │
│                                      │                              │
│                                      ▼                              │
│  4. Valida datos ◄──────── 3. Carga en BD                          │
│         │                                                           │
│         ▼                                                           │
│  ¿Correcto? ──NO──────────► 5. Corrige                             │
│         │                          │                                │
│        SI                          │                                │
│         │                          │                                │
│         ▼                          ▼                                │
│  6. Aprueba ──────────────► 7. Siguiente OS                        │
│                                                                     │
│  [Repetir para cada OS]                                             │
│                                                                     │
│  8. Piloto (2-3 usuarios) ─► 9. Ajustes finales                    │
│                                      │                              │
│                                      ▼                              │
│  10. Capacitación ◄──────── 11. Deploy producción                  │
│         │                                                           │
│         ▼                                                           │
│  12. GO LIVE ────────────────────────────────────────────►         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 15.9 Modelo de Contratación Seleccionado

**Este proyecto se contrata bajo el modelo Tiempo y Materiales (T&M).**

| Aspecto                  | Detalle                                            |
|--------------------------|----------------------------------------------------|
| **Modalidad**            | Horas reales trabajadas × tarifa hora ($40.000)    |
| **Estimación inicial**   | ~146 horas para implementación completa            |
| **Facturación**          | Al finalizar cada fase, por horas trabajadas       |
| **Flexibilidad**         | Ajuste automático si el alcance cambia             |
| **Riesgo**               | Cliente asume variaciones sobre la estimación      |

Ver sección 15.4 para detalles completos del modelo T&M.

### 15.10 Condiciones para el Éxito

| Requisito                    | Responsable    | Impacto si falta             |
|------------------------------|----------------|------------------------------|
| Docs de cada OS disponibles  | Cliente        | Demora en carga              |
| Validación en <48hs          | Cliente        | Bloquea avance               |
| Servidor disponible          | Cliente/Hernán | No puede deployar            |
| Supervisores definidos       | Cliente        | Sin gestión restricciones    |
| Tiempo para capacitación     | Cliente        | Baja adopción                |

---

## Contacto Técnico

Para consultas sobre implementación: **Hernán**

---

*Documento generado: Febrero 2026*
*Versión: Escenario 2 - Bot SQL sin IA*
