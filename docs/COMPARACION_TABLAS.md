# Comparación de Tablas: Documentos Originales vs Chunks Indexados

**Fecha**: 2026-01-21
**Propósito**: Validación manual de extracción de tablas para el RAG

---

## Resumen Ejecutivo

| Obra Social | Archivo Original | Tablas Detectadas | Chunks de Contactos | Chunks de Texto |
|-------------|------------------|-------------------|---------------------|-----------------|
| ASI | 2024-01-04_normas.docx | 2 tablas | 1 | 11 |
| ENSALUD | 2024-01-04_normativa.pdf | 59 tablas | 1 | 9 |
| IOSFA | 2024-01-04_checklist.docx | 0 tablas | 0 | 1 |
| GRUPO_PEDIATRICO | checklist_general_grupo_pediatrico.docx | 0 tablas | 0 | 1 |

---

## 1. ASI (Acción Social de Empresarios)

### Archivo Original
- **Ubicación**: `data/obras_sociales/asi/2024-01-04_normas.docx`

### Tablas Detectadas (2)

#### TABLA T001 - Contactos Mesa Operativa
**Tipo**: Tabla de contactos por departamento

**Contenido indexado**:
```
El mail de Mesa Operativa de ASI es Derivaciones y Presupuestos: autorizaciones@asi.com.ar
Internaciones: internados.asi@asi.com.ar.
El teléfono de Mesa Operativa de ASI es 0810-888-8274 op.4 + op. 1.
El mail de Contratos y normas Operativas de ASI es convenios@asi.com.ar.
El teléfono de Contratos y normas Operativas de ASI es 4716-8723.
El mail de Portal de prestadores de ASI es mesadeayuda@asi.com.ar.
El teléfono de Portal de prestadores de ASI es 4716-8723.
El mail de Liquidaciones de ASI es liquidaciones@asi.com.ar.
El teléfono de Liquidaciones de ASI es 0810-888-8274 int. 347/381.
El mail de Pago a Prestadores de ASI es cristian.sanchez@asi.com.ar.
El teléfono de Pago a Prestadores de ASI es 4716-3200 Int: 346.
```

**VERIFICAR EN ORIGINAL**:
- [ ] Mesa Operativa - Derivaciones y Presupuestos: autorizaciones@asi.com.ar
- [ ] Mesa Operativa - Internaciones: internados.asi@asi.com.ar
- [ ] Mesa Operativa teléfono: 0810-888-8274 op.4 + op. 1
- [ ] Contratos y normas: convenios@asi.com.ar / 4716-8723
- [ ] Portal de prestadores: mesadeayuda@asi.com.ar / 4716-8723
- [ ] Liquidaciones: liquidaciones@asi.com.ar / 0810-888-8274 int. 347/381
- [ ] Pago a Prestadores: cristian.sanchez@asi.com.ar / 4716-3200 Int: 346

---

#### TABLA T002 - Grilla de Coseguros (38 filas x 7 columnas)
**Tipo**: Tabla de precios por plan

**Contenido indexado** (extracto):
```
Consultas | Blanco/Asi 100 | Asi 200 | Asi 250 | Asi 300 | Asi 350 | Asi 350P/400/450/Exclusive
Médicos de Familia/Generalistas/Pediatras/Tocoginecólogo/Médicos Especialistas | $12,000 | $6,000 | $5,000 | $4,000 | $3,000 | S/C
Guardia/Demanda Espontanea | $12,000 | S/C | S/C | S/C | S/C | S/C
Guardia Urgencia/Codigo Rojo | S/C | S/C | S/C | S/C | S/C | S/C
Programa HIV | Exento | Exento | Exento | Exento | Exento | Exento
...
```

**VERIFICAR EN ORIGINAL** (página donde está la "Grilla de Coseguros"):
- [ ] Consultas médico generalista: $12,000 (Blanco/Asi 100)
- [ ] Guardia urgencia código rojo: S/C en todos los planes
- [ ] Programa HIV: Exento en todos
- [ ] Oncología: Exento en todos
- [ ] Discapacidad: Exento en todos
- [ ] PMI: Exento en todos
- [ ] Psicología sesión incluida: $9,000 | $8,000 | $6,000 | $5,000 | $4,000 | S/C
- [ ] Laboratorio básico (hasta 6 det.): $4,200 | $2,160 | $1,680 | $1,560 | $1,320 | S/C
- [ ] TAC/RMN/alta complejidad: $24,000 | $12,000 | $10,000 | $8,000 | $6,000 | S/C
- [ ] VEDA: $60,000
- [ ] VCC: $40,000
- [ ] Odontología consultas: $10,000 | $4,800 | $3,600 | $3,000 | $2,200 | S/C

### Chunk de Contactos Extraídos (CONTACTOS)
**Contactos auto-detectados del texto**:
- autorizacionessm@asi.com.ar
- autorizaciones@asi.com.ar
- internados.asi@asi.com.ar
- cuidadosdomiciliarios@asi.com.ar
- recepcionfacturacion@asi.com.ar
- 4716-3210
- 5702-9599

---

## 2. ENSALUD

### Archivo Original
- **Ubicación**: `data/obras_sociales/ensalud/2024-01-04_normativa.pdf`

### Tablas Detectadas (59)

**NOTA IMPORTANTE**: ENSALUD tiene un PDF muy estructurado con muchas tablas pequeñas. El parser detectó 59 tablas, pero muchas son fragmentos de tablas más grandes divididas por columnas.

#### Tablas Principales por Página:

**PÁGINA 2** - Identificación y Coseguros
| Tabla | Contenido | Chunk ID |
|-------|-----------|----------|
| T001 | Header (vacío) | 1x4 cols |
| T002 | Identificación: Carnet+DNI para 5 planes | T002 |
| T003 | Coseguros consultas/rehabilitación | T003 |
| T004 | APB: SI/SI/NO/NO/NO | T004 |

**VERIFICAR EN ORIGINAL (pág 2)**:
- [ ] Coseguros consultas: SI | NO | NO | NO | NO (por plan)
- [ ] Coseguros rehabilitación/psicología: SI | SI | SI | NO | NO
- [ ] APB: SI | SI | NO | NO | NO

---

**PÁGINA 3** - Prestaciones Ambulatorias
| Tabla | Contenido | Chunk ID |
|-------|-----------|----------|
| T005 | Lista de prestaciones ambulatorias | T005 |
| T006-T010 | Cobertura/Autorización por plan | T006-T010 |

**VERIFICAR EN ORIGINAL (pág 3)**:
- [ ] Consultas especialidades básicas (clínica, gineco, pediatría): Cobertura varía por plan
- [ ] Consultas especialidades quirúrgicas: SI con autorización PREVIA
- [ ] Consultas con obstetricia: SI con autorización PREVIA
- [ ] Fisiokinesioterapia: requiere autorización PREVIA
- [ ] Fonoaudiología: requiere autorización PREVIA

---

**PÁGINA 4** - Guardia e Internaciones
| Tabla | Contenido | Chunk ID |
|-------|-----------|----------|
| T011 | Prácticas por guardia | T011 |
| T012-T016 | Cobertura guardia por plan | T012-T016 |
| T017 | Internaciones programadas | T017 |
| T018-T023 | Cobertura internaciones por plan | T018-T023 |

**VERIFICAR EN ORIGINAL (pág 4)**:
- [ ] Consultas de guardia: SI sin autorización (todos los planes)
- [ ] Internación de urgencia: SI con denuncia 24hs
- [ ] Internaciones programadas clínicas: SI con autorización PREVIA
- [ ] Intervenciones quirúrgicas programadas: SI con autorización PREVIA
- [ ] Internación obstétrica: denuncia 24hs
- [ ] Vigencia de autorizaciones: 30 días

---

**PÁGINA 5-8** - Planes Deportivos (repetición estructura)
Las tablas T024-T046 repiten la misma estructura para:
- ENSALUD Plan Corporativo Club Atlético Vélez Sarsfield
- ENSALUD Plan Corporativo Club Atlético Platense
- ENSALUD Plan Corporativo Club Atlético Rosario Central
- ENSALUD Plan Corporativo Club Atlético Independiente
- ENSALUD Plan Corporativo Club Atlético Los Andes
- ENSALUD Plan Corporativo Club Atlético San Lorenzo de Almagro

---

**PÁGINA 9** - Coseguros (valores monetarios)
| Tabla | Contenido | Chunk ID |
|-------|-----------|----------|
| T047 | Grilla de coseguros con montos | T047 |

**VERIFICAR EN ORIGINAL (pág 9)**:
- [ ] Médicos Familia/Generalistas/Pediatras/Tocoginecólogo: $1,553
- [ ] Médicos Especialistas: $2,912
- [ ] Laboratorio básico (hasta 6 det.): $971
- [ ] Valor extra por prestación adicional: $388
- [ ] Imágenes baja complejidad (RX, eco): $971
- [ ] Prácticas mediana complejidad: $1,941
- [ ] Prácticas alta complejidad (TAC, RMN, etc): $4,854
- [ ] Kinesiología por sesión: $971
- [ ] Kinesiología excedentes: $1,747
- [ ] Fonoaudiología por sesión: $971
- [ ] APB: $6,000

---

**PÁGINAS 10-11** - Listado de Prestaciones Fuera de PMO
| Tabla | Contenido | Chunk ID |
|-------|-----------|----------|
| T048-T050 | Códigos de Laboratorio | T048-T050 |
| T051 | Imágenes (códigos) | T051 |
| T052 | Anatomía Patológica | T052 |
| T053 | Neumonología | T053 |
| T054 | Dermatología | T054 |
| T055 | Neurofisiología | T055 |
| T056 | Endoscopias | T056 |
| T057 | Otorrinolaringología | T057 |
| T058 | Urología | T058 |
| T059 | Cardiología | T059 |

**VERIFICAR EN ORIGINAL (págs 10-11)** - Códigos de prestaciones:
- [ ] VIDEOCOLONOSCOPIA: código 209035
- [ ] VIDEOENDOSCOPIA ALTA: código 209036
- [ ] ERGOMETRIA 12 DERIVACIONES: código 179021
- [ ] HOLTER 3 CANALES: código 170198
- [ ] ESTUDIO URODINAMICO COMPLETO: código 369911
- [ ] FLUJOMETRIA: código 369013

### Chunk de Contactos Extraídos (CONTACTOS)
```
El mail de censo por mail a de ENSALUD es auditoria@ensalud.org.
El teléfono de contacto de ENSALUD es 11-66075765.
El mail de administración de ENSALUD es administracion@ensalud.org.
```

**VERIFICAR EN ORIGINAL (última página del PDF)**:
- [ ] auditoria@ensalud.org (para censo diario)
- [ ] 11-66075765 (teléfono de contacto)
- [ ] administracion@ensalud.org

---

## 3. IOSFA (Instituto de Obra Social de las Fuerzas Armadas)

### Archivo Original
- **Ubicación**: `data/obras_sociales/iosfa/2024-01-04_checklist.docx`

### Tablas Detectadas: 0
El documento es un checklist de texto plano, sin tablas formales.

### Chunk Único (001)
```
CHEKLIST DE ADMISION – IOSFA
DOCUMENTACION INGRESO CONSULTAS:
VALIDADOR
DNI
BONO DE CONSULTA
DOCUMENTACION INGRESO PRACTICAS:
VALIDADOR
DNI
BONO DE PRACTICAS
AUTORIZACION
DOCUMENTACION INGRESO GUARDIA:
DNI – VALIDADOR
DOCUMENTACION INGRESO INTERNACIONES PROGRAMADAS:
DNI – VALIDADOR
VER DRIVE DE ENLACE PARA CORROBORAR QUE SE ENCUENTRE AUTORIZADA LA PRESTACION
```

**VERIFICAR EN ORIGINAL**:
- [ ] Consultas: Validador + DNI + Bono
- [ ] Prácticas: Validador + DNI + Bono + Autorización
- [ ] Guardia: DNI + Validador
- [ ] Internaciones programadas: DNI + Validador + verificar Drive

### PENDIENTE - IOSFA No tiene contactos
**ACCIÓN REQUERIDA**: Agregar manualmente datos de contacto de IOSFA al documento original o crear documento separado con:
- Teléfono de atención
- Mail de autorizaciones
- Mail de internaciones

---

## 4. GRUPO PEDIÁTRICO

### Archivo Original
- **Ubicación**: `data/grupo_pediatrico/checklist_general_grupo_pediatrico.docx`

### Tablas Detectadas: 0
El documento es un checklist de texto plano, sin tablas formales.

### Chunk Único (001)
```
DOCUMENTACIÓN BÁSICA (OBLIGATORIA EN TODO INGRESO SI CORRESPONDE)
☐ DNI del paciente
☐ Credencial ASI vigente (física / virtual / provisoria)
☐ Número de socio y plan
☐ Validación de afiliación en Portal de Prestadores
☐ Diagnóstico presuntivo
☐ Firma del socio o responsable
☐ Aclaración y DNI del firmante

INGRESO AMBULATORIO / TURNOS
☐ Consultas: DNI, credencial, validación en portal, cobro de coseguro (SI CORRESPONDE)
...
```

**VERIFICAR EN ORIGINAL**:
- [ ] Documentación básica incluye: DNI, Credencial ASI, Nro socio/plan, etc.
- [ ] Ingreso ambulatorio: DNI + credencial + validación + coseguro
- [ ] Ingreso por guardia: DNI + credencial + validación
- [ ] Exentos de coseguro: Guardia, PMI, Oncológicos, HIV, Discapacidad

**NOTA**: El documento dice "Credencial ASI vigente" - esto es correcto ya que Grupo Pediátrico trabaja con ASI como obra social.

---

## Checklist de Validación Manual

### Prioridad Alta (datos sensibles)
- [ ] **ASI T002**: Verificar todos los montos de coseguros
- [ ] **ENSALUD T047**: Verificar todos los montos de coseguros
- [ ] **ENSALUD Contactos**: Verificar tel 11-66075765 y mails
- [ ] **ASI Contactos**: Verificar todos los teléfonos y mails

### Prioridad Media (cobertura)
- [ ] **ENSALUD T003**: Coseguros por tipo de prestación
- [ ] **ENSALUD T005-T010**: Cobertura ambulatoria por plan
- [ ] **ENSALUD T011-T016**: Cobertura guardia por plan

### Prioridad Baja (códigos)
- [ ] **ENSALUD T048-T059**: Códigos de prestaciones fuera de PMO

---

## Instrucciones para Validación

1. Abrir el documento original en Word/PDF viewer
2. Ubicar la tabla correspondiente (usar página indicada para ENSALUD)
3. Comparar campo por campo con el contenido indexado
4. Marcar con ✓ si coincide o anotar discrepancia

**Si encuentra errores**:
1. Anotar el chunk_id y el campo incorrecto
2. Indicar el valor correcto del original
3. Reportar para ajuste del JSON o script de conversión

---

## Archivos Relevantes

| Tipo | Ubicación |
|------|-----------|
| Originales | `data/obras_sociales/` |
| JSONs indexados | `data/obras_sociales_json/` |
| Índice FAISS | `backend/faiss_index/` |
| Script conversión | `backend/scripts/convert_docs_to_json_flat.py` |
