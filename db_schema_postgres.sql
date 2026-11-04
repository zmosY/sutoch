-- ====================================================================
-- Production PostgreSQL Database Schema
-- Hybrid Booking.com & Sutochno.ru Architecture with AI Aspect Sentiment
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. USERS & ROLES
CREATE TYPE user_role AS ENUM ('guest', 'host', 'manager', 'admin');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(30) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    avatar_url TEXT,
    role user_role DEFAULT 'guest',
    is_verified_host BOOLEAN DEFAULT FALSE,
    host_rating DECIMAL(3, 2) DEFAULT 0.0,
    response_rate_pct INT DEFAULT 100, -- % ответов хозяина на заявки (как на Суточно)
    response_time_minutes INT DEFAULT 15,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. PROPERTIES (Объекты размещения: Квартиры, Апартаменты, Отели, Коттеджи)
CREATE TYPE property_type AS ENUM ('apartment', 'studio', 'house', 'hotel', 'guesthouse', 'glamping');

CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    host_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    property_type property_type NOT NULL,
    description TEXT,
    
    -- Локация и геометки (критично для фильтров "вид на море", "у пляжа", "у метро")
    country VARCHAR(100) DEFAULT 'Россия',
    region VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    distance_to_center_km DECIMAL(6, 2),
    distance_to_sea_m INT, -- метры до моря (для курортов Сочи, Крым, Балтика)
    distance_to_metro_m INT, -- метры до метро (для Мск, СПб)
    
    -- Правила проживания (House Rules - Суточно.ру)
    check_in_from TIME DEFAULT '14:00',
    check_out_to TIME DEFAULT '12:00',
    min_stay_nights INT DEFAULT 1,
    max_stay_nights INT DEFAULT 90,
    instant_booking BOOLEAN DEFAULT TRUE, -- мгновенное бронирование без ожидания ответа хозяина
    deposit_amount DECIMAL(10, 2) DEFAULT 0.0, -- страховой залог при заселении
    cleaning_fee DECIMAL(10, 2) DEFAULT 0.0,
    pets_allowed BOOLEAN DEFAULT FALSE,
    smoking_allowed BOOLEAN DEFAULT FALSE,
    parties_allowed BOOLEAN DEFAULT FALSE,
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    
    -- Агрегированные оценки
    rating_total DECIMAL(3, 2) DEFAULT 0.0,
    reviews_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_properties_city ON properties(city);
CREATE INDEX idx_properties_coords ON properties(latitude, longitude);
CREATE INDEX idx_properties_sea_dist ON properties(distance_to_sea_m) WHERE distance_to_sea_m IS NOT NULL;

-- 3. PROPERTY UNITS (Номера в отелях или конкретные комнаты/квартиры)
CREATE TABLE property_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL, -- "Апартаменты-студия с видом на море", "Двухместный номер Делюкс"
    unit_type VARCHAR(50) DEFAULT 'entire_place', -- 'entire_place', 'private_room', 'shared_room'
    total_area_sqm DECIMAL(6, 2),
    floor INT,
    total_floors INT,
    has_elevator BOOLEAN DEFAULT TRUE,
    
    -- Вместимость
    max_guests INT NOT NULL,
    max_adults INT NOT NULL,
    max_children INT DEFAULT 0,
    bedrooms_count INT DEFAULT 1,
    bathrooms_count INT DEFAULT 1,
    beds_configuration JSONB, -- [{"type": "double_bed", "count": 1}, {"type": "sofa_bed", "count": 1}]
    
    base_price_night DECIMAL(10, 2) NOT NULL,
    extra_guest_fee DECIMAL(10, 2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_units_prop_id ON property_units(property_id);
CREATE INDEX idx_units_guests ON property_units(max_guests);

-- 4. AMENITIES (Удобства и инфраструктура)
CREATE TABLE amenities (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL, -- 'sea_view', 'balcony', 'high_speed_wifi', 'workspace', 'air_conditioning'
    category VARCHAR(50) NOT NULL,    -- 'view', 'comfort', 'kitchen', 'work', 'bathroom', 'building'
    name_ru VARCHAR(100) NOT NULL,
    icon_name VARCHAR(50)
);

CREATE TABLE property_amenities (
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    amenity_id INT NOT NULL REFERENCES amenities(id) ON DELETE CASCADE,
    PRIMARY KEY (property_id, amenity_id)
);

-- 5. PHOTOS & MEDIA
CREATE TABLE property_photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    unit_id UUID REFERENCES property_units(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    tag VARCHAR(50), -- 'view_window', 'bedroom', 'living_room', 'bathroom', 'kitchen', 'balcony'
    caption TEXT,
    is_cover BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0
);

-- 6. RATE PLANS (Тарифные планы - модель Booking.com)
CREATE TABLE rate_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL, -- "Стандартный тариф (Бесплатная отмена)", "Невозвратный со скидкой 10%"
    cancellation_policy VARCHAR(50) DEFAULT 'flexible', -- 'flexible_24h', 'moderate_5d', 'strict_non_refundable'
    discount_pct DECIMAL(5, 2) DEFAULT 0.0,
    meals_included VARCHAR(50) DEFAULT 'none', -- 'none', 'breakfast', 'all_inclusive'
    is_active BOOLEAN DEFAULT TRUE
);

-- 7. CALENDAR & AVAILABILITY (Динамические цены и сетка занятости)
CREATE TABLE unit_calendar (
    id BIGSERIAL PRIMARY KEY,
    unit_id UUID NOT NULL REFERENCES property_units(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    min_nights INT DEFAULT 1,
    unavailable_reason VARCHAR(50), -- 'booking', 'owner_block', 'ical_sync'
    booking_id UUID,
    UNIQUE(unit_id, date)
);

CREATE INDEX idx_calendar_unit_date ON unit_calendar(unit_id, date, is_available);

-- 8. ICAL CHANNEL MANAGER FEEDS (Синхронизация с Авито, Циан, Островок, Суточно)
CREATE TABLE ical_feeds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_id UUID NOT NULL REFERENCES property_units(id) ON DELETE CASCADE,
    channel_name VARCHAR(50) NOT NULL, -- 'avito', 'sutochno', 'cian', 'airbnb', 'bnovo'
    import_feed_url TEXT NOT NULL,
    export_token VARCHAR(100) UNIQUE NOT NULL,
    last_synced_at TIMESTAMPTZ,
    sync_status VARCHAR(20) DEFAULT 'active'
);

-- 9. BOOKINGS & PAYMENTS (Сделки и финансовый расчет)
CREATE TYPE booking_status AS ENUM (
    'created', 
    'awaiting_host_approval', 
    'confirmed', 
    'checked_in', 
    'completed', 
    'cancelled_by_guest', 
    'cancelled_by_host'
);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_id UUID NOT NULL REFERENCES property_units(id),
    guest_id UUID NOT NULL REFERENCES users(id),
    rate_plan_id UUID REFERENCES rate_plans(id),
    
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    nights_count INT NOT NULL,
    guests_count INT NOT NULL,
    
    -- Финансы (Суточно: аванс 15-20% на платформе, остаток хозяину)
    total_amount DECIMAL(10, 2) NOT NULL,
    prepayment_amount DECIMAL(10, 2) NOT NULL,
    platform_fee_amount DECIMAL(10, 2) NOT NULL,
    host_payout_amount DECIMAL(10, 2) NOT NULL,
    is_paid BOOLEAN DEFAULT FALSE,
    
    status booking_status DEFAULT 'confirmed',
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. REVIEWS (Верифицированные отзывы гостей)
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID UNIQUE NOT NULL REFERENCES bookings(id),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    guest_id UUID NOT NULL REFERENCES users(id),
    
    -- Детальные оценки по категориям (1..10)
    rating_overall DECIMAL(3, 1) NOT NULL,
    rating_cleanliness INT CHECK (rating_cleanliness BETWEEN 1 AND 10),
    rating_location INT CHECK (rating_location BETWEEN 1 AND 10),
    rating_comfort INT CHECK (rating_comfort BETWEEN 1 AND 10),
    rating_value_for_money INT CHECK (rating_value_for_money BETWEEN 1 AND 10),
    rating_host INT CHECK (rating_host BETWEEN 1 AND 10),
    rating_wifi INT CHECK (rating_wifi BETWEEN 1 AND 10),
    
    -- Текстовые блоки отзыва (Booking / Суточно формат)
    pros_text TEXT,       -- "Что понравилось"
    cons_text TEXT,       -- "Что не понравилось / на что жалуются"
    general_comment TEXT, -- Общий отзыв
    
    host_reply TEXT,
    host_replied_at TIMESTAMPTZ,
    is_moderated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reviews_property ON reviews(property_id);

-- 11. AI ASPECT-BASED SENTIMENT ANALYSIS (Аспекты отзывов: похвала и жалобы)
-- Это ядро ИИ-поиска: раскладывает отзывы на конкретные аспекты реальности
CREATE TABLE review_aspects (
    id BIGSERIAL PRIMARY KEY,
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    
    -- Категория аспекта
    aspect_code VARCHAR(50) NOT NULL,
    -- 'sea_view'             -- Вид на море
    -- 'noise_street'         -- Шум с улицы/бара/трассы
    -- 'noise_neighbors'      -- Шумоизоляция / слышимость соседей
    -- 'wifi_speed'           -- Скорость и стабильность интернета
    -- 'bed_mattress'         -- Удобство кровати и матраса
    -- 'cleanliness_bathroom' -- Чистота санузла
    -- 'air_conditioner'      -- Работа кондиционера
    -- 'water_pressure'       -- Напор и температура горячей воды
    -- 'kitchen_amenities'    -- Оснащенность кухни (сковородки, чайник, специи)
    -- 'checkin_ease'         -- Удобство заселения (бесконтактное / пунктуальность)
    
    sentiment VARCHAR(20) NOT NULL, -- 'positive', 'negative', 'neutral'
    confidence DECIMAL(4, 3) DEFAULT 1.0, -- Уверенность ML (0.000..1.000)
    excerpt TEXT NOT NULL, -- Точная цитата: "Шум с трассы не дает спать даже с закрытыми окнами"
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_aspects_search ON review_aspects(property_id, aspect_code, sentiment);

-- 12. MATERIALIZED AI SENTIMENT PROFILES (Предрассчитанный профиль для быстрого RAG)
CREATE TABLE property_sentiment_summary (
    property_id UUID PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
    top_praised_aspects JSONB,   -- [{"aspect": "sea_view", "count": 14, "quote": "Вид на море с 15 этажа просто космос"}]
    top_complaint_aspects JSONB, -- [{"aspect": "noise_street", "count": 3, "quote": "Слышно музыку из бара на набережной"}]
    has_verified_sea_view BOOLEAN DEFAULT FALSE,
    is_quiet_verified BOOLEAN DEFAULT FALSE,
    is_work_friendly_wifi BOOLEAN DEFAULT FALSE,
    last_computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. SEMANTIC VECTOR EMBEDDINGS (pgvector для свободного поиска)
CREATE TABLE property_embeddings (
    property_id UUID PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
    -- Векторный слепок объекта (комбинация описания, правил и выжимки отзывов)
    embedding vector(1536),
    document_text TEXT, -- Текст, подаваемый в эмбеддинг для семантического поиска
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. AI CHAT CONVERSATIONS (История поиска через диалог)
CREATE TABLE ai_chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(150),
    context_filters JSONB, -- Текущие жесткие фильтры (даты, гости, бюджет, город)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    recommended_property_ids UUID[], -- id предложенных вариантов
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
