"""
AI Search Engine for Sutochno & Booking Clone
Translates natural language travel queries into structured filters + Aspect-Based Review Analysis.
Identifies what real guests praise and what they complain about.
"""

import re
import json
from typing import Dict, Any, List
from src.db.schema_sqlite import get_connection

class AISearchEngine:
    def __init__(self):
        self.conn = get_connection()

    def parse_query_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Extracts structured intent from user's natural language prompt.
        Handles destination, guests, budget, and desired / anti-desired aspects.
        """
        prompt_lower = user_prompt.lower()
        intent = {
            "city": None,
            "guests": 2, # default
            "max_price": None,
            "must_have_aspects": [],
            "avoid_aspects": [],
            "keywords": []
        }

        # 1. City detection
        cities = {
            "сочи": "Сочи",
            "адлер": "Сочи",
            "питер": "Санкт-Петербург",
            "петербург": "Санкт-Петербург",
            "спб": "Санкт-Петербург",
            "зеленоградск": "Зеленоградск",
            "балтик": "Зеленоградск",
            "калининград": "Зеленоградск",
            "полян": "Красная Поляна",
            "казан": "Казань"
        }
        for k, v in cities.items():
            if k in prompt_lower:
                intent["city"] = v
                break

        # 2. Guests
        if "один" in prompt_lower or "одного" in prompt_lower or "соло" in prompt_lower:
            intent["guests"] = 1
        elif "двоих" in prompt_lower or "пара" in prompt_lower or "пары" in prompt_lower or "вдвоем" in prompt_lower:
            intent["guests"] = 2
        elif "семь" in prompt_lower or "троих" in prompt_lower or "дети" in prompt_lower:
            intent["guests"] = 3

        # 3. Budget (e.g. "до 7000", "до 8000 руб")
        price_match = re.search(r"до\s+(\d+[\s\d]*)\s*(?:руб|р|k)?", prompt_lower)
        if price_match:
            intent["max_price"] = float(price_match.group(1).replace(" ", ""))

        # 4. Desired Aspects (Natural language matching)
        if any(w in prompt_lower for w in ["мор", "на море", "видом на море", "пляж"]):
            intent["must_have_aspects"].append("sea_view")
        if any(w in prompt_lower for w in ["гор", "на горы"]):
            intent["must_have_aspects"].append("mountain_view")
        if any(w in prompt_lower for w in ["балкон", "террас", "лоджи"]):
            intent["must_have_aspects"].append("balcony")
        if any(w in prompt_lower for w in ["вайфай", "вай-фай", "wifi", "интернет", "удаленк", "ворккейшн", "zoom", "зум", "работ"]):
            intent["must_have_aspects"].append("wifi_speed")
        if any(w in prompt_lower for w in ["двор", "колодец", "тихий двор"]):
            intent["must_have_aspects"].append("yard_view")
        if any(w in prompt_lower for w in ["чист", "уборк"]):
            intent["must_have_aspects"].append("cleanliness")
        if any(w in prompt_lower for w in ["кроват", "матрас", "поспать"]):
            intent["must_have_aspects"].append("bed_comfort")

        # 5. Negative Aspects to avoid (Complaints filter)
        noise_patterns = [
            r"не\s+(\w+\s+)?шум",
            r"без\s+(\w+\s+)?шум",
            r"тихо",
            r"тишин",
            r"спокойн",
            r"без\s+(\w+\s+)?бар",
            r"без\s+(\w+\s+)?клуб",
            r"без\s+крик"
        ]
        if any(re.search(pat, prompt_lower) for pat in noise_patterns):
            intent["avoid_aspects"].append("noise_street")
            intent["avoid_aspects"].append("noise_neighbors")

        return intent

    def search(self, user_prompt: str = None, explicit_city: str = None, explicit_max_price: float = None, explicit_guests: int = None, required_amenities: List[str] = None) -> Dict[str, Any]:
        """
        Executes hybrid search with aspect-based review verification.
        Combines natural language prompt intent with optional explicit UI filters.
        """
        intent = self.parse_query_intent(user_prompt) if user_prompt else {
            "city": None,
            "guests": 2,
            "max_price": None,
            "must_have_aspects": [],
            "avoid_aspects": [],
            "keywords": []
        }

        # Override/merge with explicit UI filters if provided
        if explicit_city:
            intent["city"] = explicit_city
        if explicit_max_price:
            intent["max_price"] = explicit_max_price
        if explicit_guests:
            intent["guests"] = explicit_guests
        if required_amenities:
            for am in required_amenities:
                if am not in intent["must_have_aspects"]:
                    intent["must_have_aspects"].append(am)

        conn = get_connection()
        cur = conn.cursor()

        # Build SQL candidate query with photos and amenities
        query_sql = """
            SELECT 
                p.id, p.title, p.city, p.district, p.address, p.property_type,
                p.distance_to_sea_m, 
                (SELECT COUNT(*) FROM reviews WHERE property_id = p.id) as reviews_count,
                COALESCE((SELECT ROUND(AVG(rating_overall), 2) FROM reviews WHERE property_id = p.id), p.rating_total) as rating_total,
                p.instant_booking, p.description,
                u.base_price_night, u.max_guests, u.name as unit_name,
                s.has_verified_sea_view, s.sea_view_positive_count,
                s.noise_negative_count, s.wifi_positive_count, s.wifi_negative_count,
                s.top_praised_summary, s.top_complaints_summary,
                (SELECT photo_url FROM property_photos WHERE property_id = p.id AND is_cover = 1 LIMIT 1) as cover_photo,
                (SELECT GROUP_CONCAT(a.name_ru, ' • ') FROM property_amenities pa JOIN amenities a ON pa.amenity_id = a.id WHERE pa.property_id = p.id) as amenities_names
            FROM properties p
            JOIN property_units u ON p.id = u.property_id
            JOIN property_sentiment_summary s ON p.id = s.property_id
            WHERE p.is_active = 1
        """
        params = []

        if intent["city"]:
            query_sql += " AND p.city = ?"
            params.append(intent["city"])

        if intent["guests"]:
            query_sql += " AND u.max_guests >= ?"
            params.append(intent["guests"])

        if intent["max_price"]:
            query_sql += " AND u.base_price_night <= ?"
            params.append(intent["max_price"])

        cur.execute(query_sql, params)
        rows = cur.fetchall()

        # Rank candidates using AI Aspect Scoring
        scored_candidates = []
        for r in rows:
            prop_id = r["id"]
            title = r["title"]
            base_score = r["rating_total"] * 10 # scale 0..100

            reasons_to_recommend = []
            warnings = []

            # Fetch detailed aspect quotes for this property
            cur.execute("""
                SELECT aspect_code, sentiment, excerpt 
                FROM review_aspects 
                WHERE property_id = ?
            """, (prop_id,))
            aspect_rows = cur.fetchall()

            aspect_map = {}
            for ar in aspect_rows:
                code, sent, excerpt = ar["aspect_code"], ar["sentiment"], ar["excerpt"]
                if code not in aspect_map:
                    aspect_map[code] = {"pos": [], "neg": []}
                if sent == "positive":
                    aspect_map[code]["pos"].append(excerpt)
                elif sent == "negative":
                    aspect_map[code]["neg"].append(excerpt)

            # Evaluate must-have aspects
            for must_asp in intent["must_have_aspects"]:
                if must_asp == "sea_view":
                    if aspect_map.get("sea_view", {}).get("pos"):
                        base_score += 40
                        reasons_to_recommend.append(f"Гости подтверждают вид на море: «{aspect_map['sea_view']['pos'][0]}»")
                    elif r["distance_to_sea_m"] and r["distance_to_sea_m"] < 150:
                        base_score += 15
                        reasons_to_recommend.append(f"Близко к морю ({r['distance_to_sea_m']}м)")
                    elif aspect_map.get("sea_view", {}).get("neg"):
                        base_score -= 50
                        warnings.append(f"Внимание: {aspect_map['sea_view']['neg'][0]}")

                if must_asp == "wifi_speed":
                    if aspect_map.get("wifi_speed", {}).get("pos"):
                        base_score += 25
                        reasons_to_recommend.append(f"Хвалят интернет: «{aspect_map['wifi_speed']['pos'][0]}»")
                    elif aspect_map.get("wifi_speed", {}).get("neg"):
                        base_score -= 30
                        warnings.append(f"Жалоба на интернет: «{aspect_map['wifi_speed']['neg'][0]}»")

                if must_asp == "yard_view":
                    if aspect_map.get("noise_street", {}).get("pos"):
                        base_score += 30
                        reasons_to_recommend.append(f"Тихий закрытый двор: «{aspect_map['noise_street']['pos'][0]}»")

            # Evaluate avoid aspects (Noise complaints)
            if "noise_street" in intent["avoid_aspects"]:
                if aspect_map.get("noise_street", {}).get("neg"):
                    base_score -= 80
                    warnings.append(f"В отзывах жалуются на шум: «{aspect_map['noise_street']['neg'][0]}»")
                elif aspect_map.get("noise_street", {}).get("pos"):
                    base_score += 30
                    reasons_to_recommend.append(f"Подтверждена тишина: «{aspect_map['noise_street']['pos'][0]}»")

            scored_candidates.append({
                "property_id": prop_id,
                "title": title,
                "city": r["city"],
                "district": r["district"],
                "address": r["address"],
                "property_type": r["property_type"],
                "price": r["base_price_night"],
                "rating": r["rating_total"],
                "reviews_count": r["reviews_count"],
                "distance_to_sea_m": r["distance_to_sea_m"],
                "instant_booking": bool(r["instant_booking"]),
                "cover_photo": r["cover_photo"] or "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
                "amenities_names": r["amenities_names"] or "",
                "description": r["description"] or "",
                "ai_score": round(base_score, 1),
                "reasons": reasons_to_recommend,
                "warnings": warnings,
                "top_praised": r["top_praised_summary"],
                "top_complaints": r["top_complaints_summary"]
            })

        # Sort by AI Score descending
        scored_candidates.sort(key=lambda x: x["ai_score"], reverse=True)
        conn.close()

        return {
            "query": user_prompt or "",
            "parsed_intent": intent,
            "total_candidates": len(scored_candidates),
            "results": scored_candidates
        }
