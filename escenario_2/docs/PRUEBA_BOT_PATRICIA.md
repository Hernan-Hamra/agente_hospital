# Prueba del Bot de Admisión con Patricia

**Fecha:** 2026-02-07
**Bot:** @GrupoPediatricoBot
**PIN de prueba:** 1234

---

## Parte 1: Consultas (usuario normal)

### Paso 1: Iniciar el bot

```
/start
```

**Esperado:** Bienvenida con lista de obras sociales (ENSALUD, ASI, IOSFA)

---

### Paso 2: Consulta ambulatorio

```
ambulatorio ensalud
```

**Esperado:** Info de ingreso ambulatorio (documentación, teléfono, portal)

---

### Paso 3: Consulta internación

```
internacion asi
```

**Esperado:** Info de internación (mail denuncia, plazo 24hs)

---

### Paso 4: Consulta guardia

```
guardia iosfa
```

**Esperado:** Info de guardia (documentación, coseguro)

---

## Parte 2: Restricciones (supervisor)

### Formato del comando

```
/restriccion:PIN OBRA_SOCIAL TIPO "MENSAJE" [PERMITIDOS]
```

Donde:

| Parámetro      | Valores posibles                                      | Obligatorio |
|----------------|-------------------------------------------------------|-------------|
| PIN            | 1234 (el PIN configurado)                             | Sí          |
| OBRA_SOCIAL    | ENSALUD, ASI, IOSFA                                   | Sí          |
| TIPO           | falta_pago, convenio_suspendido, cupo_agotado         | Sí          |
| "MENSAJE"      | Texto libre entre comillas                            | Sí          |
| PERMITIDOS     | ambulatorio, internacion, guardia, traslados (o nada) | No          |

**IMPORTANTE:** Si no se pone PERMITIDOS, se bloquean TODOS los tipos de ingreso.

---

### Paso 5: Agregar restricción (solo permite guardia)

```
/restriccion:1234 ENSALUD falta_pago "Deuda pendiente. Solo guardia autorizado." guardia
```

**Esperado:**
- Tu mensaje DESAPARECE (se borra automáticamente para ocultar el PIN)
- Aparece: "👤 Acción de supervisor" + "Solo permite: guardia"

---

### Paso 6: Verificar que internación está bloqueada

```
internacion ensalud
```

**Esperado:** ⛔ ATENCIÓN al inicio + info de internación

---

### Paso 7: Verificar que guardia está permitida

```
guardia ensalud
```

**Esperado:** Info normal SIN alerta (guardia está permitida)

---

### Paso 8: Ver restricciones activas

```
/restricciones:1234
```

**Esperado:** Lista mostrando la restricción de ENSALUD

---

### Paso 9: Quitar restricción de ENSALUD

```
/quitar_restriccion:1234 ENSALUD
```

**Esperado:** "Se quitaron 1 restricción(es) de ENSALUD"

---

### Paso 10: Verificar que se quitó

```
internacion ensalud
```

**Esperado:** Info normal SIN alerta ⛔

---

### Paso 11: Restricción que bloquea TODO

```
/restriccion:1234 ASI convenio_suspendido "Convenio suspendido hasta nuevo aviso"
```

**Esperado:** "Bloquea: TODOS los ingresos" (porque no se puso tipo permitido)

---

### Paso 12: Verificar bloqueo total

```
internacion asi
```
```
guardia asi
```

**Esperado:** Ambos muestran ⛔ ATENCIÓN

---

### Paso 13: Quitar y limpiar

```
/quitar_restriccion:1234 ASI
```

**Esperado:** Se quitó la restricción de ASI

---

### Paso 14: Probar PIN incorrecto

```
/restriccion:9999 ENSALUD falta_pago "test"
```

**Esperado:**
- Mensaje se borra
- Aparece: "👤 Acción de supervisor" + "⛔ PIN incorrecto"

---

## Resumen de resultados

| Paso | Descripción                    | OK? |
|------|--------------------------------|-----|
| 1    | /start                         | [ ] |
| 2    | ambulatorio ensalud            | [ ] |
| 3    | internacion asi                | [ ] |
| 4    | guardia iosfa                  | [ ] |
| 5    | Agregar restricción (guardia)  | [ ] |
| 6    | internacion bloqueada ⛔       | [ ] |
| 7    | guardia permitida              | [ ] |
| 8    | /restricciones                 | [ ] |
| 9    | Quitar restricción ENSALUD     | [ ] |
| 10   | Sin alerta                     | [ ] |
| 11   | Restricción bloquea TODO       | [ ] |
| 12   | Ambos bloqueados ⛔            | [ ] |
| 13   | Quitar restricción ASI         | [ ] |
| 14   | PIN incorrecto                 | [ ] |

---

## Notas de la prueba

(Espacio para anotar problemas o comentarios)

```




```

---

*Documento generado: 2026-02-07*
