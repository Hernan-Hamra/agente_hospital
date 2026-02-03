# Formato de Preguntas para Entrenar Empleados de Admisión

## Cómo usar el bot

El bot entiende preguntas simples con **dos elementos clave**:
1. **Obra social**: ENSALUD, ASI, IOSFA
2. **Tipo de consulta**: ambulatorio, internación, guardia, traslados, coseguros

### Formato recomendado
```
[tipo de consulta] [obra social]
```

**Ejemplos:**
- `ambulatorio ensalud`
- `internación asi`
- `guardia iosfa`
- `coseguros ensalud`

---

## Preguntas por Tipo de Ingreso

### 📋 INGRESO AMBULATORIO / TURNOS

| Pregunta | Qué obtiene |
|----------|-------------|
| `ambulatorio ensalud` | Checklist completo ambulatorio |
| `turnos asi` | Checklist completo ambulatorio |
| `consulta iosfa` | Checklist completo ambulatorio |
| `coseguros ensalud` | Valores de coseguro por plan |

**Información que devuelve:**
- Documentación requerida (DNI, credencial)
- Link del portal validador
- Teléfono de contacto
- Si aplica coseguro o no
- Notas sobre autorizaciones

---

### 🏥 INTERNACIÓN

| Pregunta | Qué obtiene |
|----------|-------------|
| `internación ensalud` | Checklist completo internación |
| `internación asi` | Checklist completo internación |
| `cirugía iosfa` | Checklist completo internación |

**Información que devuelve:**
- Documentación requerida
- Mail para denuncia de internación
- Plazo de denuncia (24hs, etc.)
- Portal/validador
- Notas sobre censo diario

---

### 🚨 GUARDIA

| Pregunta | Qué obtiene |
|----------|-------------|
| `guardia ensalud` | Checklist completo guardia |
| `urgencia asi` | Checklist completo guardia |
| `emergencia iosfa` | Checklist completo guardia |

**Información que devuelve:**
- Documentación requerida
- Si paga coseguro (generalmente EXENTO)
- Portal/validador
- Notas sobre autorización (no requiere)

---

### 🚑 TRASLADOS

| Pregunta | Qué obtiene |
|----------|-------------|
| `traslados ensalud` | Checklist completo traslados |
| `derivación asi` | Checklist completo traslados |
| `ambulancia iosfa` | Checklist completo traslados |

**Información que devuelve:**
- Documentación requerida
- Teléfono/mail para gestión
- Requisitos específicos

---

### 💰 COSEGUROS

| Pregunta | Qué obtiene |
|----------|-------------|
| `coseguros ensalud` | Valores por plan y prestación |
| `copago asi` | Valores por plan y prestación |
| `precios iosfa` | Valores por plan y prestación |

**Información que devuelve:**
- Planes disponibles
- Valor por tipo de prestación
- Condiciones de exención

---

## Sinónimos Aceptados

El bot entiende estas variaciones:

### Tipo de Ingreso
| Escribe | El bot entiende |
|---------|-----------------|
| ambulatorio, turno, turnos, consulta | Ambulatorio |
| internación, internar, internado, cirugía, cama | Internación |
| guardia, urgencia, emergencia | Guardia |
| traslado, traslados, derivación, ambulancia | Traslados |

### Obras Sociales
| Escribe | El bot entiende |
|---------|-----------------|
| ensalud, en salud | ENSALUD |
| asi, asi salud | ASI |
| iosfa, fuerzas armadas | IOSFA |

---

## Ejercicios de Práctica

### Nivel 1: Consultas básicas
1. Necesitás saber qué documentación pedir para un turno de ENSALUD
   → Escribí: `ambulatorio ensalud`

2. Llega un paciente de ASI por guardia
   → Escribí: `guardia asi`

3. Tenés que internar un paciente de IOSFA
   → Escribí: `internación iosfa`

### Nivel 2: Coseguros
1. Un paciente de ENSALUD pregunta cuánto paga de coseguro
   → Escribí: `coseguros ensalud`

2. Querés saber si guardia paga coseguro en ASI
   → Escribí: `guardia asi` (en la respuesta dice si es exento)

### Nivel 3: Casos especiales
1. Necesitás el mail para denunciar una internación de ENSALUD
   → Escribí: `internación ensalud` (incluye el mail de denuncia)

2. Necesitás el teléfono para coordinar un traslado de ASI
   → Escribí: `traslados asi`

---

## Qué hacer si el bot no entiende

Si el bot responde "Para ayudarte necesito que me indiques...", significa que faltó información:

| Mensaje del bot | Qué falta |
|-----------------|-----------|
| "...obra social (ENSALUD, ASI, IOSFA)" | Agregar nombre de obra social |
| "...tipo de ingreso (ambulatorio, internación...)" | Agregar tipo de consulta |

**Solución:** Reescribir la pregunta con los dos elementos.

---

## Casos que el bot NO resuelve (por ahora)

- Restricciones temporales por falta de pago
- Convenios especiales
- Excepciones de cobertura
- Autorizaciones complejas

Para estos casos, contactar directamente a la obra social o al supervisor.
