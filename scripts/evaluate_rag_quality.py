#!/usr/bin/env python3
"""
Evaluador de calidad del RAG - Sin LLM

Evalúa si el RAG encuentra correctamente:
1. Datos sensibles: teléfonos, emails, copagos
2. Contenido de tablas
3. Protocolos y requisitos

Uso:
    python scripts/evaluate_rag_quality.py
"""
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re

# Agregar backend al path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")


@dataclass
class TestCase:
    """Caso de prueba para RAG"""
    categoria: str  # sensible, tabla, protocolo
    query: str
    obra_social: str
    dato_esperado: str  # Lo que debería encontrar
    ubicacion_original: str  # Dónde validar en archivo original
    es_tabla: bool = False


@dataclass
class TestResult:
    """Resultado de un caso de prueba"""
    test: TestCase
    encontrado: bool
    similarity: float
    chunk_text: str
    chunk_index: int
    observacion: str


# ============================================================
# CASOS DE PRUEBA - Datos que DEBEN estar en el RAG
# ============================================================

TEST_CASES = [
    # ===================== DATOS SENSIBLES =====================

    # ASI - Teléfonos
    TestCase(
        categoria="sensible",
        query="teléfono mesa operativa ASI",
        obra_social="ASI",
        dato_esperado="0810-888-8274",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx - Tabla de contactos"
    ),
    TestCase(
        categoria="sensible",
        query="teléfono liquidaciones ASI",
        obra_social="ASI",
        dato_esperado="0810-888-8274 int. 347/381",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx - Tabla de contactos"
    ),

    # ASI - Emails
    TestCase(
        categoria="sensible",
        query="mail autorizaciones ASI",
        obra_social="ASI",
        dato_esperado="autorizaciones@asi.com.ar",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx - Tabla de contactos"
    ),
    TestCase(
        categoria="sensible",
        query="mail internaciones ASI",
        obra_social="ASI",
        dato_esperado="internados.asi@asi.com.ar",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx - Tabla de contactos"
    ),
    TestCase(
        categoria="sensible",
        query="mail liquidaciones ASI",
        obra_social="ASI",
        dato_esperado="liquidaciones@asi.com.ar",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx - Tabla de contactos"
    ),

    # ENSALUD - Teléfonos
    TestCase(
        categoria="sensible",
        query="teléfono ENSALUD contacto",
        obra_social="ENSALUD",
        dato_esperado="11-66075765",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Final del documento"
    ),

    # ENSALUD - Emails
    TestCase(
        categoria="sensible",
        query="mail administración ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="administracion@ensalud.org",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Final del documento"
    ),
    TestCase(
        categoria="sensible",
        query="mail auditoría ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="auditoria@ensalud.org",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Sección Parte Diario"
    ),

    # IOSFA - Teléfonos/Emails (pueden no existir)
    TestCase(
        categoria="sensible",
        query="teléfono IOSFA contacto",
        obra_social="IOSFA",
        dato_esperado="(verificar si existe)",
        ubicacion_original="data/obras_sociales/iosfa/2024-01-04_checklist.docx"
    ),
    TestCase(
        categoria="sensible",
        query="mail IOSFA contacto",
        obra_social="IOSFA",
        dato_esperado="(verificar si existe)",
        ubicacion_original="data/obras_sociales/iosfa/2024-01-04_checklist.docx"
    ),

    # ===================== COPAGOS (TABLAS) =====================

    TestCase(
        categoria="sensible",
        query="copago consulta médico especialista ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="$ 2912",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla COSEGUROS",
        es_tabla=True
    ),
    TestCase(
        categoria="sensible",
        query="copago consulta médico familia ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="$ 1553",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla COSEGUROS",
        es_tabla=True
    ),
    TestCase(
        categoria="sensible",
        query="copago kinesiología ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="$ 971",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla COSEGUROS",
        es_tabla=True
    ),
    TestCase(
        categoria="sensible",
        query="copago fonoaudiología ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="$ 971",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla COSEGUROS",
        es_tabla=True
    ),
    TestCase(
        categoria="sensible",
        query="copago APB ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="$ 6000",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla COSEGUROS",
        es_tabla=True
    ),
    TestCase(
        categoria="sensible",
        query="exentos de coseguro ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="HIV, Oncología, Discapacidad, PMI",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla COSEGUROS",
        es_tabla=True
    ),

    # ===================== TABLAS - PLANES Y COBERTURAS =====================

    TestCase(
        categoria="tabla",
        query="planes ENSALUD disponibles",
        obra_social="ENSALUD",
        dato_esperado="DELTA PLUS, KRONO, QUANTUM, INTEGRAL, TOTAL, GLOBAL",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Encabezado",
        es_tabla=True
    ),
    TestCase(
        categoria="tabla",
        query="consulta especialista necesita autorización ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="SI PREVIA o NO según plan",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla coberturas",
        es_tabla=True
    ),
    TestCase(
        categoria="tabla",
        query="internación programada autorización ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="SI PREVIA",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla internaciones",
        es_tabla=True
    ),
    TestCase(
        categoria="tabla",
        query="vigencia autorizaciones ENSALUD",
        obra_social="ENSALUD",
        dato_esperado="30 días",
        ubicacion_original="data/obras_sociales/ensalud/2024-01-04_normativa.pdf - Tabla internaciones",
        es_tabla=True
    ),

    # ===================== PROTOCOLOS =====================

    # IOSFA - Requisitos de ingreso
    TestCase(
        categoria="protocolo",
        query="documentos ingreso consulta IOSFA",
        obra_social="IOSFA",
        dato_esperado="VALIDADOR, DNI, BONO DE CONSULTA",
        ubicacion_original="data/obras_sociales/iosfa/2024-01-04_checklist.docx - Checklist"
    ),
    TestCase(
        categoria="protocolo",
        query="documentos ingreso prácticas IOSFA",
        obra_social="IOSFA",
        dato_esperado="VALIDADOR, DNI, BONO DE PRACTICAS, AUTORIZACION",
        ubicacion_original="data/obras_sociales/iosfa/2024-01-04_checklist.docx - Checklist"
    ),
    TestCase(
        categoria="protocolo",
        query="documentos ingreso guardia IOSFA",
        obra_social="IOSFA",
        dato_esperado="DNI, VALIDADOR",
        ubicacion_original="data/obras_sociales/iosfa/2024-01-04_checklist.docx - Checklist"
    ),
    TestCase(
        categoria="protocolo",
        query="documentos internación programada IOSFA",
        obra_social="IOSFA",
        dato_esperado="DNI, VALIDADOR",
        ubicacion_original="data/obras_sociales/iosfa/2024-01-04_checklist.docx - Checklist"
    ),

    # GRUPO PEDIATRICO - Protocolos generales
    TestCase(
        categoria="protocolo",
        query="documentación básica ingreso grupo pediátrico",
        obra_social="GRUPO_PEDIATRICO",
        dato_esperado="DNI, Credencial, Validación, Diagnóstico",
        ubicacion_original="data/grupo_pediatrico/checklist_general_grupo_pediatrico.docx"
    ),
    TestCase(
        categoria="protocolo",
        query="requisitos guardia grupo pediátrico",
        obra_social="GRUPO_PEDIATRICO",
        dato_esperado="DNI, credencial, validación afiliatoria",
        ubicacion_original="data/grupo_pediatrico/checklist_general_grupo_pediatrico.docx"
    ),
    TestCase(
        categoria="protocolo",
        query="requisitos internación urgencia grupo pediátrico",
        obra_social="GRUPO_PEDIATRICO",
        dato_esperado="DNI, credencial, Validación, Denuncia",
        ubicacion_original="data/grupo_pediatrico/checklist_general_grupo_pediatrico.docx"
    ),
    TestCase(
        categoria="protocolo",
        query="requisitos internación programada grupo pediátrico",
        obra_social="GRUPO_PEDIATRICO",
        dato_esperado="Orden autorizada, Presupuesto",
        ubicacion_original="data/grupo_pediatrico/checklist_general_grupo_pediatrico.docx"
    ),
    TestCase(
        categoria="protocolo",
        query="exentos coseguro grupo pediátrico",
        obra_social="GRUPO_PEDIATRICO",
        dato_esperado="Guardia, PMI, Oncológicos, HIV, Discapacidad",
        ubicacion_original="data/grupo_pediatrico/checklist_general_grupo_pediatrico.docx"
    ),

    # ASI - Protocolos
    TestCase(
        categoria="protocolo",
        query="requisitos internación programada ASI",
        obra_social="ASI",
        dato_esperado="orden autorizada emitida por ASI",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx"
    ),
    TestCase(
        categoria="protocolo",
        query="denuncia internación plazo ASI",
        obra_social="ASI",
        dato_esperado="24 hs",
        ubicacion_original="data/obras_sociales/asi/2024-01-04_normas.docx"
    ),
]


def run_evaluation():
    """Ejecuta la evaluación del RAG"""
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    import pickle

    print("="*70)
    print("EVALUACIÓN DE CALIDAD DEL RAG - SIN LLM")
    print("="*70)

    # Cargar modelo y datos
    print("\nCargando modelo de embeddings...")
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')

    print("Cargando índice FAISS...")
    index = faiss.read_index(str(backend_path / 'faiss_index/index.faiss'))
    with open(backend_path / 'faiss_index/documents.pkl', 'rb') as f:
        docs = pickle.load(f)

    print(f"Índice cargado: {len(docs)} chunks")
    print(f"Casos de prueba: {len(TEST_CASES)}")

    # Ejecutar pruebas
    results: List[TestResult] = []

    for test in TEST_CASES:
        # Generar embedding de la query
        query_embedding = model.encode([test.query])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Buscar en FAISS
        distances, indices = index.search(query_embedding, 20)

        # Filtrar por obra social y buscar el dato
        encontrado = False
        mejor_chunk = None
        mejor_similarity = 0
        mejor_index = -1

        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                break

            doc = docs[idx]
            similarity = (dist + 1) / 2

            # Filtrar por obra social
            if doc.get('obra_social', '').upper() != test.obra_social.upper():
                continue

            chunk_text = doc.get('text', '')

            # Verificar si el dato esperado está en el chunk
            dato_lower = test.dato_esperado.lower()
            chunk_lower = chunk_text.lower()

            # Para datos que son "verificar si existe", solo checkeamos que haya chunks
            if "verificar" in dato_lower:
                if mejor_chunk is None:
                    mejor_chunk = chunk_text
                    mejor_similarity = similarity
                    mejor_index = idx
                continue

            # Buscar coincidencias parciales
            datos_buscar = [d.strip() for d in test.dato_esperado.split(',')]
            coincidencias = sum(1 for d in datos_buscar if d.lower() in chunk_lower)

            if coincidencias > 0 or any(d in chunk_lower for d in datos_buscar):
                encontrado = True
                mejor_chunk = chunk_text
                mejor_similarity = similarity
                mejor_index = idx
                break

            # Guardar el mejor chunk de esta obra social
            if mejor_chunk is None or similarity > mejor_similarity:
                mejor_chunk = chunk_text
                mejor_similarity = similarity
                mejor_index = idx

        # Crear resultado
        observacion = ""
        if not encontrado:
            if mejor_chunk and "verificar" in test.dato_esperado.lower():
                observacion = "Chunk encontrado pero sin datos de contacto"
            elif mejor_chunk:
                observacion = f"Chunk más cercano no contiene el dato esperado"
            else:
                observacion = "No se encontraron chunks de esta obra social"
        else:
            observacion = "OK - Dato encontrado"

        results.append(TestResult(
            test=test,
            encontrado=encontrado,
            similarity=mejor_similarity,
            chunk_text=mejor_chunk[:300] if mejor_chunk else "",
            chunk_index=mejor_index,
            observacion=observacion
        ))

    return results


def print_results(results: List[TestResult]):
    """Imprime los resultados en formato tabla"""

    # Agrupar por categoría
    categorias = {}
    for r in results:
        cat = r.test.categoria
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(r)

    print("\n" + "="*100)
    print("RESULTADOS POR CATEGORÍA")
    print("="*100)

    total_ok = 0
    total = len(results)

    for cat, cat_results in categorias.items():
        ok = sum(1 for r in cat_results if r.encontrado)
        total_ok += ok

        print(f"\n{'─'*100}")
        print(f"📁 {cat.upper()} ({ok}/{len(cat_results)} = {ok/len(cat_results)*100:.0f}%)")
        print(f"{'─'*100}")
        print(f"{'#':<3} {'Query':<40} {'OS':<10} {'Sim':<6} {'OK':<4} {'Dato Esperado':<30}")
        print(f"{'─'*100}")

        for i, r in enumerate(cat_results, 1):
            status = "✅" if r.encontrado else "❌"
            sim = f"{r.similarity:.2f}" if r.similarity > 0 else "N/A"
            dato = r.test.dato_esperado[:28] + ".." if len(r.test.dato_esperado) > 30 else r.test.dato_esperado
            query = r.test.query[:38] + ".." if len(r.test.query) > 40 else r.test.query
            print(f"{i:<3} {query:<40} {r.test.obra_social:<10} {sim:<6} {status:<4} {dato:<30}")

    print(f"\n{'='*100}")
    print(f"RESUMEN TOTAL: {total_ok}/{total} = {total_ok/total*100:.1f}%")
    print(f"{'='*100}")

    # Tabla de validación para el usuario
    print("\n\n" + "="*120)
    print("TABLA DE VALIDACIÓN - Para corroborar en archivos originales")
    print("="*120)
    print(f"{'#':<3} {'Query':<35} {'Dato Esperado':<25} {'Encontrado':<5} {'Ubicación Original':<50}")
    print(f"{'─'*120}")

    for i, r in enumerate(results, 1):
        status = "✅" if r.encontrado else "❌"
        query = r.test.query[:33] + ".." if len(r.test.query) > 35 else r.test.query
        dato = r.test.dato_esperado[:23] + ".." if len(r.test.dato_esperado) > 25 else r.test.dato_esperado
        ubicacion = r.test.ubicacion_original[:48] + ".." if len(r.test.ubicacion_original) > 50 else r.test.ubicacion_original
        print(f"{i:<3} {query:<35} {dato:<25} {status:<5} {ubicacion:<50}")

    return total_ok, total


def print_failed_details(results: List[TestResult]):
    """Imprime detalles de los casos fallidos"""
    failed = [r for r in results if not r.encontrado]

    if not failed:
        print("\n✅ Todos los casos pasaron!")
        return

    print(f"\n\n{'='*100}")
    print(f"DETALLE DE CASOS FALLIDOS ({len(failed)})")
    print(f"{'='*100}")

    for i, r in enumerate(failed, 1):
        print(f"\n{'─'*100}")
        print(f"❌ CASO {i}: {r.test.query}")
        print(f"{'─'*100}")
        print(f"   Obra Social:     {r.test.obra_social}")
        print(f"   Dato Esperado:   {r.test.dato_esperado}")
        print(f"   Ubicación:       {r.test.ubicacion_original}")
        print(f"   Similarity:      {r.similarity:.4f}")
        print(f"   Observación:     {r.observacion}")
        if r.chunk_text:
            print(f"   Chunk cercano:   {r.chunk_text[:200]}...")


def save_report(results: List[TestResult], total_ok: int, total: int):
    """Guarda el reporte en JSON"""
    report = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "total_tests": total,
        "passed": total_ok,
        "failed": total - total_ok,
        "percentage": round(total_ok/total*100, 1),
        "by_category": {},
        "results": []
    }

    # Agrupar por categoría
    categorias = {}
    for r in results:
        cat = r.test.categoria
        if cat not in categorias:
            categorias[cat] = {"passed": 0, "failed": 0, "tests": []}
        if r.encontrado:
            categorias[cat]["passed"] += 1
        else:
            categorias[cat]["failed"] += 1

    report["by_category"] = {
        cat: {
            "passed": data["passed"],
            "failed": data["failed"],
            "total": data["passed"] + data["failed"],
            "percentage": round(data["passed"]/(data["passed"]+data["failed"])*100, 1)
        }
        for cat, data in categorias.items()
    }

    for r in results:
        report["results"].append({
            "categoria": r.test.categoria,
            "query": r.test.query,
            "obra_social": r.test.obra_social,
            "dato_esperado": r.test.dato_esperado,
            "ubicacion_original": r.test.ubicacion_original,
            "es_tabla": r.test.es_tabla,
            "encontrado": r.encontrado,
            "similarity": round(r.similarity, 4),
            "observacion": r.observacion,
            "chunk_preview": r.chunk_text[:200] if r.chunk_text else ""
        })

    report_path = project_root / "reports" / "rag_quality_evaluation.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Reporte guardado en: {report_path}")


if __name__ == "__main__":
    results = run_evaluation()
    total_ok, total = print_results(results)
    print_failed_details(results)
    save_report(results, total_ok, total)
