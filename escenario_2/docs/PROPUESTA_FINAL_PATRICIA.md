# Propuesta Técnica y Comercial

**Febrero 2026 – Versión Final**

## SISTEMA BOT OPERATIVO DE ADMISIÓN
### Grupo Pediátrico

---

**Presentado por:**

**Hernán Hamra**
Arquitectura y Desarrollo de Sistemas
Tel: 11-5317-1213
Email: hamrahernan@gmail.com

---

## Contenido

1. [Nota de Presentación](#nota-de-presentación)
2. [Resumen Ejecutivo](#1-resumen-ejecutivo)
3. [Problema a Resolver](#2-problema-a-resolver)
4. [Solución Propuesta](#3-solución-propuesta)
5. [Estado Actual del Proyecto](#4-estado-actual-del-proyecto)
6. [Arquitectura Técnica](#5-arquitectura-técnica)
7. [Plan de Implementación](#6-plan-de-implementación)
8. [Estimación de Esfuerzo](#7-estimación-de-esfuerzo)
9. [Modelo Comercial](#8-modelo-comercial)
10. [Estimación Económica y Duración](#9-estimación-económica-y-duración)
11. [Infraestructura y Costos Operativos](#10-infraestructura-y-costos-operativos)
12. [Condiciones Operativas](#11-condiciones-operativas)
13. [Impacto Operativo](#12-impacto-operativo)
14. [Alcance](#13-alcance)
15. [Próximos Pasos](#14-próximos-pasos)
16. [Consideraciones Comerciales](#15-consideraciones-comerciales)
17. [Cierre](#16-cierre)
18. [Anexo Técnico](#anexo-técnico)

---

## Nota de Presentación

Sra. Patricia Rivas:

Por medio del presente documento se presenta la propuesta formal para la implementación del Sistema Bot Operativo de Admisión del Grupo Pediátrico.

El objetivo del proyecto es ordenar, estructurar y centralizar la información operativa vinculada a obras sociales, reduciendo tiempos administrativos, errores y dependencia de conocimiento informal.

La solución ya cuenta con una base técnica desarrollada y una demo funcional operativa. La presente propuesta detalla el alcance, el plan de implementación, el modelo económico y los costos operativos asociados, con estimaciones controladas y techo presupuestario definido.

El proyecto está planteado con foco en:
- Bajo riesgo técnico
- Control presupuestario
- Implementación gradual
- Medición operativa desde el primer día

Quedo a disposición para revisar cada sección en detalle y coordinar una demo en vivo.

Atentamente,

**Hernán Hamra**

---

## 1. Resumen Ejecutivo

Se propone la implementación de un Sistema Bot Operativo de Admisión, diseñado para centralizar y responder consultas internas sobre obras sociales de manera inmediata, estructurada y auditable.

El sistema ya cuenta con una demo funcional operativa, desarrollada y validada según los lineamientos solicitados.

| Aspecto             | Detalle                                        |
|---------------------|------------------------------------------------|
| Tecnología          | Base de datos estructurada (sin LLM en operación) |
| Canal               | Telegram                                       |
| Tiempo de respuesta | < 100 ms                                       |
| Disponibilidad      | 24/7                                           |
| Escalabilidad       | Hasta 200+ obras sociales                      |
| Usuarios            | Equipo de admisión                             |

---

## 2. Problema a Resolver

Actualmente la información de obras sociales:
- Está dispersa (PDFs, mails, manuales, conocimiento informal)
- Genera interrupciones operativas
- Produce inconsistencias
- Depende de validaciones manuales

**Impacto:**
- Tiempo improductivo
- Riesgo de errores
- Dependencia del conocimiento individual
- Falta de trazabilidad

---

## 3. Solución Propuesta

Se propone la implementación de un Sistema Bot Operativo de Admisión, diseñado para centralizar, estructurar y disponibilizar la información de obras sociales de manera inmediata y auditable.

**El sistema permitirá:**
- Centralizar la información actualmente dispersa
- Responder consultas estructuradas por tipo de ingreso
- Gestionar restricciones temporales (ej. suspensión por falta de pago)
- Registrar métricas de uso y tasa de éxito
- Generar reportes automáticos de actividad
- Incorporar mejoras continuas basadas en datos reales de uso

### Ejemplos de consultas solicitadas

Durante las reuniones iniciales se definieron casos concretos que el sistema ya resuelve en su versión demo:
- Consulta de ingreso ambulatorio por obra social
- Requisitos de internación y plazos de denuncia
- Consulta de valores de coseguro por plan
- Gestión de restricciones temporales ante situaciones administrativas
- Reportes semanales de uso para supervisión

Estos casos serán refinados y validados en la Fase 1 de carga y normalización de datos.

**El sistema no utiliza IA en producción, lo que garantiza:**
- Exactitud del dato cargado
- Respuesta inmediata (<100 ms)
- Costos operativos mínimos
- Total control sobre la información

Para el detalle completo de funcionalidades, arquitectura y modelo de métricas, ver [Anexo Técnico](#anexo-técnico).

---

## 4. Estado Actual del Proyecto

### Fase 0 – Desarrollo (Finalizada)

El proyecto cuenta actualmente con una base técnica desarrollada y validada mediante pruebas reales.

**Durante esta etapa se realizaron:**
- Investigación técnica y pruebas de concepto para asegurar un modelo operativo sin dependencia de LLM en producción
- Diseño de arquitectura escalable
- Desarrollo del Bot en Python
- Diseño y normalización de base de datos
- Implementación de sistema de logs y métricas
- Desarrollo de comandos de supervisión
- Demo funcional operativa conforme a los requerimientos solicitados

La etapa inicial permitió reducir significativamente el riesgo técnico del proyecto y validar su viabilidad operativa.

**Esta fase fue íntegramente asumida sin impacto económico para la institución.**

---

## 5. Arquitectura Técnica

- Bot en Python
- Base SQLite
- Sistema de normalización
- Motor de consulta estructurado
- Sistema de logs
- Reporte semanal en CSV

El sistema está diseñado para crecer sin rediseño estructural.

---

## 6. Plan de Implementación

### Fase 1 – Carga y Validación de Datos (4 semanas)
- Relevamiento documental
- Extracción estructurada con LLM
- Carga en base
- Validación con supervisor
- Ajustes y correcciones

### Fase 2 – Despliegue Inicial Controlado (2 semanas)
- Uso con grupo reducido
- Monitoreo de métricas
- Ajustes por uso real

### Fase 3 – Implementación Productiva (2 semanas)
- Deploy
- Capacitación
- Activación de métricas
- Puesta en producción

### Fase 4 – Mantenimiento Mensual
- Soporte
- Actualizaciones
- Carga de nuevas OS
- Ajuste de sinónimos
- Revisión de métricas

### Gantt Timeline estimado (8 semanas)

```
SEMANAS →        1    2    3    4    5    6    7    8
               ├────┼────┼────┼────┼────┼────┼────┼────┤

FASE 1
Carga y validación de datos
               ████████████████

FASE 2
Despliegue Inicial Controlado
                              ████████

FASE 3
Implementación productiva
                                        ████████

FASE 4
Mantenimiento mensual
                                                  ░░░░░░░░░░→
```

---

## 7. Estimación de Esfuerzo

**Alcance:** implementación para 200 obras sociales

| Fase    | Descripción                                    | Horas estimadas |
|---------|------------------------------------------------|-----------------|
| Fase 0  | Desarrollo inicial (finalizada)                | —               |
| Fase 1  | Parametrización, extracción y carga estructurada | ~150–170 hs   |
| Fase 2  | Despliegue Inicial Controlado y ajustes        | ~15 hs          |
| Fase 3  | Implementación operativa y capacitación        | ~15 hs          |
| **Total estimado implementación** |                        | **~180 hs**     |
| **Techo operativo máximo** |                               | **200 hs**      |
| Mantenimiento mensual promedio |                           | ~8 hs           |

La estimación base del proyecto es de aproximadamente 180 horas efectivas de trabajo.

**El proyecto no superará las 200 horas sin aprobación previa y expresa del cliente.**

---

## 8. Modelo Comercial

### Modalidad: Tiempo y Materiales (T&M) con control operativo

El proyecto se ejecuta bajo modalidad Tiempo y Materiales con seguimiento semanal y validación por etapa.

### Principios del modelo
- Se facturan exclusivamente horas efectivamente trabajadas.
- Cada fase cuenta con una estimación base.
- Se enviará reporte semanal de horas acumuladas.
- Cualquier posible desvío respecto de la estimación será informado antes de continuar.
- No se ejecutarán horas adicionales sin aprobación previa.

### Esto garantiza
- Transparencia total
- Control presupuestario
- Visibilidad anticipada de desvíos
- Ausencia de ajustes retroactivos
- Gobernanza del proyecto

**El modelo prioriza previsibilidad presupuestaria y control de avance.**

---

## 9. Estimación Económica y Duración

| Concepto                    | Detalle                        |
|-----------------------------|--------------------------------|
| Duración estimada           | 8 semanas                      |
| Dedicación promedio         | 20–25 horas semanales          |
| Total estimado              | 180–200 horas                  |
| Tarifa hora                 | $40.000 ARS (~USD 27)          |

**Incluye:**
- Desarrollo y ajustes
- Extracción y normalización de documentación
- Costos de herramientas LLM
- Soporte técnico durante implementación

| Concepto                         | Horas      | Costo estimado              |
|----------------------------------|------------|-----------------------------|
| Fase 0 (absorbida)               | —          | $0                          |
| Implementación (8 semanas)       | 180–200 hs | $7.200.000 – $8.000.000     |
| Mantenimiento mensual estimado   | ~8 hs      | ~$320.000                   |

### Inversión total estimada del proyecto:

**Entre $7.200.000 y un máximo de $8.000.000** para la implementación completa de 8 semanas.

**No se superará el techo de 200 horas sin aprobación expresa.**

---

## 10. Infraestructura y Costos Operativos

### 10.1 Infraestructura Técnica

El sistema requiere:
- Servidor (cloud o interno)
- Base de datos SQLite (incluida en la solución base)
- Acceso a internet para conexión con Telegram
- Sistema de backup periódico

No requiere hardware adicional para usuarios finales.
La arquitectura es liviana y no exige infraestructura de alta disponibilidad.

### 10.2 Modalidades de Hosting

El sistema puede operar bajo dos esquemas:

#### Opción A – Infraestructura del cliente

Implementación sobre servidor existente del Grupo Pediátrico.

**Costo:** sin cargo adicional por parte del proveedor (infraestructura provista por la institución).

#### Opción B – Hosting administrado (operación productiva)

Servidor cloud (VPS) con backup automático:
- Servidor: USD 30–70 mensuales
- Backup y almacenamiento: USD 10–20 mensuales

**Costo operativo total estimado:** Entre USD 40 y USD 90 mensuales.

Infraestructura liviana, sin dependencia de servicios externos complejos.
El hosting puede contratarse a nombre de la institución.

### 10.3 Costos Variables

**Durante implementación:**
- Uso de LLM para extracción estructurada → incluido dentro de horas estimadas.

**En operación productiva:**
- No utiliza LLM.
- No genera costos variables por consulta.
- No requiere licencias externas.

---

## 11. Condiciones Operativas

Para mantener la estimación dentro de la base prevista:
- Entrega estructurada de documentación por obra social
- Validación dentro de 48 horas hábiles
- Designación de referentes técnicos
- Disponibilidad de entorno servidor

Demoras en validación o entrega documental impactan en el cronograma, no en la tarifa horaria.

El mantenimiento contempla un promedio de 8 horas mensuales e incluye monitoreo, ajustes menores y soporte operativo.

---

## 12. Impacto Operativo

El Sistema Bot Operativo reduce el tiempo administrativo por consulta de admisión.

**Estimación conservadora:**
- Tiempo actual promedio por consulta: 4–6 minutos
- Tiempo con sistema: 1–2 minutos
- Ahorro estimado: 3 minutos por paciente

### Impacto según volumen mensual

| Pacientes/mes | Ahorro en horas |
|---------------|-----------------|
| 400           | 20 hs           |
| 800           | 40 hs           |
| 1200          | 60 hs           |

*(Cálculo: 3 minutos × volumen mensual)*

### Qué significa esto en la práctica
- Menos tiempo buscando información en múltiples fuentes
- Menos consultas internas entre administrativos
- Menos errores por datos desactualizados
- Menos dependencia de una persona específica que "sabe cómo es cada obra social"

El impacto depende directamente del volumen de admisiones.

La medición real del ahorro podrá validarse durante la Fase 2 (Despliegue Inicial Controlado), utilizando métricas efectivas de uso.

El sistema permite transformar tiempo administrativo en capacidad operativa disponible.

**La medición sistemática del uso y desempeño es lo que convierte al sistema en una herramienta de gestión, y no solo en un bot de consultas.**

---

## 13. Alcance

### Incluye:
- Bot operativo
- Sistema de métricas
- Reporte CSV
- Comandos supervisor
- Gestión de restricciones
- Mantenimiento correctivo

### No incluye:
- Integraciones externas
- WhatsApp
- Dashboard web
- Sistemas de autorización
- Integraciones con historia clínica

Estos desarrollos pueden cotizarse por separado.

---

## 14. Próximos Pasos

1. Aprobación de propuesta
2. Demo en vivo
3. Definición de cantidad inicial de OS
4. Inicio Fase 1

---

## 15. Consideraciones Comerciales

- Existe una demo funcional ya desarrollada.
- El desarrollo base fue absorbido.
- El proyecto presenta bajo riesgo técnico.
- El valor estimado del proyecto se encuentra dentro de rangos habituales para desarrollos internos de automatización operativa en instituciones de salud.
- El modelo T&M está estructurado con control previo de desvíos.

---

## 16. Cierre

El Sistema Bot Operativo de Admisión permite:
- Ordenar información dispersa
- Reducir errores
- Disminuir interrupciones
- Medir desempeño operativo
- Escalar sin rediseño

El proyecto presenta bajo riesgo técnico, alcance definido, modelo económico controlado y capacidad de medición operativa desde el primer día.

Su implementación permite ordenar el proceso de admisión sin modificar la operatoria actual ni generar dependencias tecnológicas externas.

---

# ANEXO TÉCNICO

## Sistema Bot Operativo de Admisión

---

## 1. Funcionalidades del Sistema

### 1.1 Consultas Operativas (Usuarios Generales)

El sistema permite consultas estructuradas por tipo de ingreso y obra social.

| Comando            | Función                                  |
|--------------------|------------------------------------------|
| `ambulatorio [OS]` | Información de turnos / ingreso ambulatorio |
| `internacion [OS]` | Requisitos y datos de internación        |
| `guardia [OS]`     | Información de ingreso por guardia       |
| `traslados [OS]`   | Gestión de traslados                     |
| `coseguros [OS]`   | Valores de coseguro por plan             |

#### Información disponible según tipo

**Ambulatorio**
- Documentación requerida
- Portal o validador
- Teléfono
- Coseguro
- Notas especiales

**Internación**
- Documentación
- Mail de denuncia
- Plazo de denuncia
- Portal
- Observaciones

**Guardia**
- Documentación
- Exenciones de coseguro
- Notas especiales

**Traslados**
- Teléfono de gestión
- Documentación requerida

---

### 1.2 Gestión de Restricciones (Supervisión)

Permite aplicar restricciones temporales por razones administrativas.
Requiere PIN de supervisor.

| Comando                          | Función              |
|----------------------------------|----------------------|
| `/restriccion:PIN:OS:"mensaje"`  | Agrega restricción   |
| `/quitar_restriccion:PIN:OS`     | Quita restricción    |
| `/restricciones:PIN`             | Lista activas        |
| `/reporte:PIN`                   | Genera reporte semanal |

**Ejemplo:**
Si una obra social presenta deuda, el bot mostrará alerta destacada antes de la información normal, indicando limitaciones de ingreso.

Esto permite controlar operativamente situaciones administrativas sin depender de comunicación informal.

---

### 1.3 Reporte de Problemas

Cualquier usuario puede reportar errores o datos faltantes:

```
/reportar "descripción"
```

El sistema:
- Registra el reporte
- Envía notificación automática por mail
- Permite corrección rápida en base de datos

---

## 2. Sistema de Mejora Continua

El sistema integra tres capas:

### 2.1 Registro Automático (Logs)

Cada consulta guarda:
- Fecha
- Usuario
- Texto ingresado
- Obra social detectada
- Tipo de ingreso detectado
- Resultado (éxito/falla)

Esto permite analizar uso real.

### 2.2 Métricas Operativas

Se calculan automáticamente:
- Tasa de éxito de consultas
- Usuarios activos
- Consultas por semana
- Consultas fallidas más frecuentes
- Reportes pendientes

### 2.3 Reporte Semanal Automatizado

El supervisor puede solicitar reporte y obtiene:
- Resumen estadístico
- Tasa de éxito
- Nivel de adopción
- Top consultas fallidas
- Archivo CSV descargable

Esto permite identificar:
- Nuevos sinónimos a incorporar
- Obras sociales no cargadas
- Errores frecuentes
- Necesidades de capacitación

---

## 3. Arquitectura Técnica

El sistema opera bajo una arquitectura liviana y controlada:

```
Telegram
    ↓
Bot Python
    ↓
Motor de Normalización
    ↓
Motor de Consulta
    ↓
Base de Datos SQLite
```

**Base de datos incluye:**
- Obras sociales
- Requisitos por tipo
- Coseguros
- Sinónimos
- Restricciones
- Logs de consultas
- Reportes

No requiere servicios externos ni licencias.

---

## 4. Datos Requeridos para Carga Inicial

Para cada obra social:

### Datos generales
- Código
- Nombre completo
- Tipo (sindical / prepaga / estatal)

### Por tipo de ingreso
- Documentación
- Portal o validador
- Mail de denuncia (si aplica)
- Plazos
- Teléfonos
- Coseguros
- Notas especiales

---

*Documento generado: Febrero 2026*
*Versión: Final*
