"""
Interactive CLI Chat with Sutochno / Booking RAG AI Assistant
Uses the 4-step RAG pipeline to answer user questions in real-time.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.ai_engine.search_engine import RAGSearchEngine
from src.db.schema_sqlite import get_connection

def main():
    engine = RAGSearchEngine(get_connection)
    print("=" * 75)
    print("[AI TRAVEL] ИНТЕЛЛЕКТУАЛЬНЫЙ АССИСТЕНТ ПОИСКА ЖИЛЬЯ (RAG ARCHITECTURE)")
    print("  Архитектура: [Браузер] -> [API] -> [Embedding 1536d] -> [Cosine Search] -> [LLM]")
    print("  Пример запроса: 'Посоветуй квартиру у моря в Сочи' или 'дом в лесу с камином'")
    print("  Для выхода введите 'выход' или 'exit'")
    print("=" * 75)

    while True:
        try:
            user_input = input("\n[Вы]: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "выход", "q"):
                print("Всего доброго!")
                break

            response = engine.generate_chat_response(user_input, top_k=3)
            print("\n[ИИ-Ассистент]:")
            print(response["reply"])

        except (KeyboardInterrupt, EOFError):
            print("\nВыход.")
            break

if __name__ == "__main__":
    main()
