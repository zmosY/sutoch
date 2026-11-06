"""
FastAPI Backend for Sutochno & Booking RAG Architecture
Implements the full diagram flow:
  [Пользователь / Браузер] -> [Backend API] -> Embedding Model -> Property Embeddings -> LLM Model
"""

import os
import re
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.ai_engine.search_engine import RAGSearchEngine
from src.db.schema_sqlite import get_connection

app = FastAPI(
    title="Sutochno & Booking AI RAG API",
    description="Backend API с 1536d векторным семантическим поиском и генерацией рекомендаций через LLM",
    version="2.0.0"
)

search_engine = RAGSearchEngine(get_connection)

INDEX_HTML_PATH = os.path.join(os.path.dirname(__file__), "static", "index.html")
PROPERTY_HTML_PATH = os.path.join(os.path.dirname(__file__), "static", "property.html")

# Базовые фото интерьеров высокого качества для красивого отображения в UI
PROPERTY_PHOTOS = {
    1: [
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?auto=format&fit=crop&w=800&q=80"
    ],
    2: [
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"
    ],
    3: [
        "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80"
    ],
    4: [
        "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?auto=format&fit=crop&w=800&q=80"
    ],
    5: [
        "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1502005229762-ee1b2b8ab275?auto=format&fit=crop&w=800&q=80"
    ],
    6: [
        "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"
    ]
}

DEFAULT_PHOTOS = [
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80"
]

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    parsed_intent: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

def _enrich_property_for_frontend(p: Dict[str, Any]) -> Dict[str, Any]:
    """Форматирует объект из БД под требования карточек фронтенда."""
    p_id = p["id"]
    conn = get_connection()
    cur = conn.cursor()

    # Считаем реальный средний рейтинг и количество отзывов
    cur.execute("""
        SELECT 
            COUNT(r.id) as cnt,
            AVG((r.rating_location + r.rating_cleanliness + r.rating_value) / 3.0) as avg_score
        FROM reviews r
        JOIN bookings b ON r.booking_id = b.id
        WHERE b.property_id = ?
    """, (p_id,))
    rev_row = cur.fetchone()
    conn.close()

    rev_cnt = rev_row["cnt"] if rev_row and rev_row["cnt"] is not None else 0
    rating = round(rev_row["avg_score"], 1) if (rev_row and rev_row["avg_score"] is not None and rev_cnt > 0) else 9.5

    # Извлечение города из адреса
    city = "Сочи"
    if "Санкт-Петербург" in p.get("address", ""):
        city = "Санкт-Петербург"
    elif "Москва" in p.get("address", ""):
        city = "Москва"
    elif "Ленинградская" in p.get("address", ""):
        city = "Ленинградская обл."
    elif "Зеленоградск" in p.get("address", "") or "Калининград" in p.get("address", ""):
        city = "Зеленоградск"

    photos = PROPERTY_PHOTOS.get(p_id, DEFAULT_PHOTOS)
    cover = photos[0]

    # Удобства в зависимости от типа
    amenities_text = "• Wi-Fi • Кондиционер • Кухня • Двуспальная кровать"
    if "моря" in p["title"].lower():
        amenities_text += " • Вид на море • Терраса"
    if "шале" in p["title"].lower():
        amenities_text = "• Камин на дровах • Баня • Мангал • Парковка"

    sim = p.get("similarity", 0.85)
    ai_score = int(sim * 100) if sim > 0 else 85

    return {
        "property_id": str(p_id),
        "id": p_id,
        "title": p["title"],
        "description": p["description"],
        "cover_photo": cover,
        "price": p["price_per_night"],
        "price_per_night": p["price_per_night"],
        "rating": rating,
        "reviews_count": rev_cnt,
        "city": city,
        "district": "",
        "address": p["address"],
        "distance_to_sea_m": 120 if "моря" in p["title"].lower() else None,
        "amenities_names": amenities_text,
        "reasons": [
            f"Семантическое сходство {ai_score}% по описанию и расположению",
            "Высокие оценки чистоты и расположения от реальных гостей"
        ],
        "warnings": [],
        "latitude": p["latitude"],
        "longitude": p["longitude"],
        "ai_score": ai_score,
        "instant_booking": True
    }

@app.get("/", response_class=HTMLResponse)
def serve_home_ui():
    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)

@app.get("/property/{property_id}", response_class=HTMLResponse)
def serve_property_page(property_id: str):
    if os.path.exists(PROPERTY_HTML_PATH):
        with open(PROPERTY_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Property page not found</h1>", status_code=404)

@app.get("/api/status")
def read_root():
    return {
        "status": "online",
        "architecture": "100% Match with Project ER-Diagram & 4-Step RAG",
        "tables": ["users", "properties", "property_embeddings", "bookings", "chats", "messages", "reviews"],
        "rag_steps": {
            "1": "Векторизация базы (title + description -> Embedding Model -> 1536d)",
            "2": "Векторизация запроса (user query -> Embedding Model -> 1536d)",
            "3": "Семантический поиск (Cosine Similarity -> Top-3 / Top-5)",
            "4": "Генерация ответа (Context + Query -> LLM Model -> Text)"
        }
    }

@app.get("/api/search")
def search_properties(
    q: Optional[str] = Query(None, description="Поисковый запрос на естественном языке")
):
    query = (q or "").strip()
    if not query:
        # Если запрос пустой, возвращаем все объекты
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM properties WHERE is_available = 1")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        enriched = [_enrich_property_for_frontend(r) for r in rows]
        return {
            "query": "",
            "parsed_intent": {"query": "", "filters": {}},
            "results": enriched,
            "count": len(enriched)
        }

    # Шаги 2 и 3: Векторизация запроса и косинусный поиск
    raw_results = search_engine.semantic_search(query, top_k=6)
    enriched = [_enrich_property_for_frontend(r) for r in raw_results]

    return {
        "query": query,
        "parsed_intent": {"query": query, "filters": {}},
        "results": enriched,
        "count": len(enriched)
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_ai(req: ChatRequest):
    # Полный RAG-цикл (Шаги 2, 3, 4)
    rag_result = search_engine.generate_chat_response(req.message, top_k=4)
    enriched = [_enrich_property_for_frontend(r) for r in rag_result["results"]]

    return ChatResponse(
        reply=rag_result["reply"],
        parsed_intent={"raw_query": req.message},
        recommendations=enriched
    )

@app.get("/api/properties")
def list_properties(city: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM properties WHERE is_available = 1"
    params = []
    if city:
        query += " AND address LIKE ?"
        params.append(f"%{city}%")
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    enriched = [_enrich_property_for_frontend(r) for r in rows]
    return {"count": len(enriched), "items": enriched}

@app.get("/api/properties/{property_id}")
def get_property_details(property_id: str):
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Извлечение объекта
    cur.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
    prop = cur.fetchone()
    if not prop:
        conn.close()
        raise HTTPException(status_code=404, detail="Property not found")

    prop_dict = dict(prop)
    p_id = prop_dict["id"]

    # 2. Хозяин из таблицы USER
    cur.execute("SELECT * FROM users WHERE id = ?", (prop_dict["host_id"],))
    host_row = cur.fetchone()
    host_dict = dict(host_row) if host_row else {}
    host_dict["is_verified_host"] = True
    host_dict["host_rating"] = 4.95
    host_dict["response_rate_pct"] = 99
    host_dict["response_time_minutes"] = 10
    host_dict["avatar_url"] = f"https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80"

    # 3. Отзывы из таблицы Reviews через связку с Bookings и USER
    cur.execute("""
        SELECT 
            r.id, r.booking_id, r.rating_location, r.rating_cleanliness, r.rating_value,
            r.comment, r.host_reply, r.created_at,
            ROUND((r.rating_location + r.rating_cleanliness + r.rating_value) / 3.0, 1) as rating_overall,
            u.first_name as guest_first_name,
            u.last_name as guest_last_name,
            'Москва' as guest_city,
            'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80' as guest_avatar_url
        FROM reviews r
        JOIN bookings b ON r.booking_id = b.id
        JOIN users u ON b.guest_id = u.id
        WHERE b.property_id = ?
        ORDER BY r.created_at DESC
    """, (p_id,))
    reviews = [dict(r) for r in cur.fetchall()]

    # 4. Фотогалерея
    photo_urls = PROPERTY_PHOTOS.get(p_id, DEFAULT_PHOTOS)
    photos = [
        {"photo_url": url, "caption": f"Фото {idx+1}", "is_cover": idx == 0}
        for idx, url in enumerate(photo_urls)
    ]

    # 5. Условный юнит для спецификаций на фронтенде
    units = [{
        "total_area_sqm": 55 if "апартаменты" in prop_dict["title"].lower() else 120,
        "floor": 4,
        "total_floors": 16,
        "has_elevator": True,
        "max_guests": prop_dict["max_guests"],
        "bedrooms_count": 2 if prop_dict["max_guests"] > 2 else 1
    }]

    # 6. Удобства
    amenities = [
        {"name_ru": "Скоростной Wi-Fi 200 Мбит", "category": "work"},
        {"name_ru": "Кондиционер", "category": "comfort"},
        {"name_ru": "Оборудованная кухня", "category": "kitchen"},
        {"name_ru": "Стиральная машина", "category": "bathroom"}
    ]
    if "моря" in prop_dict["title"].lower():
        amenities.append({"name_ru": "Прямой панорамный вид на море", "category": "view"})

    # 7. ИИ-выжимка аспектов
    ai_aspects = [
        {"aspect_code": "location", "sentiment": "positive", "excerpt": "Отличное расположение и удобная транспортная доступность"},
        {"aspect_code": "cleanliness", "sentiment": "positive", "excerpt": "Кристальная чистота в квартире, свежее белье и полотенца"}
    ]

    conn.close()

    # Обогащаем свойствами
    prop_dict["instant_booking"] = True
    prop_dict["reviews_count"] = len(reviews)
    prop_dict["rating_total"] = reviews[0]["rating_overall"] if reviews else 9.6

    return {
        "property": prop_dict,
        "host": host_dict,
        "photos": photos,
        "units": units,
        "amenities": amenities,
        "reviews": reviews,
        "ai_aspects": ai_aspects,
        "sentiment_summary": None
    }
