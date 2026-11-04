"""
FastAPI Backend for Sutochno & Booking AI Clone
Exposes search, property details, reviews with aspect sentiment, and AI chat.
"""

import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.ai_engine.search_engine import AISearchEngine
from src.db.schema_sqlite import get_connection

app = FastAPI(
    title="Sutochno & Booking AI Engine API",
    description="API для умного поиска жилья с анализом отзывов и жалоб гостей",
    version="1.0.0"
)

search_engine = AISearchEngine()

INDEX_HTML_PATH = os.path.join(os.path.dirname(__file__), "static", "index.html")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    parsed_intent: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

@app.get("/", response_class=HTMLResponse)
def serve_home_ui():
    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)

@app.get("/api/status")
def read_root():
    return {
        "status": "online",
        "service": "Sutochno / Booking AI Backend",
        "endpoints": {
            "/": "Главный интерфейс поиска (Booking / Суточно дизайн + ИИ Чат)",
            "/api/search": "Семантический и аспектный поиск жилья по запросу на естественном языке",
            "/api/chat": "ИИ-диалог с подбором вариантов",
            "/api/properties": "Каталог всех объектов размещения",
            "/api/properties/{id}": "Детальная карточка с отзывами и извлеченными аспектами"
        }
    }

@app.get("/api/search")
def search_properties(
    q: Optional[str] = Query(None, description="Поисковый запрос на русском языке, например: 'хочу в Сочи на море с балконом без шума'")
):
    results = search_engine.search(q or "")
    return results

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_ai(req: ChatRequest):
    res = search_engine.search(req.message)
    intent = res["parsed_intent"]
    top_items = res["results"][:3]

    if not top_items:
        reply = f"К сожалению, по вашему запросу ничего не найдено в базе. Попробуйте изменить параметры или выбрать другой город."
    else:
        best = top_items[0]
        reply_lines = [
            f"Я проанализировал объекты и реальные отзывы гостей по вашему запросу.",
            f"\nЛучший вариант: **{best['title']}** ({best['city']}, {best['price']:.0f} ₽/ночь)."
        ]
        if best["reasons"]:
            reply_lines.append("\nПочему это лучший выбор по отзывам:")
            for r in best["reasons"]:
                reply_lines.append(f"• {r}")
        if len(top_items) > 1 and top_items[1]["warnings"]:
            other = top_items[1]
            reply_lines.append(f"\n⚠️ Обратите внимание: другой популярный вариант «{other['title']}» я не стал рекомендовать первым, так как {other['warnings'][0].lower()}")

        reply = "\n".join(reply_lines)

    return ChatResponse(
        reply=reply,
        parsed_intent=intent,
        recommendations=top_items
    )

@app.get("/api/properties")
def list_properties(city: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT p.*, u.base_price_night, u.max_guests, s.top_praised_summary, s.top_complaints_summary
        FROM properties p
        JOIN property_units u ON p.id = u.property_id
        JOIN property_sentiment_summary s ON p.id = s.property_id
    """
    params = []
    if city:
        query += " WHERE p.city = ?"
        params.append(city)
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "items": rows}

@app.get("/api/properties/{property_id}")
def get_property_details(property_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
    prop = cur.fetchone()
    if not prop:
        conn.close()
        raise HTTPException(status_code=404, detail="Property not found")

    cur.execute("SELECT * FROM property_units WHERE property_id = ?", (property_id,))
    units = [dict(u) for u in cur.fetchall()]

    cur.execute("""
        SELECT a.code, a.category, a.name_ru, a.icon_name 
        FROM amenities a
        JOIN property_amenities pa ON a.id = pa.amenity_id
        WHERE pa.property_id = ?
    """, (property_id,))
    amenities = [dict(a) for a in cur.fetchall()]

    cur.execute("SELECT * FROM reviews WHERE property_id = ?", (property_id,))
    reviews = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT aspect_code, sentiment, confidence, excerpt FROM review_aspects WHERE property_id = ?", (property_id,))
    aspects = [dict(asp) for asp in cur.fetchall()]

    cur.execute("SELECT * FROM property_sentiment_summary WHERE property_id = ?", (property_id,))
    sentiment_summary = cur.fetchone()

    conn.close()
    return {
        "property": dict(prop),
        "units": units,
        "amenities": amenities,
        "reviews": reviews,
        "ai_aspects": aspects,
        "sentiment_summary": dict(sentiment_summary) if sentiment_summary else None
    }
