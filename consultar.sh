#!/bin/bash
# Script interactivo para consultar al agente hospitalario

API_URL="http://127.0.0.1:8000/query"

echo "=========================================="
echo "   AGENTE HOSPITALARIO - CONSULTAS"
echo "=========================================="
echo ""

# Leer la pregunta
echo "Escribí tu pregunta:"
read -r PREGUNTA

echo ""
echo "¿Para qué obra social? (ENSALUD/ASI/IOSFA o dejá en blanco para todas)"
read -r OBRA_SOCIAL

echo ""
echo "⏳ Procesando tu consulta (puede tardar ~2 minutos)..."
echo ""

# Armar el JSON según si hay obra social o no
if [ -z "$OBRA_SOCIAL" ]; then
  JSON_DATA="{\"pregunta\": \"$PREGUNTA\"}"
else
  JSON_DATA="{\"pregunta\": \"$PREGUNTA\", \"obra_social\": \"$OBRA_SOCIAL\"}"
fi

# Hacer la consulta y mostrar solo la respuesta
RESPONSE=$(curl -s -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d "$JSON_DATA")

# Verificar si jq está instalado
if command -v jq &> /dev/null; then
  echo ""
  echo "=========================================="
  echo "   RESPUESTA:"
  echo "=========================================="
  echo ""
  echo "$RESPONSE" | jq -r '.respuesta'
  echo ""
  echo "=========================================="
  echo ""
  echo "Fuentes consultadas:"
  echo "$RESPONSE" | jq -r '.fuentes[] | "  - \(.archivo) (relevancia: \(.relevancia))"'
else
  # Si no tiene jq, mostrar el JSON completo
  echo ""
  echo "=========================================="
  echo "   RESPUESTA (JSON):"
  echo "=========================================="
  echo ""
  echo "$RESPONSE"
fi

echo ""
echo "=========================================="
