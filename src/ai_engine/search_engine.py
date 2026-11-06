"""
====================================================================
ДВИЖОК ИИ-ПОИСКА RAG (ФАЙЛ: src/ai_engine/search_engine.py)
====================================================================
Этот модуль реализует 4-шаговый пайплайн RAG (Retrieval-Augmented Generation),
описанный в таблице на архитектурной схеме проекта:

  Шаг 1: Векторизация базы
         Вход: Текст title + description из таблицы properties
         Компонент: Embedding Model (размерность 1536d)
         Результат: Запись в векторную таблицу property_embeddings

  Шаг 2: Векторизация запроса
         Вход: Поисковый запрос пользователя на естественном языке
         Компонент: Та же Embedding Model (1536d)
         Результат: Вектор запроса

  Шаг 3: Семантический поиск
         Вход: Вектор запроса
         Компонент: Расчет косинусного сходства (Cosine Similarity)
         Результат: Извлечение Топ-3 / Топ-5 наиболее похожих объектов (Контекст)

  Шаг 4: Генерация ответа
         Вход: Контекст найденных квартир + Текст запроса
         Компонент: LLM (Языковая модель)
         Результат: Финализированный естественный ответ с аргументами и ссылками
====================================================================
"""

import os
import re
import json
import math
import hashlib
from typing import List, Dict, Any, Tuple, Optional

# Проверяем наличие ключа OpenAI в переменных окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EmbeddingModel:
    """
    Embedding Model (1536 измерений) — Шаги 1 и 2 схемы.
    
    Что такое эмбеддинг (Embedding)?
    Это математический перевод текста на «язык чисел». Текст превращается в список
    из 1536 чисел с плавающей точкой. В этом 1536-мерном пространстве слова и фразы
    с похожим смыслом («у моря», «на первой линии пляжа», «вид на волны»)
    оказываются геометрически близко друг к другу.
    
    Гибридный режим работы:
    1. Если в системе задан OPENAI_API_KEY -> вызывает модель text-embedding-3-small (1536d).
    2. Если ключа нет -> автоматически запускает локальный детерминированный проектор (1536d),
       что позволяет проекту работать полностью оффлайн без платных подписок.
    """
    DIMENSION = 1536  # Стандартная размерность эмбеддингов OpenAI

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None

    def get_embedding(self, text: str) -> List[float]:
        """
        Преобразует входную строку текста в нормализованный вектор из 1536 чисел.
        """
        clean_text = text.strip()
        if not clean_text:
            return [0.0] * self.DIMENSION

        # Вариант А: Официальный OpenAI API (если доступен)
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=clean_text
                )
                return response.data[0].embedding
            except Exception:
                pass  # При сбое сети или ошибке квоты переходим на локальный проектор

        # Вариант Б: Локальный автономный 1536d проектор
        return self._local_semantic_embedding(clean_text)

    def _local_semantic_embedding(self, text: str) -> List[float]:
        """
        Локальный алгоритм проекции в 1536-мерное пространство (Subword Random Projection).
        
        Как это работает:
        1. Текст очищается от знаков препинания и приводится к нижнему регистру.
        2. Извлекаются отдельные слова и соседние пары слов (биграммы) для учета контекста.
        3. Для учета русской морфологии ("море", "моря", "морской") извлекаются
           символьные 3-граммы и 4-граммы (как в FastText / BPE токенизаторах).
        4. Каждый токен через SHA-256 хешируется и проецируется на фиксированные координаты.
        5. Производится L2-нормализация (длина вектора = 1.0) для быстрого расчета Cosine Similarity.
        """
        words = re.findall(r'\b[a-zA-Zа-яА-Я0-9ёЁ]{2,}\b', text.lower())
        vector = [0.0] * self.DIMENSION
        if not words:
            return vector

        tokens = list(words)
        # Биграммы слов для учета словосочетаний ("вид_на", "на_море")
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")

        # Символьные n-граммы (3-граммы и 4-граммы) для учета морфологии и падежей
        for w in words:
            padded = f"<{w}>"
            for n in (3, 4):
                if len(padded) >= n:
                    for i in range(len(padded) - n + 1):
                        tokens.append(padded[i:i+n])

        for token in tokens:
            hash_bytes = hashlib.sha256(token.encode('utf-8')).digest()
            # Проецируем токен на 4 базисные оси из 1536
            for step in range(4):
                idx = int.from_bytes(hash_bytes[step*4 : (step+1)*4], 'little') % self.DIMENSION
                sign = 1.0 if (hash_bytes[step] % 2 == 0) else -1.0
                vector[idx] += sign

        # L2-нормализация: длина вектора sqrt(x1^2 + x2^2 + ... + x1536^2) = 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector


class LLMModel:
    """
    LLM (Языковая модель) — Шаг 4 схемы.
    
    Получает:
    1. Запрос пользователя («хочу квартиру в Сочи у моря для двоих»).
    2. Извлеченный контекст (Топ-3 / Топ-5 объектов, найденных на Шаге 3 через Косинусное сходство).
    
    Задача:
    Сформулировать связный, грамотный и живой человеческий ответ с объяснением,
    почему именно эти варианты подходят под пожелания гостя.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None

    def generate_response(self, query: str, context_properties: List[Dict[str, Any]]) -> str:
        """
        Шаг 4 RAG: Формирование рекомендаций через LLM на основе контекста.
        """
        if not context_properties:
            return (
                "К сожалению, по вашему запросу не удалось найти подходящих свободных объектов. "
                "Попробуйте скорректировать параметры поиска (например, указать другой город или бюджет)."
            )

        # Вариант А: Реальный вызов OpenAI gpt-4o-mini
        if self.client:
            try:
                prompt_context = "\n\n".join([
                    f"Объект #{p['id']}: {p['title']}\n"
                    f"Тип: {p['type']}, Адрес: {p['address']}, Цена: {p['price_per_night']} руб/сутки, До гостей: {p['max_guests']}\n"
                    f"Описание: {p['description']}\n"
                    f"Сходство с запросом: {p.get('similarity', 0.0):.2f}\n"
                    f"Оценка гостей: {p.get('rating', 9.5)}/10"
                    for p in context_properties
                ])

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Ты — профессиональный ИИ-консьерж сервиса посуточной аренды (аналог Booking.com и Суточно.ру). "
                            "Твоя задача — ответить на запрос пользователя вежливо, четко и структурированно, опираясь "
                            "исключительно на переданные объекты в контексте. Объясни преимущества каждого варианта."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Запрос пользователя: \"{query}\"\n\nКонтекст найденных квартир:\n{prompt_context}"
                    }
                ]

                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7
                )
                return completion.choices[0].message.content
            except Exception:
                pass

        # Вариант Б: Локальный автономный генератор структурированного ответа
        return self._format_local_response(query, context_properties)

    def _format_local_response(self, query: str, properties: List[Dict[str, Any]]) -> str:
        best = properties[0]
        text_parts = [
            f"Я проанализировал ваш запрос «{query}» и подобрал лучшие варианты через векторный поиск:\n"
        ]

        # Главный рекомендованный вариант
        text_parts.append(
            f"🌟 **Лучший выбор:** [{best['title']}](/property/{best['id']})\n"
            f"• **Адрес:** {best['address']}\n"
            f"• **Цена:** {int(best['price_per_night']):,} руб./сутки (до {best['max_guests']} гостей)\n"
            f"• **Почему подходит:** {best['description'][:140]}...\n"
            f"• **Оценка сходства:** {int(best.get('similarity', 0.85) * 100)}% совпадения с вашими пожеланиями."
        )

        # Дополнительные альтернативные варианты
        if len(properties) > 1:
            text_parts.append("\n**Другие отличные альтернативы:**")
            for p in properties[1:4]:
                text_parts.append(
                    f"• **[{p['title']}](/property/{p['id']})** — {int(p['price_per_night']):,} руб./сутки, "
                    f"{p['address']} (совпадение {int(p.get('similarity', 0.75) * 100)}%)"
                )

        text_parts.append("\nВы можете нажать на любой объект, чтобы посмотреть фотографии и отзывы гостей!")
        return "\n".join(text_parts)


class RAGSearchEngine:
    """
    Главный оркестратор конвейера поиска RAG.
    Связывает базу данных, модель эмбеддингов, косинусное ранжирование и генерацию ответа.
    """
    def __init__(self, db_conn_factory):
        self.get_conn = db_conn_factory
        self.embedding_model = EmbeddingModel()
        self.llm_model = LLMModel()

    # ================================================================
    # ШАГ 1: Векторизация базы
    # ================================================================
    def vectorize_and_store_property(self, property_id: int, title: str, description: str):
        """
        Шаг 1 из таблицы:
        • Входные данные: Текст: title + description (из таблицы properties).
        • Процесс: Embedding Model преобразует текст в математические координаты 1536d.
        • Выход: Вектор числовых значений (1536d).
        • Хранение: Запись в векторную БД (таблица property_embeddings).
        """
        combined_text = f"{title} {description}".strip()
        vector = self.embedding_model.get_embedding(combined_text)
        vector_json = json.dumps(vector)

        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO property_embeddings (property_id, embedding, document_text, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (property_id, vector_json, combined_text))
        conn.commit()
        conn.close()

    # ================================================================
    # ШАГ 2: Векторизация запроса
    # ================================================================
    def vectorize_query(self, query_text: str) -> List[float]:
        """
        Шаг 2 из таблицы:
        • Входные данные: Текстовый поисковый запрос пользователя ("квартира у парка").
        • Процесс: Embedding Model обрабатывает запрос ТОЙ ЖЕ моделью, что и на Шаге 1.
        • Выход: Вектор запроса (1536d).
        • Результат: Передача вектора в блок математического сравнения.
        """
        return self.embedding_model.get_embedding(query_text)

    # ================================================================
    # ШАГ 3: Семантический поиск (Расчет Косинусного Сходства)
    # ================================================================
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Математический расчет косинусного сходства (Cosine Similarity):
        
                 v1 · v2
        cos(θ) = -----------------
                 ||v1|| * ||v2||
        
        • Значение 1.0 означает абсолютно одинаковое семантическое направление.
        • Значение 0.0 означает независимые темы.
        • Поскольку наши векторы заранее нормализованы к длине 1.0, знаменатель
          всегда равен 1.0, и формула сводится к быстрому скалярному произведению (dot product):
          dot_product = sum(v1[i] * v2[i])
        """
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        return max(-1.0, min(1.0, dot_product))

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        max_price: Optional[float] = None,
        min_guests: Optional[int] = None,
        city_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Шаг 3 из таблицы:
        • Входные данные: Вектор запроса пользователя (из Шага 2).
        • Процесс: Расчет косинусного сходства между вектором запроса и каждым
          вектором в таблице property_embeddings.
        • Выход: ID и данные наиболее похожих объектов (Топ-3 или Топ-5).
        • Результат: Извлеченный текстовый контекст для нейросети (Шаг 4).
        """
        query_vector = self.vectorize_query(query)

        conn = self.get_conn()
        cursor = conn.cursor()

        # Извлекаем все доступные объекты и их сохраненные эмбеддинги
        cursor.execute("""
            SELECT 
                p.id, p.host_id, p.title, p.description, p.type,
                p.price_per_night, p.latitude, p.longitude, p.address,
                p.max_guests, p.is_available,
                pe.embedding
            FROM properties p
            JOIN property_embeddings pe ON p.id = pe.property_id
            WHERE p.is_available = 1
        """)
        rows = cursor.fetchall()

        # Ключевые смысловые корни слов запроса для учета русской морфологии (падежи и окончания)
        query_stems = [
            re.sub(r'(ый|ий|ой|ая|яя|ое|ее|ые|ие|ого|его|ому|ему|ых|их|ую|юю|ом|ем|а|я|у|ю|е|о|ы|и)$', '', w.lower())
            for w in re.findall(r'\b[a-zA-Zа-яА-Я0-9ёЁ]{3,}\b', query)
        ]
        query_stems = [s if len(s) >= 3 else s[:3] for s in query_stems if len(s) >= 3]

        scored_properties = []
        for row in rows:
            # Опциональные жесткие фильтры (цена, вместимость, город)
            if max_price and row["price_per_night"] > max_price:
                continue
            if min_guests and row["max_guests"] < min_guests:
                continue
            if city_hint and city_hint.lower() not in row["address"].lower() and city_hint.lower() not in row["description"].lower():
                continue

            # Расчет косинусного сходства между вектором запроса и вектором объекта
            try:
                emb = json.loads(row["embedding"])
                similarity = self.cosine_similarity(query_vector, emb)
            except Exception:
                similarity = 0.0

            # Гибридный учет (Hybrid RAG): проверяем наличие корней запроса в тексте объекта
            doc_text = f"{row['title']} {row['description']} {row['address']}".lower()
            stem_hits = sum(1 for s in query_stems if s in doc_text)
            if stem_hits > 0:
                similarity += 0.12 * stem_hits
            else:
                # Если ни один смысловой корень короткого точного запроса не найден,
                # объект штрафуется и не попадает в топ рекомендаций
                if len(query_stems) <= 2:
                    similarity -= 0.15

            prop_dict = {
                "id": row["id"],
                "host_id": row["host_id"],
                "title": row["title"],
                "description": row["description"],
                "type": row["type"],
                "price_per_night": row["price_per_night"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "address": row["address"],
                "max_guests": row["max_guests"],
                "similarity": similarity
            }
            scored_properties.append(prop_dict)

        conn.close()

        # Сортировка по убыванию косинусного сходства (самые релевантные идут первыми)
        scored_properties.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_properties[:top_k]

    # ================================================================
    # ШАГ 4: Генерация ответа через LLM
    # ================================================================
    def generate_chat_response(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Полный цикл RAG:
        1. Векторизует запрос пользователя (Шаг 2).
        2. Ищет Топ-K подходящих объектов через Cosine Similarity (Шаг 3).
        3. Передает найденный контекст в языковую модель (Шаг 4).
        4. Возвращает готовый ответ и карточки вариантов на экран пользователя.
        """
        # Шаги 2 и 3: Извлечение контекста
        context_properties = self.semantic_search(user_query, top_k=top_k)

        # Шаг 4: Генерация связного ответа языковой моделью
        llm_reply = self.llm_model.generate_response(user_query, context_properties)

        return {
            "query": user_query,
            "reply": llm_reply,
            "results": context_properties,
            "count": len(context_properties)
        }
