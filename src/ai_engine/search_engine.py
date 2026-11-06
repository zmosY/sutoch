"""
AI RAG Search Engine implementing the 4-step pipeline from the architecture diagram:
  Шаг 1: Векторизация базы (title + description -> Embedding Model -> 1536d vector -> property_embeddings)
  Шаг 2: Векторизация запроса (user query -> Embedding Model -> 1536d vector)
  Шаг 3: Семантический поиск (Cosine Similarity -> Top-3 / Top-5 context properties)
  Шаг 4: Генерация ответа (Context + User Query -> LLM Model -> natural text response)
"""

import os
import re
import json
import math
import hashlib
from typing import List, Dict, Any, Tuple, Optional

# Optional OpenAI integration if OPENAI_API_KEY is configured
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EmbeddingModel:
    """
    Embedding Model (1536 измерений) - Шаг 1 и Шаг 2 архитектурной схемы.
    Преобразует текстовые данные в 1536-мерные числовые векторы.
    
    При наличии переменной OPENAI_API_KEY использует OpenAI text-embedding-3-small (1536d).
    При отсутствии ключа использует локальный детерминированный семантический проектор (1536d)
    на основе Random Projection (сохраняет косинусное сходство по лемме Джонсона-Линденштраусса),
    что позволяет запускать код автономно без платных API.
    """
    DIMENSION = 1536

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
        """Генерирует 1536-мерный нормализованный вектор для входного текста."""
        clean_text = text.strip()
        if not clean_text:
            return [0.0] * self.DIMENSION

        # Если доступен официальный OpenAI API
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=clean_text
                )
                return response.data[0].embedding
            except Exception as e:
                # Мягкий откат на локальный 1536d проектор при сбое сети
                pass

        # Автономный 1536d семантический проектор
        return self._local_semantic_embedding(clean_text)

    def _local_semantic_embedding(self, text: str) -> List[float]:
        """
        Локальный алгоритм Random Projection в 1536 измерений.
        Разбивает текст на слова и биграммы, проецирует в 1536d пространство
        и нормализует длину вектора до 1.0 (L2-норма).
        """
        words = re.findall(r'\b[a-zA-Zа-яА-Я0-9ёЁ]{2,}\b', text.lower())
        vector = [0.0] * self.DIMENSION
        if not words:
            return vector

        # Токены: отдельные слова и биграммы для учета контекста
        tokens = list(words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")

        for token in tokens:
            # Детерминированный хеш токена
            hash_bytes = hashlib.sha256(token.encode('utf-8')).digest()
            # Проекция токена на несколько базисных осей из 1536
            for step in range(8):
                idx = int.from_bytes(hash_bytes[step*4 : (step+1)*4], 'little') % self.DIMENSION
                sign = 1.0 if (hash_bytes[step] % 2 == 0) else -1.0
                vector[idx] += sign

        # L2-нормализация: длина вектора равна 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector


class LLMModel:
    """
    LLM (Языковая модель) - Шаг 4 архитектурной схемы.
    Принимает извлеченный контекст (Топ квартир из векторного поиска) + Запрос пользователя
    и генерирует естественный, аргументированный ответ с рекомендациями.
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
        """Шаг 4: Формирование связного текста рекомендаций на основе контекста."""
        if not context_properties:
            return (
                "К сожалению, по вашему запросу не удалось найти подходящих объектов. "
                "Попробуйте изменить параметры (например, указать другой город или расширить бюджет)."
            )

        # Если доступен официальный OpenAI API
        if self.client:
            try:
                prompt_context = "\n\n".join([
                    f"Объект #{p['id']}: {p['title']}\n"
                    f"Тип: {p['type']}, Адрес: {p['address']}, Цена: {p['price_per_night']} руб/сутки, До гостей: {p['max_guests']}\n"
                    f"Описание: {p['description']}\n"
                    f"Сходство с запросом: {p.get('similarity', 0.0):.2f}\n"
                    f"Отзывы гостей: {p.get('reviews_summary', 'Положительные оценки')}"
                    for p in context_properties
                ])

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Ты — интеллектуальный ассистент сервиса посуточной аренды (аналог Booking и Суточно.ру). "
                            "Твоя задача — проанализировать предоставленный список найденных объектов и ответить на запрос "
                            "пользователя живым, вежливым языком. Объясни, почему каждый вариант подходит, укажи цены, "
                            "локацию и честно подсвети ключевые плюсы и нюансы."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Запрос пользователя: \"{query}\"\n\nНайденные варианты (Контекст):\n{prompt_context}"
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

        # Автономный генератор естественного ответа (без внешних зависимостей)
        return self._format_local_response(query, context_properties)

    def _format_local_response(self, query: str, properties: List[Dict[str, Any]]) -> str:
        best = properties[0]
        text_parts = [
            f"Я проанализировал ваш запрос «{query}» и подобрал лучшие варианты через векторный поиск:\n"
        ]

        # Главная рекомендация
        text_parts.append(
            f"🌟 **Лучший выбор:** [{best['title']}](/property/{best['id']})\n"
            f"• **Адрес:** {best['address']}\n"
            f"• **Цена:** {int(best['price_per_night']):,} руб./сутки (до {best['max_guests']} гостей)\n"
            f"• **Почему подходит:** {best['description'][:140]}...\n"
            f"• **Оценка сходства:** {int(best.get('similarity', 0.85) * 100)}% совпадения с вашими пожеланиями."
        )

        # Альтернативы
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
    Основной поисковый конвейер RAG, связывающий:
    [Пользователь / Браузер] -> [Backend API] -> Embedding Model -> Property Embeddings -> LLM Model
    """
    def __init__(self, db_conn_factory):
        self.get_conn = db_conn_factory
        self.embedding_model = EmbeddingModel()
        self.llm_model = LLMModel()

    # ----------------------------------------------------------------
    # ШАГ 1: Векторизация базы
    # ----------------------------------------------------------------
    def vectorize_and_store_property(self, property_id: int, title: str, description: str):
        """
        Шаг 1:
        Вход: Текст: title + description (из таблицы properties)
        Компонент: Embedding Model (преобразование в 1536-мерный вектор)
        Выход: Вектор числовых значений (1536d)
        Хранение: Запись в Векторную БД (property_embeddings)
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

    # ----------------------------------------------------------------
    # ШАГ 2: Векторизация запроса
    # ----------------------------------------------------------------
    def vectorize_query(self, query_text: str) -> List[float]:
        """
        Шаг 2:
        Вход: Текстовый поисковый запрос пользователя ("квартира у парка")
        Компонент: Embedding Model (обработка той же моделью, что и на Шаге 1)
        Выход: Вектор запроса (1536d)
        """
        return self.embedding_model.get_embedding(query_text)

    # ----------------------------------------------------------------
    # ШАГ 3: Семантический поиск (Расчет Косинусного сходства)
    # ----------------------------------------------------------------
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Расчет косинусного сходства (Cosine Similarity):
        cos(θ) = (v1 · v2) / (||v1|| * ||v2||)
        Для нормализованных векторов равен их скалярному произведению.
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
        Шаг 3:
        Вход: Вектор запроса пользователя
        Компонент: Расчет косинусного сходства между запросом и базой property_embeddings
        Выход: ID и данные наиболее похожих объектов (Топ-3 или Топ-5)
        Хранение: Извлеченный текстовый Контекст для нейросети
        """
        query_vector = self.vectorize_query(query)

        conn = self.get_conn()
        cursor = conn.cursor()

        # Извлекаем все свойства с их эмбеддингами
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

        scored_properties = []
        for row in rows:
            # Жесткие фильтры (если заданы)
            if max_price and row["price_per_night"] > max_price:
                continue
            if min_guests and row["max_guests"] < min_guests:
                continue
            if city_hint and city_hint.lower() not in row["address"].lower() and city_hint.lower() not in row["description"].lower():
                continue

            # Расчет сходства между вектором запроса и вектором объекта
            try:
                emb = json.loads(row["embedding"])
                similarity = self.cosine_similarity(query_vector, emb)
            except Exception:
                similarity = 0.0

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

        # Сортировка по косинусному сходству (от самых релевантных к менее)
        scored_properties.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_properties[:top_k]

    # ----------------------------------------------------------------
    # ШАГ 4: Генерация ответа (LLM)
    # ----------------------------------------------------------------
    def generate_chat_response(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Полный RAG-цикл (Шаги 2 -> 3 -> 4):
        1. Векторизует запрос
        2. Ищет Топ-K квартир в базе по косинусному сходству
        3. Передает контекст в LLM
        4. Возвращает ответ пользователю и карточки объектов
        """
        # Шаг 2 и 3: Извлечение контекста
        context_properties = self.semantic_search(user_query, top_k=top_k)

        # Шаг 4: Генерация ответа через языковую модель
        llm_reply = self.llm_model.generate_response(user_query, context_properties)

        return {
            "query": user_query,
            "reply": llm_reply,
            "results": context_properties,
            "count": len(context_properties)
        }
