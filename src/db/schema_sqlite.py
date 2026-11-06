"""
SQLite Database Schema matching the project ER-Diagram and RAG Architecture 1:1.
Tables:
  1. users (USER)
  2. properties (Properties)
  3. property_embeddings (Property Embeddings, VECTOR 1536)
  4. bookings (Bookings)
  5. chats (Messages chats)
  6. messages (Messages messages)
  7. reviews (Reviews)
"""

import sqlite3
import os
import json
from typing import List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sutochno_booking.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DB_PATH):
    """Инициализация базы данных со всеми 7 таблицами в точном соответствии с диаграммой."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    -- Очистка таблиц перед созданием
    PRAGMA foreign_keys = OFF;
    DROP TABLE IF EXISTS messages;
    DROP TABLE IF EXISTS chats;
    DROP TABLE IF EXISTS reviews;
    DROP TABLE IF EXISTS bookings;
    DROP TABLE IF EXISTS property_embeddings;
    DROP TABLE IF EXISTS properties;
    DROP TABLE IF EXISTS users;
    PRAGMA foreign_keys = ON;

    -- ====================================================================
    -- 1. USER: Пользователи (гости, хозяева, администраторы)
    -- ====================================================================
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        role TEXT CHECK(role IN ('guest', 'host', 'admin')) DEFAULT 'guest',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_users_email ON users(email);

    -- ====================================================================
    -- 2. Properties: Объекты недвижимости
    -- ====================================================================
    CREATE TABLE properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT,
        type TEXT CHECK(type IN ('apartment', 'house', 'room')) DEFAULT 'apartment',
        price_per_night REAL NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        max_guests INTEGER NOT NULL DEFAULT 2,
        is_available INTEGER NOT NULL DEFAULT 1 -- 1 (TRUE) / 0 (FALSE)
    );

    CREATE INDEX idx_properties_host ON properties(host_id);
    CREATE INDEX idx_properties_coords ON properties(latitude, longitude);
    CREATE INDEX idx_properties_price ON properties(price_per_night);

    -- ====================================================================
    -- 3. Property Embeddings: Векторные представления (1536 измерений)
    -- Хранят эмбеддинг title + description (Шаг 1 RAG-пайплайна)
    -- ====================================================================
    CREATE TABLE property_embeddings (
        property_id INTEGER PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
        embedding TEXT NOT NULL, -- JSON-массив из 1536 чисел с плавающей точкой
        document_text TEXT,      -- Исходный текст: title + description
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- ====================================================================
    -- 4. Bookings: Бронирования жилья
    -- ====================================================================
    CREATE TABLE bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        guest_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        check_in_date TEXT NOT NULL,
        check_out_date TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT CHECK(status IN ('pending', 'confirmed', 'cancelled', 'completed')) DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_bookings_prop ON bookings(property_id);
    CREATE INDEX idx_bookings_guest ON bookings(guest_id);

    -- ====================================================================
    -- 5. Messages: Чаты и сообщения между гостем и хозяином
    -- ====================================================================
    CREATE TABLE chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        guest_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
        sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        message_text TEXT NOT NULL,
        is_read INTEGER DEFAULT 0, -- 0 = False, 1 = True
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_messages_chat ON messages(chat_id);

    -- ====================================================================
    -- 6. Reviews: Отзывы гостей с оценками локации, чистоты и цены
    -- ====================================================================
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
        rating_location INTEGER NOT NULL CHECK (rating_location BETWEEN 1 AND 10),
        rating_cleanliness INTEGER NOT NULL CHECK (rating_cleanliness BETWEEN 1 AND 10),
        rating_value INTEGER NOT NULL CHECK (rating_value BETWEEN 1 AND 10),
        comment TEXT NOT NULL,
        host_reply TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_reviews_booking ON reviews(booking_id);
    """)

    conn.commit()
    conn.close()
    print("Database schema initialized successfully matching the diagram 100%.")

if __name__ == "__main__":
    init_db()
