Portada del Informe

Informe Ejecutivo – Agente Conversacional de IA

Evaluación de escenarios para implementación en el Grupo Pediátrico

 

Fecha:
15 de enero de 2026

Autor:
Hernán Hamra

Destinatarios:
Adolfo Korman – Director Ejecutivo
Patricia Rivas – Directora de TI


 
Contenido
Informe Ejecutivo	3
1. Objetivo del Informe	3
2. Modos de Funcionamiento del Agente Conversacional	3
🔹 Modo Consulta (NO agente)	3
🔹 Modo Agente (charla completa)	3
3. Regla Crítica de Precisión (aplica SOLO a Modo Consulta)	4
4. Escenarios Evaluados	4
ESCENARIO 1 – Modelo local en CPU (sin GPU)	4
ESCENARIO 2 – Modelo local en GPU (RTX 3060 12GB)	5
ESCENARIO 3 – Modelo cloud gratuito	5
ESCENARIO 4 – Modelo cloud pago (suscripción mensual)	6
RESUMEN COMPARATIVO DE ESCENARIOS (visión ejecutiva)	6
IMPACTO OPERATIVO Y ROI (con valores concretos)	6
Ahorro de tiempo humano	7
Ahorro mensual estimado	7
Comparación costo vs beneficio	7
BENEFICIOS ADICIONALES (no financieros)	7
CONCLUSIONES GENERALES	8
RECOMENDACIÓN FINAL	8
GLOSARIO	8
CIERRE EJECUTIVO Y PRÓXIMOS PASOS	9
Cierre Ejecutivo:	9
Próximos Pasos Recomendados:	9

 
Informe Ejecutivo
Evaluación de Implementación de un Agente Conversacional de IA
Grupo Pediátrico
Fecha: 2026-01-15
Destinatarios:
•	Adolfo Korman – Director Ejecutivo
•	Patricia Rivas – Directora de TI
Elaborado por: Hernán Hamra
________________________________________
1. Objetivo del Informe
El objetivo de este informe es evaluar técnica y económicamente distintas alternativas para implementar un agente conversacional de IA en el Grupo Pediátrico, capaz de:
•	Atender consultas puntuales basadas en documentación (RAG)
•	Conducir charlas completas de enrolamiento con pacientes
•	Reducir costos operativos
•	Mejorar tiempos de respuesta y calidad de atención
•	Escalar sin incrementar proporcionalmente la estructura humana
El análisis está orientado a apoyar decisiones ejecutivas (costos, beneficios, escalabilidad) y técnicas (arquitectura, modelos, viabilidad operativa).
________________________________________
2. Modos de Funcionamiento del Agente Conversacional
El agente opera exclusivamente en dos modos. No existen otros.
🔹 Modo Consulta (NO agente)
•	Una pregunta → una respuesta
•	No usa memoria conversacional
•	No requiere planificación ni recall
•	Utiliza RAG sobre documentación
•	Pregunta bien direccionada
Uso típico:
“¿Cuál es el mail de la obra social ENSALUD?”
Tokens promedio (recalculados):
•	Total por consulta con RAG: ~1.000 tokens
________________________________________
🔹 Modo Agente (charla completa)
•	Conversación guiada (≈ 8 turnos)
•	Usa memoria conversacional acumulativa
•	Razonamiento y conducción del diálogo
•	Puede usar RAG en parte de la charla
Uso típico:
Proceso completo de enrolamiento de un paciente.
Tokens promedio (recalculados):
•	Total por charla completa: ~8.640 tokens
________________________________________
3. Regla Crítica de Precisión (aplica SOLO a Modo Consulta)
Regla obligatoria
En Modo Consulta, toda pregunta debe incluir metadata explícita indicando:
•	Si la consulta es para una obra social específica, o
•	Si corresponde solo a procesos internos del Grupo Pediátrico
Esta metadata es obligatoria para:
•	Ejecutar un RAG preciso
•	Limitar correctamente el corpus
•	Evitar respuestas ambiguas o incorrectas
📌 Esta regla NO aplica al Modo Agente, que puede manejar ambigüedad y solicitar aclaraciones.
________________________________________
4. Escenarios Evaluados
Se evalúan cuatro escenarios, cada uno con los dos modos (Consulta y Agente) presentados en la misma tabla, con parámetros homogéneos.
________________________________________
ESCENARIO 1 – Modelo local en CPU (sin GPU)
Modelo utilizado: Qwen2.5 3B (Ollama)
Observación clave:
•	Problemas para usar herramientas
•	Mal comportamiento como agente
•	Latencias elevadas
Tabla operativa
Parámetro	Modo Consulta	Modo Agente
Tokens promedio	~1.000	~8.640
Tiempo promedio por respuesta	60–90 s	120–180 s
Interacciones por minuto	~0,8	~0,3
Interacciones por hora	~48	~18
Capacidad por día (8 h)	~384	~144
Costo mensual	$0	$0
Viabilidad productiva	❌ No	❌ No
Conclusión Escenario 1:
❌ No viable para producción. Solo útil para desarrollo o pruebas técnicas.
________________________________________
 
ESCENARIO 2 – Modelo local en GPU (RTX 3060 12GB)
Infraestructura
•	GPU: NVIDIA RTX 3060 (12GB)
•	CPU: Intel i5 / Ryzen equivalente
•	RAM: 64GB
________________________________________
Tabla operativa unificada
Parámetro	Modo Consulta	Modo Agente
Modelo recomendado	Qwen2.5 14B Q4	Llama 3.1 8B
Motivo	Pregunta dirigida, sin recall	Razonamiento + memoria
Tokens promedio	~1.000	~8.640
Tiempo promedio por respuesta	4–6 s	6–8 s (por respuesta)
Interacciones por minuto	~10	~6
Interacciones por hora	~600	~360
Capacidad por día (8 h)	~4.800	~2.880
Costo mensual	$0	$0
Viabilidad productiva	✅ Muy alta	✅ Alta
📌 Aclaración clave:
En Modo Agente, 6–8 segundos es el tiempo por respuesta, no por charla completa.
Conclusión Escenario 2:
✅ Escenario óptimo técnico, sin costos recurrentes. Requiere inversión inicial en hardware.
________________________________________
ESCENARIO 3 – Modelo cloud gratuito
Proveedor: Groq
Modelo: llama-3.3-70B (free tier)
Limitaciones: límites estrictos diarios y por minuto.
Tabla operativa
Parámetro	Modo Consulta	Modo Agente
Tokens promedio	~1.000	~8.640
Tiempo promedio por respuesta	<1 s	<2 s
Límite diario aproximado	~100 consultas	~12 charlas
Costo mensual	$0	$0
Viabilidad productiva	⚠️ Baja	❌ No
Conclusión Escenario 3:
⚠️ Solo para demos y pruebas, no para operación real.
________________________________________
 

ESCENARIO 4 – Modelo cloud pago (suscripción mensual)
Proveedor: Groq
Modelo: Llama 3.1 8B Instant
Costo promedio: USD 0,065 / 1M tokens (input + output)
Tabla operativa
Parámetro	Modo Consulta	Modo Agente
Tokens promedio por interacción	~1.000	~8.640
Tiempo promedio por respuesta	< 1 s	1–2 s
Costo unitario	~USD 0,00007	~USD 0,00056
Capacidad diaria	Ilimitada	Ilimitada
Costo mensual estimado	USD 1–5	USD 1–10
Calidad de respuesta	Alta	Buena
Comportamiento agente	❌ No aplica	✅ Correcto
Viabilidad productiva	✅ Muy alta	✅ Muy alta
Evaluación del escenario
•	Velocidad y disponibilidad óptimas
•	Costos extremadamente bajos incluso a alto volumen
•	No requiere inversión inicial
•	Dependencia de proveedor externo (cloud)
Conclusión Escenario 4
Ideal para puesta en producción inmediata, pruebas con usuarios reales y escalado progresivo sin riesgo financiero.
________________________________________
RESUMEN COMPARATIVO DE ESCENARIOS (visión ejecutiva)
Escenario	Infraestructura	Costo mensual	Latencia	Escala	Dependencia externa
CPU local	Baja	USD 0	❌ Alta	❌ Muy baja	No
GPU local	Media	USD 0	✅ Baja	✅ Alta	No
Cloud gratuito	baja	USD 0	✅ Muy baja	❌ Muy baja	Sí
Cloud pago	baja	USD 1–10	✅ Muy baja	✅ Muy alta	Sí
________________________________________
IMPACTO OPERATIVO Y ROI (con valores concretos)
Supuestos conservadores
•	100 consultas puntuales por día
•	10 charlas de enrolamiento por día
•	Costo horario administrativo: USD 6 / hora
________________________________________
Ahorro de tiempo humano
Consultas puntuales
•	Tiempo humano promedio: ~4 min
•	100 consultas → 400 min → 6,7 h/día
Charlas de enrolamiento
•	Tiempo humano promedio: ~20 min
•	10 charlas → 200 min → 3,3 h/día
Ahorro total diario: ~10 horas humanas
________________________________________
Ahorro mensual estimado
•	10 h/día × 22 días = 220 h/mes
•	220 h × USD 6 = USD 1.320 / mes
________________________________________
Comparación costo vs beneficio
Concepto	USD / mes
Ahorro operativo estimado	1.320
Costo agente (cloud pago)	1–10
Beneficio neto mensual	~1.310
➡️ ROI extremadamente alto con inversión mínima
________________________________________
BENEFICIOS ADICIONALES (no financieros)
Para Dirección Ejecutiva (Adolfo Korman)
•	Reducción directa de costos operativos
•	Escalabilidad sin aumento de personal
•	Mejora inmediata en tiempos de atención
•	Inversión reversible y de bajo riesgo
Para Dirección de TI (Patricia Rivas)
•	Arquitectura moderna y controlada
•	RAG preciso con metadata explícita
•	Posibilidad de migrar a infraestructura local
•	Observabilidad y auditoría del sistema
Para pacientes y prestadores
•	Atención inmediata (segundos, no minutos)
•	Disponibilidad 24/7
•	Menos fricción y derivaciones internas

________________________________________ 
CONCLUSIONES GENERALES
1.	El agente conversacional no es un bot, sino un sistema de IA con razonamiento y acceso a documentación.
2.	Existen dos modos claramente diferenciados:
o	Modo Consulta: rápido, dirigido, de alto volumen.
o	Modo Agente: conversación estructurada para enrolamiento.
3.	El escenario Cloud pago permite:
o	Producción inmediata.
o	Costos insignificantes.
o	Validación real del impacto.
4.	El ROI se alcanza en el primer mes, incluso con volúmenes bajos.
5.	La infraestructura local con GPU queda como optimización futura, no como requisito inicial.
________________________________________
RECOMENDACIÓN FINAL
Fase 1 – Inmediata
•	Implementar Escenario 4 (Cloud pago).
•	Medir volumen real y ahorro efectivo.
Fase 2 – Optimización
•	Evaluar migración parcial o total a GPU local.
•	Eliminar costos recurrentes si el volumen lo justifica.
________________________________________
GLOSARIO (breve)
Término	Significado
Agente conversacional	Sistema de IA con razonamiento y uso de herramientas
Modo Consulta	Pregunta puntual, sin memoria
Modo Agente	Conversación guiada con razonamiento
RAG	Búsqueda documental previa a responder
Tokens	Unidad de costo y procesamiento de texto
Costo unitario	Costo por token o interacción en modalidad cloud
________________________________________
 
CIERRE EJECUTIVO Y PRÓXIMOS PASOS
Cierre Ejecutivo:
El presente informe evidencia que la implementación del agente conversacional de IA en el Grupo Pediátrico optimiza tiempos de atención, mejora la experiencia del paciente y genera un ahorro significativo de recursos administrativos con inversión mínima.
La adopción del escenario Cloud pago permite iniciar operaciones de manera inmediata, con capacidad ilimitada y alta calidad de respuestas.
La infraestructura local con GPU puede evaluarse como optimización futura según el crecimiento del volumen de consultas y charlas de enrolamiento.
Próximos Pasos Recomendados:
1.	Activar el agente Cloud pago (Llama 3.1 8B Instant) para pruebas iniciales con usuarios reales.
2.	Medir indicadores clave: volumen de consultas, tiempo promedio por interacción y ahorro en horas administrativas.
3.	Evaluar, a mediano plazo, la implementación local con GPU RTX 3060 para consultas específicas de alto volumen o necesidades de mayor control.
4.	Ajustar flujos, embeddings y metadata de RAG para asegurar precisión según obra social o procesos internos del Grupo Pediátrico.
Firma:
Hernán Hamra
Autor del informe
15 de enero de 2026



