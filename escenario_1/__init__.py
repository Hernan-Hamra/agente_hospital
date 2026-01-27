"""
Escenario 1: Modo Consulta + ChromaDB + Groq Gratis
====================================================

Bot de Telegram autocontenido para consultas sobre obras sociales.
- Sin memoria conversacional (stateless)
- Entity detection determinístico
- ChromaDB RAG con filtro nativo
- Groq gratis (llama-3.3-70b-versatile)

Uso:
    python -m escenario_1.bot
    # o
    python escenario_1/bot.py
"""
__version__ = "1.0.0"
