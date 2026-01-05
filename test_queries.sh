#!/bin/bash
# Script de prueba de consultas al agente hospitalario

API_URL="http://127.0.0.1:8000/query"

echo "==================================="
echo "PRUEBAS - AGENTE HOSPITALARIO"
echo "==================================="

# Test 1: Enrolamiento ENSALUD
echo -e "\n[TEST 1] Consulta sobre ENSALUD..."
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué documentos necesito para enrolar un paciente de ENSALUD?", "obra_social": "ENSALUD"}' \
  | jq -r '.respuesta'

echo -e "\n\n---\n"

# Test 2: Planes ASI
echo -e "\n[TEST 2] Consulta sobre planes ASI..."
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuáles son los planes disponibles de ASI?", "obra_social": "ASI"}' \
  | jq -r '.respuesta'

echo -e "\n\n---\n"

# Test 3: IOSFA checklist
echo -e "\n[TEST 3] Consulta sobre IOSFA..."
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué pasos debo seguir para IOSFA?", "obra_social": "IOSFA"}' \
  | jq -r '.respuesta'

echo -e "\n\n---\n"

# Test 4: Pregunta general
echo -e "\n[TEST 4] Consulta general (sin obra social específica)..."
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué documentación básica necesito siempre?"}' \
  | jq -r '.respuesta'

echo -e "\n\n---\n"

# Test 5: Pregunta fuera del contexto
echo -e "\n[TEST 5] Consulta fuera del contexto (debería decir que no tiene la info)..."
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuál es el horario de atención del hospital?"}' \
  | jq -r '.respuesta'

echo -e "\n\n==================================="
echo "PRUEBAS COMPLETADAS"
echo "==================================="
