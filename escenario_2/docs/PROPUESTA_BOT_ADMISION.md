# Bot de Consultas para Admisión - Grupo Pediátrico

## Resumen Ejecutivo

Bot de Telegram que responde consultas del equipo de admisión sobre obras sociales.
**Sin inteligencia artificial**, usa búsqueda estructurada en base de datos.

---

## Cómo Funciona

### Consulta del empleado
El empleado escribe en Telegram:
```
internación ensalud
```

### Respuesta del bot (instantánea)
```
🏥 INTERNACIÓN - ENSALUD - Seguridad Social

📄 Documentación: DNI, Carnet de afiliación
📧 Mail denuncia: auditoria@ensalud.org
⏰ Plazo: Dentro de las 24 horas
🔗 Portal: https://ensalud.org/novedades/soy-prestador/
📞 Teléfono: 11-66075765

⚠️ Internación programada requiere autorización PREVIA.
   Censo diario obligatorio a auditoria@ensalud.org
```

---

## Ejemplos de Consultas

| Empleado escribe       | Bot responde                               |
|------------------------|--------------------------------------------|
| `ambulatorio ensalud`  | Documentación, portal, teléfono, coseguro  |
| `internación asi`      | Documentación, mail denuncia, plazo, portal|
| `guardia iosfa`        | Documentación, validador, coseguro (EXENTO)|
| `coseguros ensalud`    | Valores por plan y prestación              |
| `traslados asi`        | Documentación, teléfono gestión            |

### Cuando falta información
| Empleado escribe | Bot responde                                             |
|------------------|----------------------------------------------------------|
| `hola`           | "Necesito: obra social + tipo de ingreso"                |
| `ensalud`        | "Necesito: tipo de ingreso (ambulatorio, internación...)" |
| `internación`    | "Necesito: obra social (ENSALUD, ASI, IOSFA)"            |

---

## Funcionalidad de Restricciones Temporales

Cuando una obra social tiene restricciones (ej: falta de pago), el supervisor puede cargarla y el bot alerta automáticamente:

```
⛔ ATENCIÓN: ENSALUD tiene pagos pendientes. Solo se permite GUARDIA.

🏥 INTERNACIÓN - ENSALUD...
[resto de la info normal]
```

---

## Tiempos de Respuesta

| Métrica              | Valor        |
|----------------------|--------------|
| Tiempo de respuesta  | **< 100 ms** |
| Disponibilidad       | 24/7         |
| Usuarios simultáneos | Ilimitados   |

*Comparación: Un bot con IA tarda 1-3 segundos por respuesta*

---

## Costos

### Costo de operación mensual

| Concepto           | Costo               |
|--------------------|---------------------|
| Servidor (hosting) | **$0 - $5 USD/mes** |
| Base de datos      | Incluido (SQLite)   |
| API de IA          | **$0** (no usa IA)  |
| **TOTAL**          | **$0 - $5 USD/mes** |

### Opciones de hosting

| Opción              | Costo       | Características           |
|---------------------|-------------|---------------------------|
| **Servidor propio** | $0          | Cualquier PC con internet |
| **VPS básico**      | ~$5 USD/mes | DigitalOcean, Linode, etc.|
| **Heroku free**     | $0          | Con limitaciones horarias |
| **Railway**         | ~$5 USD/mes | Sin mantenimiento         |

---

## Requisitos Técnicos para Hostear

### Mínimos
- Python 3.10+
- 512 MB RAM
- 100 MB disco
- Conexión a internet

### Puede correr en:
- PC de escritorio (Windows/Linux/Mac)
- Raspberry Pi
- Servidor en la nube
- Cualquier VPS básico

### Instalación (una vez)
```bash
pip install python-telegram-bot python-dotenv
python escenario_2/data/init_db.py
python escenario_2/bot.py
```

---

## Qué se necesita para implementar

### 1. Token de Telegram (gratis)
- Crear bot con @BotFather en Telegram
- Obtener token

### 2. Cargar datos de obras sociales
- Completar información de cada obra social
- El equipo de admisión/enlace proporciona los datos

### 3. Servidor donde correr
- Puede ser una PC del hospital que esté siempre encendida
- O un servidor en la nube ($5/mes)

---

## Comparación con solución con IA

| Aspecto          | Bot SQL (este)       | Bot con IA            |
|------------------|----------------------|-----------------------|
| Costo mensual    | $0-5 USD             | $50-200 USD           |
| Tiempo respuesta | <100ms               | 1-3 segundos          |
| Precisión        | 100% (datos exactos) | ~90% (puede alucinar) |
| Mantenimiento    | Bajo                 | Medio                 |
| Flexibilidad     | Estructurado         | Lenguaje natural      |

---

## Limitaciones

1. **Solo responde lo que está cargado**: Si no está en la base de datos, dice "No tengo información"
2. **Requiere formato específico**: El empleado debe escribir "obra social + tipo de ingreso"
3. **No interpreta**: Si escribe mal, puede no entender

---

## Próximos pasos sugeridos

1. **Demo en vivo**: Probar el bot con casos reales
2. **Cargar datos**: Completar ASI e IOSFA
3. **Definir supervisores**: Quiénes pueden cargar restricciones
4. **Elegir hosting**: Servidor propio o en la nube
5. **Capacitación**: 30 min con el equipo de admisión

---

## Contacto técnico

Para consultas sobre implementación, contactar a Hernán.

---

*Documento generado: Febrero 2026*
*Versión: Escenario 2 - Bot SQL sin IA*
