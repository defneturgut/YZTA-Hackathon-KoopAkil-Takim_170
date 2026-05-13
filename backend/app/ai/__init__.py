"""Aegis-KOBI AI layer.

Contains the Gemini service abstraction, RAG pipeline, multi-tool
operations agent, and the prompt library. Designed so the *real*
Gemini integration can be enabled by flipping ``AI_DEMO_MODE=false``
and providing ``GEMINI_API_KEY`` — nothing else changes.
"""
