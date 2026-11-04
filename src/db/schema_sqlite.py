"""
SQLite Database Schema and Initialization for Sutochno & Booking Clone
Supports JSON, FTS5 (Full-Text Search), and Aspect-Based Sentiment Analysis.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sutochno_booking.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    -- 1. Пользователи и роли
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE,
        first_name TEXT NOT NULL,
        last_name TEXT,
        avatar_url TEXT,
        role TEXT DEFAULT 'guest', -- 'guest', 'host', 'admin'
        is_verified_host INTEGER DEFAULT 0,
        host_rating REAL DEFAULT 0.0,
        response_rate_pct INTEGER DEFAULT 100,
        response_time_minutes INTEGER DEFAULT 15,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. Объекты недвижимости (Квартиры, Апартаменты, Отели, Коттеджи)
    CREATE TABLE IF NOT EXISTS properties (
        id TEXT PRIMARY KEY,
        host_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        property_type TEXT NOT NULL, -- 'apartment', 'studio', 'house', 'hotel'
        description TEXT,
        
        -- Локация
        country TEXT DEFAULT 'Россия',
        city TEXT NOT NULL,
        district TEXT,
        address TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        distance_to_center_km REAL,
        distance_to_sea_m INTEGER,   -- метры до моря (важно для Сочи/Крыма/Балтики)
        distance_to_metro_m INTEGER, -- метры до метро
        
        -- Правила проживания
        check_in_from TEXT DEFAULT '14:00',
        check_out_to TEXT DEFAULT '12:00',
        min_stay_nights INTEGER DEFAULT 1,
        max_stay_nights INTEGER DEFAULT 90,
        instant_booking INTEGER DEFAULT 1,
        deposit_amount REAL DEFAULT 0.0,
        cleaning_fee REAL DEFAULT 0.0,
        pets_allowed INTEGER DEFAULT 0,
        smoking_allowed INTEGER DEFAULT 0,
        parties_allowed INTEGER DEFAULT 0,
        quiet_hours_start TEXT DEFAULT '22:00',
        quiet_hours_end TEXT DEFAULT '08:00',
        
        -- Рейтинги
        rating_total REAL DEFAULT 0.0,
        reviews_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- 3. Номера и юниты
    CREATE TABLE IF NOT EXISTS property_units (
        id TEXT PRIMARY KEY,
        property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        unit_type TEXT DEFAULT 'entire_place',
        total_area_sqm REAL,
        floor INTEGER,
        total_floors INTEGER,
        has_elevator INTEGER DEFAULT 1,
        max_guests INTEGER NOT NULL,
        bedrooms_count INTEGER DEFAULT 1,
        beds_count INTEGER DEFAULT 1,
        beds_configuration TEXT, -- JSON: [{"type": "double_bed", "count": 1}]
        base_price_night REAL NOT NULL,
        extra_guest_fee REAL DEFAULT 0.0
    );

    -- 4. Удобства (Amenities)
    CREATE TABLE IF NOT EXISTS amenities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        name_ru TEXT NOT NULL,
        icon_name TEXT
    );

    CREATE TABLE IF NOT EXISTS property_amenities (
        property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        amenity_id INTEGER NOT NULL REFERENCES amenities(id) ON DELETE CASCADE,
        PRIMARY KEY (property_id, amenity_id)
    );

    -- 5. Фотографии
    CREATE TABLE IF NOT EXISTS property_photos (
        id TEXT PRIMARY KEY,
        property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        photo_url TEXT NOT NULL,
        tag TEXT, -- 'view_window', 'bedroom', 'balcony', 'kitchen'
        caption TEXT,
        is_cover INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0
    );

    -- 6. Тарифные планы (Rate Plans)
    CREATE TABLE IF NOT EXISTS rate_plans (
        id TEXT PRIMARY KEY,
        property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        cancellation_policy TEXT DEFAULT 'flexible', -- 'flexible_24h', 'moderate_5d', 'strict'
        discount_pct REAL DEFAULT 0.0,
        meals_included TEXT DEFAULT 'none'
    );

    -- 7. Календарь цен и доступности на каждый день
    CREATE TABLE IF NOT EXISTS unit_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id TEXT NOT NULL REFERENCES property_units(id) ON DELETE CASCADE,
        date TEXT NOT NULL, -- 'YYYY-MM-DD'
        price REAL NOT NULL,
        is_available INTEGER DEFAULT 1,
        min_nights INTEGER DEFAULT 1,
        unavailable_reason TEXT, -- 'booking', 'owner_block', 'ical_sync'
        booking_id TEXT,
        UNIQUE(unit_id, date)
    );

    -- 8. Бронирования
    CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY,
        unit_id TEXT NOT NULL REFERENCES property_units(id),
        guest_id TEXT NOT NULL REFERENCES users(id),
        rate_plan_id TEXT REFERENCES rate_plans(id),
        check_in_date TEXT NOT NULL,
        check_out_date TEXT NOT NULL,
        nights_count INTEGER NOT NULL,
        guests_count INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        prepayment_amount REAL NOT NULL,
        platform_fee_amount REAL NOT NULL,
        host_payout_amount REAL NOT NULL,
        status TEXT DEFAULT 'confirmed', -- 'pending', 'confirmed', 'completed', 'cancelled'
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- 9. Отзывы (Reviews)
    CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        booking_id TEXT UNIQUE NOT NULL REFERENCES bookings(id),
        property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        guest_id TEXT NOT NULL REFERENCES users(id),
        
        rating_overall REAL NOT NULL,
        rating_cleanliness INTEGER,
        rating_location INTEGER,
        rating_comfort INTEGER,
        rating_value_for_money INTEGER,
        rating_host INTEGER,
        rating_wifi INTEGER,
        
        pros_text TEXT,       -- "Что понравилось"
        cons_text TEXT,       -- "Что не понравилось / жалобы"
        general_comment TEXT,
        
        host_reply TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- 10. Аспекты отзывов (Aspect-Based Sentiment Analysis)
    CREATE TABLE IF NOT EXISTS review_aspects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
        property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        aspect_code TEXT NOT NULL, -- 'sea_view', 'noise_street', 'noise_neighbors', 'wifi_speed', etc.
        sentiment TEXT NOT NULL,   -- 'positive', 'negative', 'neutral'
        confidence REAL DEFAULT 1.0,
        excerpt TEXT NOT NULL,     -- точная цитата из отзыва
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- 11. Агрегированные инсайты для быстрого ИИ-поиска
    CREATE TABLE IF NOT EXISTS property_sentiment_summary (
        property_id TEXT PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
        has_verified_sea_view INTEGER DEFAULT 0,
        sea_view_positive_count INTEGER DEFAULT 0,
        noise_negative_count INTEGER DEFAULT 0,
        wifi_positive_count INTEGER DEFAULT 0,
        wifi_negative_count INTEGER DEFAULT 0,
        top_praised_summary TEXT,   -- "Шикарный вид на море, чистый душ, мягкий матрас"
        top_complaints_summary TEXT -- "Шум с трассы, слабый вай-фай на балконе"
    );

    -- 12. Full-Text Search виртуальная таблица (FTS5) для быстрого гибридного поиска
    CREATE VIRTUAL TABLE IF NOT EXISTS property_search_fts USING fts5(
        property_id UNINDEXED,
        title,
        city,
        district,
        description,
        amenities_list,
        ai_praised,
        ai_complaints,
        tokenize='unicode61 remove_diacritics 2'
    );

    -- 13. AI Диалоги и поиск
    CREATE TABLE IF NOT EXISTS ai_chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(id),
        title TEXT,
        context_filters TEXT, -- JSON
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ai_chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
        sender TEXT NOT NULL, -- 'user', 'assistant'
        content TEXT NOT NULL,
        recommended_properties TEXT, -- JSON array of property IDs
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_prop_city ON properties(city);
    CREATE INDEX IF NOT EXISTS idx_prop_type ON properties(property_type);
    CREATE INDEX IF NOT EXISTS idx_aspects_tag ON review_aspects(property_id, aspect_code, sentiment);
    CREATE INDEX IF NOT EXISTS idx_cal_avail ON unit_calendar(unit_id, date, is_available);
    """);

    conn.commit()
    conn.close()
    print("Database schema successfully created!")

if __name__ == "__main__":
    init_db()
