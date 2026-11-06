"""
Interactive Demo for AI RAG Travel Search
Demonstrates the 4-step pipeline:
  Шаг 2: Векторизация запроса (Embedding Model 1536d)
  Шаг 3: Семантический поиск (Cosine Similarity)
  Шаг 4: Генерация ответа через языковую модель (LLM)
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.ai_engine.search_engine import RAGSearchEngine
from src.db.schema_sqlite import get_connection

def run_test_cases():
    engine = RAGSearchEngine(get_connection)

    test_queries = [
        "Панорамная квартира в Сочи у моря с красивым видом на закат",
        "Тихая дизайнерская студия у Невского проспекта для работы",
        "Уединенный деревянный дом шале в лесу с баней и камином"
    ]

    for idx, query in enumerate(test_queries, 1):
        print("=" * 80)
        print(f"ТЕСТОВЫЙ ЗАПРОС #{idx}: \"{query}\"")
        print("=" * 80)

        # Шаг 2: Векторизация запроса
        q_vec = engine.vectorize_query(query)
        print(f"[Шаг 2 - Векторизация запроса]: Вектор размерности {len(q_vec)}d сформирован")
        print(f"                               Первые координаты: {[round(x, 4) for x in q_vec[:5]]}...")

        # Шаг 3: Семантический поиск по косинусному сходству
        results = engine.semantic_search(query, top_k=3)
        print(f"\n[Шаг 3 - Семантический поиск по Cosine Similarity]: Найдено Топ-{len(results)} объектов:")
        for rank, p in enumerate(results, 1):
            sim_pct = round(p['similarity'] * 100, 1)
            print(f"  {rank}. [{sim_pct}% совпадения] {p['title']}")
            print(f"     Адрес: {p['address']} | Цена: {int(p['price_per_night'])} руб/сутки")

        # Шаг 4: Генерация связного ответа через LLM
        print("\n[Шаг 4 - Генерация ответа LLM]:")
        llm_reply = engine.llm_model.generate_response(query, results)
        print(llm_reply)
        print("\n")

if __name__ == "__main__":
    run_test_cases()
