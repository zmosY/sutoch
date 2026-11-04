"""
Interactive CLI Chat with Sutochno / Booking AI Assistant
Type anything in natural language to search and filter accommodations.
Type 'exit' or 'выход' to quit.
"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

from src.ai_engine.search_engine import AISearchEngine

def main():
    engine = AISearchEngine()
    print("=" * 70)
    print("[AI TRAVEL] ДОБРО ПОЖАЛОВАТЬ В УМНЫЙ ПОИСК ЖИЛЬЯ (СУТОЧНО / BOOKING AI)")
    print("   Напишите, что вы ищете (например: 'Хочу в Сочи на море с балконом,")
    print("   но чтобы не было шума от баров и быстрый интернет для удаленки')")
    print("   Для выхода введите 'выход' или 'exit'")
    print("=" * 70)

    while True:
        try:
            user_input = input("\n[Вы]: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "выход", "q"):
                print("До встречи!")
                break

            res = engine.search(user_input)
            intent = res["parsed_intent"]
            top_items = res["results"]

            print("\n[ИИ-Ассистент]:")
            if not top_items:
                print("   К сожалению, по вашим критериям ничего не найдено.")
                continue

            best = top_items[0]
            print(f"   Я проанализировал объекты и отзывы. Вот лучший вариант:\n")
            print(f"   * {best['title']}")
            print(f"     Город: {best['city']} | Цена: {best['price']:.0f} руб/ночь | Рейтинг: {best['rating']} ({best['reviews_count']} отзывов)")
            
            if best["reasons"]:
                print(f"     [+] На что обратил внимание в отзывах:")
                for r in best["reasons"]:
                    print(f"         - {r}")

            # If there was a heavily penalized alternative with noise complaints or fake view, warn user:
            warnings_found = [it for it in top_items[1:] if it["warnings"]]
            if warnings_found:
                bad = warnings_found[0]
                print(f"\n     [!] Важное предупреждение по другим вариантам:")
                print(f"         Вариант «{bad['title']}» я не рекомендую, потому что:")
                for w in bad["warnings"]:
                    print(f"         - {w}")

        except (KeyboardInterrupt, EOFError):
            print("\nВыход.")
            break

if __name__ == "__main__":
    main()
