-- ====================================================================
-- Production PostgreSQL Database Schema (Архитектурная схема проекта)
-- Полное соответствие диаграмме сущностей (ERD) и RAG-пайплайну
-- ====================================================================

-- Подключение расширения pgvector для хранения и поиска векторов (1536d)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- --------------------------------------------------------------------
-- 1. ТАБЛИЦА: USER (Пользователи системы)
-- Соответствует блоку USER на диаграмме
-- --------------------------------------------------------------------
CREATE TYPE user_role AS ENUM ('guest', 'host', 'admin');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    role user_role NOT NULL DEFAULT 'guest',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- --------------------------------------------------------------------
-- 2. ТАБЛИЦА: Properties (Объекты недвижимости)
-- Соответствует блоку Properties на диаграмме
-- --------------------------------------------------------------------
CREATE TYPE property_type AS ENUM ('apartment', 'house', 'room');

CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    host_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type property_type NOT NULL DEFAULT 'apartment',
    price_per_night DECIMAL(10, 2) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address VARCHAR(255) NOT NULL,
    max_guests INT NOT NULL DEFAULT 2,
    is_available BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_properties_host ON properties(host_id);
CREATE INDEX idx_properties_coords ON properties(latitude, longitude);
CREATE INDEX idx_properties_price ON properties(price_per_night);

-- --------------------------------------------------------------------
-- 3. ТАБЛИЦА: Property Embeddings (Векторные представления объектов)
-- Соответствует блоку Property Embeddings на диаграмме
-- Вход: title + description (Шаг 1 RAG-пайплайна)
-- Модель: Embedding Model (OpenAI text-embedding-3-small, 1536 измерений)
-- --------------------------------------------------------------------
CREATE TABLE property_embeddings (
    property_id INT PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW-индекс для мгновенного поиска по косинусному сходству (Cosine Distance)
CREATE INDEX idx_property_embeddings_cosine 
ON property_embeddings USING hnsw (embedding vector_cosine_ops);

-- --------------------------------------------------------------------
-- 4. ТАБЛИЦА: Bookings (Бронирования)
-- Соответствует блоку Bookings на диаграмме
-- --------------------------------------------------------------------
CREATE TYPE booking_status AS ENUM ('pending', 'confirmed', 'cancelled', 'completed');

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    guest_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status booking_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bookings_dates ON bookings(property_id, check_in_date, check_out_date);
CREATE INDEX idx_bookings_guest ON bookings(guest_id);

-- --------------------------------------------------------------------
-- 5. ТАБЛИЦЫ: Messages (Чаты и сообщения)
-- Соответствует блоку Messages (chats & messages) на диаграмме
-- --------------------------------------------------------------------
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    guest_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    host_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    chat_id INT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    sender_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_chat ON messages(chat_id, created_at);

-- --------------------------------------------------------------------
-- 6. ТАБЛИЦА: Reviews (Отзывы гостей)
-- Соответствует блоку Reviews на диаграмме
-- Привязаны к верифицированному бронированию (booking_id)
-- --------------------------------------------------------------------
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    booking_id INT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    rating_location INT NOT NULL CHECK (rating_location BETWEEN 1 AND 10),
    rating_cleanliness INT NOT NULL CHECK (rating_cleanliness BETWEEN 1 AND 10),
    rating_value INT NOT NULL CHECK (rating_value BETWEEN 1 AND 10),
    comment TEXT NOT NULL,
    host_reply TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_booking ON reviews(booking_id);

-- ====================================================================
-- ПОТОК ДАННЫХ RAG (RETRIEVAL-AUGMENTED GENERATION)
-- ====================================================================
-- Шаг 1: Векторизация базы
--   Вход:   Текст (properties.title + ' ' + properties.description)
--   Модель: Embedding Model (1536d)
--   Выход:  Вектор VECTOR(1536) -> запись в property_embeddings
--
-- Шаг 2: Векторизация запроса
--   Вход:   Поисковый запрос пользователя ("квартира у моря с балконом")
--   Модель: Та же Embedding Model (1536d)
--   Выход:  Вектор запроса
--
-- Шаг 3: Семантический поиск
--   Метод:  Косинусное сходство (Cosine Similarity / pgvector <=>)
--   Запрос: SELECT property_id, 1 - (embedding <=> :query_vector) AS similarity
--           FROM property_embeddings ORDER BY similarity DESC LIMIT 5;
--   Выход:  Топ-3 или Топ-5 наиболее релевантных объектов (Контекст)
--
-- Шаг 4: Генерация ответа
--   Вход:   Контекст найденных квартир + Текст запроса пользователя
--   Модель: LLM (Языковая модель)
--   Выход:  Человеческий связный ответ с рекомендациями на экран
-- ====================================================================
