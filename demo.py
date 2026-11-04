"""
Interactive Demo for AI Travel Search with Aspect Analysis
Runs typical natural language requests and outputs AI reasoning based on review complaints/praises.
"""

import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from src.ai_engine.search_engine import AISearchEngine

def run_test_cases():
    engine = AISearchEngine()

    test_queries = [
        "Хочу в Сочи на двоих смотреть на море с балкона, только чтобы не было шумно от баров и нормальный вай-фай для работы",
        "Ищу квартиру в Питере для удаленной работы, чтобы была тишина и быстрый интернет, без пьяных криков под окнами",
        "Хочу отдых на Балтийском море у первой линии, чтобы слышать прибой",
    ]

    for idx, query in enumerate(test_queries, 1):
        print("=" * 80)
        print(f"ТЕСТОВЫЙ ЗАПРОС #{idx}: \"{query}\"")
        print("=" * 80)

        res = engine.search(query)
        intent = res["parsed_intent"]
        print(f"[Распознанный интент ИИ]: Город={intent['city']}, Гостей={intent['guests']}, Нужные аспекты={intent['must_have_aspects']}, Избегать жалоб={intent['avoid_aspects']}")
        print(f"\n[Найдено кандидатов: {res['total_candidates']}]\n")

        for rank, item in enumerate(res["results"], 1):
            if rank == 1 and item["ai_score"] > 80:
                flag = "[ РЕКОМЕНДАЦИЯ ИИ ]"
            elif item["warnings"]:
                flag = "[ ВНИМАНИЕ: ЕСТЬ ЖАЛОБЫ В ОТЗЫВАХ ]"
            else:
                flag = "[ АЛЬТЕРНАТИВНЫЙ ВАРИАНТ ]"

            print(f"{rank}. {flag} {item['title']}")
            print(f"   Город: {item['city']} | Цена: {item['price']:.0f} руб/ночь | Рейтинг: {item['rating']} ({item['reviews_count']} отзывов) | AI Match Score: {item['ai_score']}")
            
            if item["reasons"]:
                print(f"   [+] Почему подходит:")
                for r in item["reasons"]:
                    print(f"       * {r}")
            
            if item["warnings"]:
                print(f"   [-] На что жалуются гости в отзывах:")
                for w in item["warnings"]:
                    print(f"       * {w}")
            
            print()

if __name__ == "__main__":
    run_test_cases()
