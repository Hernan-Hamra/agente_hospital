#!/usr/bin/env python3
"""
Test exhaustivo de RAG con 50 preguntas complejas
Evalúa retrieval puro (sin LLM) para todas las obras sociales

Uso:
    pytest escenario_1/tests/test_rag_50.py -v
"""
import sys
import pytest
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from escenario_1.rag.retriever import ChromaRetriever
from escenario_1.core.query_rewriter import rewrite_query

CHROMA_PATH = str(project_root / "shared" / "data" / "chroma_db")


@dataclass
class TestCase:
    """Caso de prueba para RAG"""
    id: int
    categoria: str
    query: str
    obra_social: str
    dato_esperado: str
    descripcion: str


# ============================================================
# 50 CASOS DE PRUEBA COMPLEJOS
# ============================================================

TEST_CASES = [
    # ==================== ASI (1-12) ====================
    TestCase(1, "contacto", "teléfono mesa operativa ASI", "ASI", "0810-888-8274", "Tel Mesa Op"),
    TestCase(2, "contacto", "mail autorizaciones ASI", "ASI", "autorizaciones@asi.com.ar", "Mail Autoriz"),
    TestCase(3, "contacto", "mail internaciones ASI", "ASI", "internados.asi@asi.com.ar", "Mail Intern"),
    TestCase(4, "contacto", "correo liquidaciones ASI", "ASI", "liquidaciones@asi.com.ar", "Mail Liquid"),
    TestCase(5, "contacto", "email cuidados domiciliarios ASI", "ASI", "cuidadosdomiciliarios@asi.com.ar", "Mail Cuid Dom"),
    TestCase(6, "protocolo", "plazo denuncia internación ASI", "ASI", "24", "Plazo denuncia"),
    TestCase(7, "protocolo", "requisitos internación programada ASI", "ASI", "orden autorizada", "Req intern prog"),
    TestCase(8, "protocolo", "documentación para autorizaciones ASI", "ASI", "orden", "Doc autoriz"),
    TestCase(9, "contacto", "como contacto a ASI por teléfono", "ASI", "0810", "Contacto tel"),
    TestCase(10, "contacto", "a donde mando mail para autorizar en ASI", "ASI", "autorizaciones@asi", "Donde mandar mail"),
    TestCase(11, "protocolo", "en cuanto tiempo debo avisar una internación ASI", "ASI", "24", "Tiempo aviso"),
    TestCase(12, "protocolo", "que necesito para internarme con ASI", "ASI", "orden", "Necesito internar"),

    # ==================== ENSALUD (13-35) ====================
    TestCase(13, "contacto", "teléfono ENSALUD", "ENSALUD", "66075765", "Tel ENSALUD"),
    TestCase(14, "contacto", "mail administración ENSALUD", "ENSALUD", "administracion@ensalud.org", "Mail admin"),
    TestCase(15, "contacto", "mail auditoría ENSALUD", "ENSALUD", "auditoria@ensalud.org", "Mail audit"),
    TestCase(16, "contacto", "web prestadores ENSALUD", "ENSALUD", "ensalud.org", "Web prest"),
    TestCase(17, "coseguro", "valor coseguro médico especialista ENSALUD", "ENSALUD", "2912", "Coseg espec"),
    TestCase(18, "coseguro", "precio consulta médico familia ENSALUD", "ENSALUD", "1553", "Coseg familia"),
    TestCase(19, "coseguro", "cuanto sale kinesiología ENSALUD", "ENSALUD", "971", "Coseg kinesio"),
    TestCase(20, "coseguro", "coseguro fonoaudiología ENSALUD", "ENSALUD", "971", "Coseg fono"),
    TestCase(21, "coseguro", "coseguro laboratorio básico ENSALUD", "ENSALUD", "971", "Coseg lab"),
    TestCase(22, "coseguro", "valor APB ENSALUD", "ENSALUD", "6000", "Coseg APB"),
    TestCase(23, "coseguro", "coseguro imágenes alta complejidad ENSALUD", "ENSALUD", "4854", "Coseg img alta"),
    TestCase(24, "coseguro", "cuanto cuesta consulta con especialista", "ENSALUD", "2912", "Cuanto cuesta esp"),
    TestCase(25, "coseguro", "cuanto es el copago de médico de familia", "ENSALUD", "1553", "Copago familia"),
    TestCase(26, "coseguro", "tarifa consulta pediatra ENSALUD", "ENSALUD", "1553", "Tarifa pediatra"),
    TestCase(27, "coseguro", "precio sesión de kinesiología", "ENSALUD", "971", "Precio kinesio"),
    TestCase(28, "coseguro", "quienes no pagan coseguro ENSALUD", "ENSALUD", "HIV", "Exentos"),
    TestCase(29, "coseguro", "exentos de coseguro ENSALUD", "ENSALUD", "Oncología", "Exentos 2"),
    TestCase(30, "cobertura", "planes disponibles ENSALUD", "ENSALUD", "Delta", "Planes"),
    TestCase(31, "cobertura", "que planes tiene ENSALUD", "ENSALUD", "Krono", "Planes 2"),
    TestCase(32, "cobertura", "necesito autorización para consulta especialista ENSALUD", "ENSALUD", "PREVIA", "Autoriz esp"),
    TestCase(33, "cobertura", "internación programada requiere autorización ENSALUD", "ENSALUD", "PREVIA", "Autoriz intern"),
    TestCase(34, "cobertura", "vigencia de las autorizaciones ENSALUD", "ENSALUD", "30", "Vigencia"),
    TestCase(35, "cobertura", "cuanto duran las autorizaciones ENSALUD", "ENSALUD", "30", "Duración autoriz"),

    # ==================== IOSFA (36-42) ====================
    TestCase(36, "contacto", "mail consultas IOSFA", "IOSFA", "consultas@iosfa", "Mail IOSFA"),
    TestCase(37, "protocolo", "documentos para consulta IOSFA", "IOSFA", "VALIDADOR", "Doc consulta"),
    TestCase(38, "protocolo", "requisitos prácticas IOSFA", "IOSFA", "AUTORIZACION", "Req prácticas"),
    TestCase(39, "protocolo", "que necesito para guardia IOSFA", "IOSFA", "DNI", "Req guardia"),
    TestCase(40, "protocolo", "documentación internación IOSFA", "IOSFA", "VALIDADOR", "Doc intern"),
    TestCase(41, "protocolo", "bono de consulta IOSFA", "IOSFA", "BONO", "Bono consulta"),
    TestCase(42, "protocolo", "que debo presentar para prácticas IOSFA", "IOSFA", "BONO DE PRACTICAS", "Presentar pract"),

    # ==================== GRUPO PEDIATRICO (43-50) ====================
    TestCase(43, "protocolo", "documentación básica grupo pediátrico", "GRUPO_PEDIATRICO", "DNI", "Doc básica"),
    TestCase(44, "protocolo", "requisitos ingreso guardia grupo pediátrico", "GRUPO_PEDIATRICO", "credencial", "Req guardia"),
    TestCase(45, "protocolo", "documentos internación urgencia grupo pediátrico", "GRUPO_PEDIATRICO", "Denuncia", "Doc intern urg"),
    TestCase(46, "protocolo", "requisitos internación programada grupo pediátrico", "GRUPO_PEDIATRICO", "Presupuesto", "Req intern prog"),
    TestCase(47, "protocolo", "quienes no pagan coseguro grupo pediátrico", "GRUPO_PEDIATRICO", "Guardia", "Exentos GP"),
    TestCase(48, "protocolo", "exentos de coseguro en pediatrico", "GRUPO_PEDIATRICO", "PMI", "Exentos GP 2"),
    TestCase(49, "protocolo", "que cubre el PMI grupo pediátrico", "GRUPO_PEDIATRICO", "PMI", "PMI cobertura"),
    TestCase(50, "protocolo", "pacientes oncológicos pagan coseguro grupo pediátrico", "GRUPO_PEDIATRICO", "Oncológicos", "Onco exento"),
]


@pytest.fixture(scope="module")
def retriever():
    """Carga ChromaDB una sola vez"""
    if not Path(CHROMA_PATH).exists():
        pytest.skip("ChromaDB no encontrado")
    return ChromaRetriever(persist_directory=CHROMA_PATH)


class TestRAG50Preguntas:
    """50 tests de retrieval RAG"""

    @pytest.mark.parametrize("test_case", TEST_CASES, ids=[f"q{t.id}_{t.descripcion}" for t in TEST_CASES])
    def test_rag_retrieval(self, retriever, test_case):
        """Test parametrizado para cada una de las 50 preguntas"""
        # Aplicar query rewriting
        search_query = rewrite_query(test_case.query, test_case.obra_social)

        # Buscar
        chunks = retriever.retrieve(
            query=search_query,
            top_k=3,
            obra_social_filter=test_case.obra_social
        )

        # Verificar que encontró chunks
        assert len(chunks) > 0, f"No encontró chunks para: {test_case.query}"

        # Verificar que el dato esperado está en algún chunk
        encontrado = False
        for chunk_text, metadata, score in chunks:
            if test_case.dato_esperado.lower() in chunk_text.lower():
                encontrado = True
                break

        assert encontrado, (
            f"[{test_case.id}] No encontró '{test_case.dato_esperado}' en chunks\n"
            f"Query: {test_case.query}\n"
            f"Obra social: {test_case.obra_social}\n"
            f"Top chunk: {chunks[0][0][:200]}..."
        )


def run_evaluation_with_report():
    """Ejecuta evaluación y genera reporte JSON"""
    print("=" * 80)
    print("TEST RAG 50 PREGUNTAS - Escenario 1 (ChromaDB)")
    print("=" * 80)

    retriever = ChromaRetriever(persist_directory=CHROMA_PATH)
    print(f"ChromaDB cargado: {retriever.count()} chunks\n")

    results = []
    for test in TEST_CASES:
        search_query = rewrite_query(test.query, test.obra_social)
        chunks = retriever.retrieve(
            query=search_query,
            top_k=3,
            obra_social_filter=test.obra_social
        )

        encontrado = False
        mejor_sim = 0.0
        for chunk_text, metadata, score in chunks:
            if test.dato_esperado.lower() in chunk_text.lower():
                encontrado = True
                mejor_sim = score
                break
            if score > mejor_sim:
                mejor_sim = score

        results.append({
            "id": test.id,
            "categoria": test.categoria,
            "query": test.query,
            "obra_social": test.obra_social,
            "dato_esperado": test.dato_esperado,
            "encontrado": encontrado,
            "similarity": round(mejor_sim, 4)
        })

        status = "✅" if encontrado else "❌"
        print(f"{status} [{test.id:02d}] {test.query[:50]}")

    # Estadísticas
    total = len(results)
    correctos = sum(1 for r in results if r["encontrado"])

    # Por categoría
    categorias = {}
    for r in results:
        cat = r["categoria"]
        if cat not in categorias:
            categorias[cat] = {"total": 0, "correctos": 0}
        categorias[cat]["total"] += 1
        if r["encontrado"]:
            categorias[cat]["correctos"] += 1

    # Por obra social
    obras = {}
    for r in results:
        os = r["obra_social"]
        if os not in obras:
            obras[os] = {"total": 0, "correctos": 0}
        obras[os]["total"] += 1
        if r["encontrado"]:
            obras[os]["correctos"] += 1

    print(f"\n{'=' * 80}")
    print(f"RESUMEN: {correctos}/{total} = {correctos/total*100:.1f}%")
    print("=" * 80)

    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(__file__).parent.parent / "reports" / f"reporte_rag50_{timestamp}.json"
    report_path.parent.mkdir(exist_ok=True)

    report = {
        "fecha": datetime.now().isoformat(),
        "rag_type": "ChromaDB",
        "resumen": {
            "total": total,
            "correctos": correctos,
            "porcentaje": round(correctos / total * 100, 1)
        },
        "por_categoria": {k: {**v, "porcentaje": round(v["correctos"]/v["total"]*100, 1)} for k, v in categorias.items()},
        "por_obra_social": {k: {**v, "porcentaje": round(v["correctos"]/v["total"]*100, 1)} for k, v in obras.items()},
        "resultados": results
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Reporte guardado: {report_path}")
    return correctos, total


if __name__ == "__main__":
    # Ejecutar con reporte
    run_evaluation_with_report()
