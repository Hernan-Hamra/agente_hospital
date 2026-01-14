#!/usr/bin/env python3
"""
Test rápido de las mejoras implementadas en el bot
Evalúa 3 preguntas críticas del reporte
"""
import sys
from pathlib import Path

# Agregar backend al path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from app.rag.indexer import DocumentIndexer
from app.rag.retriever import DocumentRetriever
from app.llm.client import OllamaClient
from dotenv import load_dotenv
import os
import time

# Cargar variables de entorno
env_path = backend_path / ".env"
load_dotenv(env_path)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")

print("="*80)
print("🧪 TEST RÁPIDO DE MEJORAS - BOT HOSPITALARIO")
print("="*80)
print(f"🔍 Modelo Embeddings: {EMBEDDING_MODEL}")
print(f"🤖 Modelo LLM: qwen2.5:3b")
print("="*80)

# Cargar RAG
print("\n📚 Cargando sistema RAG...")
indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)
index_path = backend_path / "faiss_index"
indexer.load_index(str(index_path))
retriever = DocumentRetriever(indexer, embedding_model=EMBEDDING_MODEL)
print(f"✅ Índice cargado: {len(indexer.documents)} chunks")

# Inicializar LLM
print("🤖 Inicializando LLM...")
llm_client = OllamaClient(model="qwen2.5:3b")
print("✅ LLM listo\n")

# Test cases basados en el reporte
test_cases = [
    {
        "nombre": "TEST 1: SALUDO (problema: no saludaba)",
        "pregunta": "Hola",
        "usa_rag": False,
        "esperado": "Debe saludar y preguntar en qué puede ayudar"
    },
    {
        "nombre": "TEST 2: INTERNACIÓN IOSFA (problema: respuesta incompleta)",
        "pregunta": "Requisitos internación programada IOSFA",
        "usa_rag": True,
        "obra_social": "IOSFA",
        "esperado": "Debe mencionar: DNI, credencial, orden autorizada, presupuesto, denuncia"
    },
    {
        "nombre": "TEST 3: PREGUNTA AMBIGUA (problema: no repreguntaba)",
        "pregunta": "¿Y el teléfono?",
        "usa_rag": True,
        "esperado": "Debe preguntar de qué obra social"
    }
]

resultados = []
historial = []  # Mantener historial entre preguntas para contexto conversacional

for idx, test in enumerate(test_cases, 1):
    print("\n" + "="*80)
    print(f"{test['nombre']}")
    print("="*80)
    print(f"Pregunta: \"{test['pregunta']}\"")
    print(f"Esperado: {test['esperado']}")
    print()

    # Ejecutar RAG si es necesario
    start_rag = time.time()
    if test.get('usa_rag'):
        obra_social_filter = test.get('obra_social')
        chunks = retriever.retrieve(
            query=test['pregunta'],
            top_k=3,
            obra_social_filter=obra_social_filter
        )
        context_parts = []
        for chunk_text, metadata, score in chunks:
            context_parts.append(f"[Fuente: {metadata['obra_social']}]\n{chunk_text[:500]}")
        context = "\n\n".join(context_parts)
        tiempo_rag = (time.time() - start_rag) * 1000
        print(f"⏱️  RAG: {tiempo_rag:.0f}ms")
        print(f"🔍 Top chunk: {metadata['obra_social']} - {metadata['archivo']} (similarity: {score:.3f})")
    else:
        context = "No hay información relevante."
        tiempo_rag = 0

    # Ejecutar LLM con historial
    start_llm = time.time()
    respuesta = llm_client.generate_response(
        query=test['pregunta'],
        context=context,
        obra_social=test.get('obra_social'),
        historial=historial  # Mantener contexto conversacional
    )
    tiempo_llm = (time.time() - start_llm) * 1000

    # Actualizar historial para la próxima pregunta
    historial.append({'role': 'user', 'content': test['pregunta']})
    historial.append({'role': 'assistant', 'content': respuesta})

    print(f"⏱️  LLM: {tiempo_llm:.0f}ms ({tiempo_llm/1000:.1f}s)")
    print(f"⏱️  TOTAL: {(tiempo_rag + tiempo_llm):.0f}ms")
    print()
    print(f"💬 RESPUESTA ({len(respuesta.split())} palabras):")
    print(f"   {respuesta}")
    print()

    # Evaluación simple
    palabras = respuesta.lower()
    cumple = []
    no_cumple = []

    if idx == 1:  # Saludo
        if "hola" in palabras and ("ayudarte" in palabras or "ayudar" in palabras):
            cumple.append("✅ Saluda correctamente")
        else:
            no_cumple.append("❌ No saluda como esperado")

    elif idx == 2:  # Internación IOSFA
        requisitos = ["dni", "credencial", "orden", "autorizada", "presupuesto", "denuncia"]
        encontrados = [r for r in requisitos if r in palabras]
        if len(encontrados) >= 4:
            cumple.append(f"✅ Menciona {len(encontrados)}/6 requisitos: {', '.join(encontrados)}")
        else:
            no_cumple.append(f"❌ Solo menciona {len(encontrados)}/6 requisitos: {', '.join(encontrados)}")

    elif idx == 3:  # Ambigua
        if "?" in respuesta and ("obra social" in palabras or "cuál" in palabras or "qué" in palabras):
            cumple.append("✅ Repregunta correctamente")
        else:
            no_cumple.append("❌ No repregunta ante ambigüedad")

    # Verificar brevedad (máx 50 palabras según prompt)
    num_palabras = len(respuesta.split())
    if num_palabras <= 50:
        cumple.append(f"✅ Conciso ({num_palabras} palabras)")
    else:
        no_cumple.append(f"❌ Demasiado largo ({num_palabras} palabras, esperado ≤50)")

    # Verificar que termina con pregunta
    if respuesta.strip().endswith("?"):
        cumple.append("✅ Termina con pregunta")
    else:
        no_cumple.append("❌ No termina con pregunta")

    print("📊 EVALUACIÓN:")
    for c in cumple:
        print(f"   {c}")
    for nc in no_cumple:
        print(f"   {nc}")

    resultados.append({
        "test": test['nombre'],
        "respuesta": respuesta,
        "tiempo_llm_s": tiempo_llm / 1000,
        "palabras": num_palabras,
        "cumple": cumple,
        "no_cumple": no_cumple
    })

# Resumen final
print("\n" + "="*80)
print("📊 RESUMEN COMPARATIVO CON REPORTE ORIGINAL")
print("="*80)

tiempo_llm_prom = sum(r['tiempo_llm_s'] for r in resultados) / len(resultados)
palabras_prom = sum(r['palabras'] for r in resultados) / len(resultados)

print(f"\n⏱️  TIEMPOS LLM:")
print(f"   Reporte original: 1.8s promedio (rango: 9-26s con errores)")
print(f"   Con mejoras: {tiempo_llm_prom:.1f}s promedio")
print()

print(f"✂️  CONCISIÓN:")
print(f"   Reporte original: 14.5% (objetivo: ≥70%)")
print(f"   Con mejoras: {palabras_prom:.1f} palabras promedio (objetivo: ≤40)")
print()

print(f"💬 HABILIDADES CONVERSACIONALES:")
print(f"   Reporte original: 0.0% (no saludaba, no repreguntaba)")

total_cumplimientos = sum(len(r['cumple']) for r in resultados)
total_checks = total_cumplimientos + sum(len(r['no_cumple']) for r in resultados)
porcentaje = (total_cumplimientos / total_checks) * 100 if total_checks > 0 else 0

print(f"   Con mejoras: {porcentaje:.1f}% ({total_cumplimientos}/{total_checks} checks)")
print()

if porcentaje > 50:
    print("🎯 RESULTADO: ✅ MEJORAS SIGNIFICATIVAS")
else:
    print("🎯 RESULTADO: ⚠️  NECESITA MÁS AJUSTES")

print("\n" + "="*80)
