# Notas de Implementación - Escenario 2

## Pipeline de Extracción de Datos (futuro)

### Decisión: Manual + OCR (sin API extra)

Cuando lleguen los documentos de obras sociales:

```
PDFs/Scans → Google Vision OCR (gratis) → Texto limpio → Claude Code extrae → JSON → Validar → SQLite
```

### Google Vision OCR

- **Free tier:** 1,000 páginas/mes
- **Setup:** Crear proyecto en Google Cloud, habilitar Vision API
- **Docs:** https://cloud.google.com/vision/docs/ocr

### Proceso paso a paso

1. **Recibir documentos** - Patricia envía PDFs
2. **OCR batch** - Script con Google Vision → carpeta con .txt
3. **Extracción** - Pegar textos a Claude Code → genera JSONs
4. **Validación** - Supervisor revisa JSONs
5. **Carga** - Script Python: JSON → SQLite

### Estructura de carpetas (cuando se implemente)

```
escenario_2/pipeline/
├── 1_docs_nuevos/        # PDFs originales
├── 2_ocr_texto/          # Salida de Google Vision
├── 3_json_pendientes/    # Claude generó, sin validar
├── 4_json_validados/     # Supervisor aprobó
└── 5_archivo/            # Ya cargados a SQLite
```

### Estimación de tiempo (200 OS)

| Enfoque | Horas | Costo extra |
|---------|-------|-------------|
| Manual con Claude Code + OCR | ~50-60 hs | $0 |
| Automatizado con API | ~25-30 hs | ~$15 USD |

### Decisión

Evaluar según cómo lleguen los documentos:
- **Goteo (de a poco):** Manual con Claude Code
- **Batch grande (50+):** Considerar API si el volumen lo justifica

---

## Funcionalidades pendientes

Según propuesta final, falta implementar:

| Feature | Prioridad | Complejidad |
|---------|-----------|-------------|
| `/reportar` comando | Alta | Baja |
| Tabla `consultas_log` | Alta | Baja |
| Logger de consultas | Alta | Baja |
| `/reporte:PIN` semanal | Media | Media |
| Generación CSV | Media | Baja |
| Métricas automáticas | Media | Media |
| Notificación mail | Baja | Media |
| PIN en lugar de IDs | Baja | Baja |

---

## Flujo de Trabajo Recomendado

### Fase de desarrollo y carga de datos (PC local con Claude Code)

```
1. Recibir documentos de OS (PDFs, mails, manuales)
2. OCR con Google Vision → textos limpios
3. Pegar texto a Claude Code → genera JSON estructurado
4. Validar datos con supervisor
5. Cargar JSONs validados a SQLite local
6. Testear bot en local
7. Cuando está listo → subir .db al servidor
```

### Fase de producción (servidor GP)

```
1. git pull (actualiza código si hay cambios)
   - o scp obras_sociales.db al servidor (solo datos)
2. systemctl restart bot_admision
3. Verificar que responde en Telegram
```

### Actualización en producción

#### Cambios de código (vía GitHub)

```bash
# Desde tu PC
git add . && git commit -m "fix: descripción" && git push

# En el servidor (un solo comando)
ssh usuario@servidor "cd /opt/bot_admision && git pull && sudo systemctl restart bot_admision"
```

#### Solo datos (sin GitHub)

```bash
# Subir .db directamente
scp escenario_2/data/obras_sociales.db usuario@servidor:/opt/bot_admision/escenario_2/data/

# Reiniciar
ssh usuario@servidor "sudo systemctl restart bot_admision"
```

#### ¿Incluir .db en Git?

| Opción | Pro | Contra |
|--------|-----|--------|
| **Sí (recomendado)** | Un solo `git pull` actualiza todo | Repo más pesado (~1-5 MB) |
| **No** | Repo liviano | Dos pasos (pull + scp) |

**Decisión:** Incluir .db en Git. Para ~200 OS el archivo es pequeño y simplifica el deploy.

### Token de Telegram

| Situación | Acción |
|-----------|--------|
| Bot de prueba/dev actual | Podés usar el mismo token |
| Querés separar dev/prod | Crear nuevo bot con @BotFather |
| Bot ya en uso en otro proyecto | Crear nuevo bot |

**Crear bot nuevo (2 min):**
1. Telegram → @BotFather → `/newbot`
2. Nombre: `Bot Admision GP`
3. Username: `admision_gp_bot` (debe ser único)
4. Copiar token al `.env`

---

## Deploy del Proyecto

### Dependencias

```
python-telegram-bot>=20.0
python-dotenv>=1.0.0
```

SQLite viene incluido con Python.

### Opción A: Deploy directo (recomendado para este proyecto)

**1. En el servidor:**

```bash
# Clonar repo
git clone https://github.com/Hernan-Hamra/agente_hospital.git /opt/bot_admision
cd /opt/bot_admision

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install python-telegram-bot python-dotenv

# Configurar variables
cp .env.example .env
nano .env  # Agregar TELEGRAM_BOT_TOKEN y TELEGRAM_SUPERVISOR_IDS

# Inicializar base de datos
python escenario_2/data/init_db.py

# Test manual
python escenario_2/bot.py
```

**2. Crear servicio systemd:**

```bash
sudo nano /etc/systemd/system/bot_admision.service
```

```ini
[Unit]
Description=Bot Admision Grupo Pediatrico
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/bot_admision
Environment=PATH=/opt/bot_admision/venv/bin
ExecStart=/opt/bot_admision/venv/bin/python escenario_2/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Activar servicio:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot_admision
sudo systemctl start bot_admision
sudo systemctl status bot_admision
```

**4. Ver logs:**

```bash
sudo journalctl -u bot_admision -f
```

### Opción B: Deploy con Docker (alternativa)

**Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY escenario_2/ ./escenario_2/

# Base de datos persistente
VOLUME /app/escenario_2/data

CMD ["python", "escenario_2/bot.py"]
```

**docker-compose.yml:**

```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    volumes:
      - ./escenario_2/data:/app/escenario_2/data
    restart: unless-stopped
```

**Comandos:**

```bash
docker-compose up -d          # Iniciar
docker-compose logs -f        # Ver logs
docker-compose down           # Detener
docker-compose up -d --build  # Rebuild
```

### Comparación

| Aspecto | Sin Docker | Con Docker |
|---------|------------|------------|
| Setup inicial | 5 min | 15 min |
| Portabilidad | Media | Alta |
| Debug | Fácil | Medio |
| Backup | Copiar /opt/bot | Copiar volume |
| Recomendado | Servidor fijo | VPS/Cloud |

### Backup

**Base de datos:**

```bash
# Backup manual
cp /opt/bot_admision/escenario_2/data/obras_sociales.db /backup/obras_sociales_$(date +%Y%m%d).db

# Cron diario (agregar a crontab)
0 3 * * * cp /opt/bot_admision/escenario_2/data/obras_sociales.db /backup/obras_sociales_$(date +\%Y\%m\%d).db
```

### Variables de entorno (.env)

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_SUPERVISOR_IDS=123456789,987654321
```

### Checklist de deploy

- [ ] Servidor con Python 3.10+
- [ ] Clonar repositorio
- [ ] Crear venv e instalar deps
- [ ] Configurar .env con token
- [ ] Inicializar base de datos
- [ ] Crear servicio systemd
- [ ] Verificar bot responde
- [ ] Configurar backup automático
- [ ] Documentar IPs y accesos

---

*Última actualización: 2026-02-07*
