"""
Interactive Demo for AI RAG Travel Search
Demonstrates the 4-step pipeline:
  Шаг 2: Векторизация запроса (Embedding Model 1536d)
  Шаг 3: Семантический поиск (Cosine Similarity)
  Шаг 4: Генерация ответа через языковую модель (LLM)
"""

import os
import sys
import time

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
        t_start = time.perf_counter()

        print("=" * 80)
        print(f"ТЕСТОВЫЙ ЗАПРОС #{idx}: \"{query}\"")
        print("=" * 80)

        # Шаг 2: Векторизация запроса
        t_v0 = time.perf_counter()
        q_vec = engine.vectorize_query(query)
        t_v1 = time.perf_counter()
        print(f"[Шаг 2 - Векторизация запроса]: Вектор {len(q_vec)}d сформирован за {((t_v1-t_v0)*1000):.2f} мс")
        print(f"                               Первые координаты: {[round(x, 4) for x in q_vec[:5]]}...")

        # Шаг 3: Семантический поиск по косинусному сходству
        t_s0 = time.perf_counter()
        results = engine.semantic_search(query, top_k=3)
        t_s1 = time.perf_counter()
        print(f"\n[Шаг 3 - Поиск по Cosine Similarity]: Найдено Топ-{len(results)} за {((t_s1-t_s0)*1000):.2f} мс:")
        for rank, p in enumerate(results, 1):
            sim_pct = round(p['similarity'] * 100, 1)
            print(f"  {rank}. [{sim_pct}% совпадения] {p['title']}")
            print(f"     Адрес: {p['address']} | Цена: {int(p['price_per_night'])} руб/сутки")

        # Шаг 4: Генерация связного ответа через LLM
        t_g0 = time.perf_counter()
        llm_reply = engine.llm_model.generate_response(query, results)
        t_g1 = time.perf_counter()

        t_total = time.perf_counter() - t_start
        print(f"\n[Шаг 4 - Генерация ответа LLM]: (сформирован за {((t_g1-t_g0)*1000):.2f} мс)")
        print(llm_reply)
        print("-" * 80)
        print(f"⚡ СКОРОСТЬ ОБРАБОТКИ НА ВАШЕМ ПК: {(t_total*1000):.2f} мс (всего {t_total:.4f} секунды!)")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    run_test_cases()
