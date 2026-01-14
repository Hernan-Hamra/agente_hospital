#!/bin/bash
# Script para ejecutar tests del agente hospitalario

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Activar virtualenv
echo -e "${YELLOW}📦 Activando entorno virtual...${NC}"
source backend/venv/bin/activate

# Función para mostrar uso
show_usage() {
    echo ""
    echo "Uso: ./run_tests.sh [opción]"
    echo ""
    echo "Opciones:"
    echo "  unit          - Ejecutar solo tests unitarios (rápidos)"
    echo "  integration   - Ejecutar solo tests de integración"
    echo "  system        - Ejecutar solo tests de sistema (lentos)"
    echo "  all           - Ejecutar todos los tests"
    echo "  coverage      - Ejecutar con reporte de cobertura"
    echo ""
    echo "Ejemplos:"
    echo "  ./run_tests.sh unit"
    echo "  ./run_tests.sh integration"
    echo "  ./run_tests.sh all"
    echo ""
}

# Si no hay argumentos, mostrar uso
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Ejecutar según opción
case "$1" in
    unit)
        echo -e "${GREEN}🧪 Ejecutando tests unitarios...${NC}"
        pytest tests/unit/ -v
        ;;

    integration)
        echo -e "${GREEN}🔗 Ejecutando tests de integración...${NC}"
        echo -e "${YELLOW}⚠️  Requiere índice FAISS actualizado${NC}"
        pytest tests/integration/ -v
        ;;

    system)
        echo -e "${GREEN}🌐 Ejecutando tests de sistema...${NC}"
        echo -e "${YELLOW}⚠️  Requiere Ollama corriendo${NC}"
        pytest tests/system/ -v
        ;;

    all)
        echo -e "${GREEN}🚀 Ejecutando TODOS los tests...${NC}"
        pytest tests/ -v
        ;;

    coverage)
        echo -e "${GREEN}📊 Ejecutando tests con cobertura...${NC}"
        pytest tests/ -v --cov=backend/app --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}✅ Reporte de cobertura generado en htmlcov/index.html${NC}"
        ;;

    *)
        echo -e "${RED}❌ Opción inválida: $1${NC}"
        show_usage
        exit 1
        ;;
esac

# Capturar código de salida
exit_code=$?

# Mensaje final
echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Tests completados exitosamente${NC}"
else
    echo -e "${RED}❌ Algunos tests fallaron${NC}"
fi

exit $exit_code
