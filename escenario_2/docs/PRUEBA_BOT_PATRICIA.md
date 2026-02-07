# Prueba del Bot de Admisión con Patricia

**Fecha:** 2026-02-07
**Bot:** @AgentHospitalarioBot (o el nombre que tenga)
**PIN de prueba:** 1234

---

## Paso 1: Iniciar el bot

Enviar en Telegram:
```
/start
```

**Esperado:** Mensaje de bienvenida con lista de obras sociales (ENSALUD, ASI, IOSFA)

---

## Paso 2: Ver tu ID

```
/mi_id
```

**Esperado:** Muestra tu ID de Telegram, username y nombre

---

## Paso 3: Consulta básica

```
ambulatorio ensalud
```

**Esperado:** Info de ingreso ambulatorio (documentación, teléfono, portal)

---

## Paso 4: Otra consulta

```
internacion ensalud
```

**Esperado:** Info de internación (mail denuncia, plazo 24hs, etc.)

---

## Paso 5: Agregar restricción (SUPERVISOR)

```
/restriccion:1234 ENSALUD falta_pago "Deuda pendiente. Solo GUARDIA autorizado." guardia
```

**Esperado:**
- Tu mensaje DESAPARECE (se borra automáticamente)
- Aparece: "👤 Acción de supervisor" + confirmación

---

## Paso 6: Verificar restricción aplicada

```
internacion ensalud
```

**Esperado:** Muestra ⛔ ATENCIÓN al inicio del mensaje

---

## Paso 7: Consulta permitida

```
guardia ensalud
```

**Esperado:** Info normal (guardia está permitido)

---

## Paso 8: Ver restricciones activas

```
/restricciones:1234
```

**Esperado:** Lista con la restricción de ENSALUD

---

## Paso 9: Quitar restricción

```
/quitar_restriccion:1234 ENSALUD
```

**Esperado:** Confirmación de que se quitó

---

## Paso 10: Verificar que se quitó

```
internacion ensalud
```

**Esperado:** Info normal SIN alerta ⛔

---

## Paso 11: Probar PIN incorrecto

```
/restriccion:9999 ENSALUD falta_pago "test"
```

**Esperado:**
- Mensaje se borra
- Aparece: "⛔ PIN incorrecto"

---

## Resumen de resultados

| Paso | Descripción                | OK? |
|------|----------------------------|-----|
| 1    | /start                     | [ ] |
| 2    | /mi_id                     | [ ] |
| 3    | ambulatorio ensalud        | [ ] |
| 4    | internacion ensalud        | [ ] |
| 5    | Agregar restricción        | [ ] |
| 6    | Ver alerta ⛔              | [ ] |
| 7    | guardia (permitido)        | [ ] |
| 8    | /restricciones             | [ ] |
| 9    | Quitar restricción         | [ ] |
| 10   | Sin alerta                 | [ ] |
| 11   | PIN incorrecto             | [ ] |

---

## Notas de la prueba

(Espacio para anotar problemas o comentarios)

```




```

---

*Documento generado: 2026-02-07*
