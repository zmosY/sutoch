"""
====================================================================
СХЕМА БАЗЫ ДАННЫХ SQLITE (ФАЙЛ: src/db/schema_sqlite.py)
====================================================================
Данный файл реализует локальную реляционную базу данных SQLite,
структура которой на 100% повторяет архитектурную схему (ER-диаграмму):
  1. users (Таблица USER на схеме)
  2. properties (Таблица Properties на схеме)
  3. property_embeddings (Таблица Property Embeddings, 1536 измерений)
  4. bookings (Таблица Bookings на схеме)
  5. chats (Блок Messages: chats на схеме)
  6. messages (Блок Messages: messages на схеме)
  7. reviews (Таблица Reviews на схеме)
"""

import sqlite3
import os
import json
from typing import List

# Путь к файлу базы данных SQLite на диске: <корень_проекта>/data/sutochno_booking.db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sutochno_booking.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Создает и возвращает активное подключение к SQLite.
    
    Синтаксис и параметры:
    • os.makedirs: гарантирует существование папки 'data', создавая её при необходимости.
    • sqlite3.connect: открывает файл БД или создаёт новый, если файла ещё нет.
    • check_same_thread=False: по умолчанию SQLite в Python разрешает работу с соединением
      только из того потока, где оно создано. Поскольку FastAPI обрабатывает сетевые запросы
      в пуле рабочих потоков, этот флаг необходим, чтобы избежать ошибки ProgrammingError.
    • conn.row_factory = sqlite3.Row: позволяет обращаться к полям строки как по индексам,
      так и по названиям колонок (как к словарю: row["title"], row["price_per_night"]).
    • PRAGMA foreign_keys = ON: в SQLite внешние ключи (FOREIGN KEY) по умолчанию выключены!
      Эта команда принудительно включает контроль целостности связей между таблицами.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DB_PATH):
    """
    Создает 7 таблиц со всеми связями, индексами и ограничениями целостности.
    Вызывается при первоначальной настройке или пересоздании базы данных.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # executescript выполняет пакет команд SQL, разделенных точкой с запятой
    cursor.executescript("""
    -- ----------------------------------------------------------------
    -- Сброс старых таблиц (для чистого пересоздания)
    -- PRAGMA foreign_keys = OFF временно отключает проверку ключей,
    -- чтобы таблицы можно было удалить без ошибок порядка зависимостей.
    -- ----------------------------------------------------------------
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
    -- 1. ТАБЛИЦА: USER (Пользователи системы)
    -- Соответствует блоку USER на диаграмме.
    -- ====================================================================
    -- • id INTEGER PRIMARY KEY AUTOINCREMENT: уникальный номер пользователя,
    --   автоматически увеличивающийся (1, 2, 3...).
    -- • email TEXT UNIQUE NOT NULL: адрес электронной почты, обязателен (NOT NULL)
    --   и не может повторяться у двух разных пользователей (UNIQUE).
    -- • password_hash TEXT NOT NULL: криптографический хеш пароля (в открытом виде
    --   пароли в базах данных хранить категорически запрещено).
    -- • role TEXT CHECK(role IN ('guest', 'host', 'admin')): ограничение CHECK
    --   гарантирует, что роль может принимать только одно из 3 значений:
    --   гость (арендатор), хост (хозяин жилья) или администратор.
    -- • created_at TEXT DEFAULT CURRENT_TIMESTAMP: дата и время создания записи.
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

    -- Индекс для мгновенного поиска пользователя при логине по email: O(log N) вместо O(N)
    CREATE INDEX idx_users_email ON users(email);

    -- ====================================================================
    -- 2. ТАБЛИЦА: Properties (Объекты недвижимости: квартиры, дома, комнаты)
    -- Соответствует блоку Properties на диаграмме.
    -- ====================================================================
    -- • host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE:
    --   Внешний ключ (Foreign Key), связывающий объект с его хозяином из таблицы users.
    --   ON DELETE CASCADE означает: если аккаунт хозяина удаляется, автоматически
    --   удаляются и все принадлежащие ему объявления.
    -- • title TEXT NOT NULL: название объявления (например, "Панорамная студия у моря").
    -- • description TEXT: подробное описание жилья, правил и преимуществ.
    -- • type TEXT CHECK(...): тип объекта ('apartment', 'house', 'room').
    -- • price_per_night REAL NOT NULL: стоимость аренды за одни сутки (дробное число).
    -- • latitude REAL, longitude REAL: географические координаты для отображения на карте.
    -- • address TEXT NOT NULL: физический адрес объекта.
    -- • max_guests INTEGER: максимальная вместимость гостей.
    -- • is_available INTEGER DEFAULT 1: флаг доступности объекта (1 = доступен, 0 = снят).
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

    -- Индексы для ускорения фильтрации и выборки
    CREATE INDEX idx_properties_host ON properties(host_id);
    CREATE INDEX idx_properties_coords ON properties(latitude, longitude);
    CREATE INDEX idx_properties_price ON properties(price_per_night);

    -- ====================================================================
    -- 3. ТАБЛИЦА: Property Embeddings (Векторные представления объектов)
    -- Соответствует блоку Property Embeddings на диаграмме.
    -- Хранит числовой вектор размерности 1536 (Шаг 1 RAG-пайплайна).
    -- ====================================================================
    -- • property_id INTEGER PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE:
    --   Связь "один-к-одному" с объектом недвижимости.
    -- • embedding TEXT NOT NULL: массив из 1536 чисел с плавающей точкой,
    --   сериализованный в JSON строку: "[0.0125, -0.0431, ...]".
    --   В PostgreSQL с расширением pgvector это тип VECTOR(1536).
    -- • document_text TEXT: исходный текст (title + description), из которого получен вектор.
    -- ====================================================================
    CREATE TABLE property_embeddings (
        property_id INTEGER PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
        embedding TEXT NOT NULL,
        document_text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- ====================================================================
    -- 4. ТАБЛИЦА: Bookings (Бронирования жилья)
    -- Соответствует блоку Bookings на диаграмме.
    -- Связывает гостя, забронированный объект и конкретные даты заезда/выезда.
    -- ====================================================================
    -- • property_id INTEGER: ссылка на арендуемую квартиру.
    -- • guest_id INTEGER: ссылка на пользователя-арендатора.
    -- • check_in_date, check_out_date: даты заезда и выезда в формате 'YYYY-MM-DD'.
    -- • total_price REAL: общая стоимость проживания.
    -- • status TEXT CHECK(...): статус заявки (pending - на рассмотрении,
    --   confirmed - подтверждено, cancelled - отменено, completed - завершено).
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
    -- 5. ТАБЛИЦЫ: Messages (Чаты и сообщения между гостем и хозяином)
    -- Соответствует блоку Messages (chats & messages) на диаграмме.
    -- ====================================================================
    -- Таблица chats: диалоговая комната между конкретным гостем и хозяином по объекту.
    CREATE TABLE chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
        guest_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Таблица messages: отдельные реплики внутри чата.
    -- • chat_id INTEGER: к какому чату относится сообщение.
    -- • sender_id INTEGER: кто автор (гость или хозяин).
    -- • message_text TEXT: сам текст переписки.
    -- • is_read INTEGER: статус прочтения (0 = непрочитано, 1 = прочитано).
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
        sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        message_text TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_messages_chat ON messages(chat_id);

    -- ====================================================================
    -- 6. ТАБЛИЦА: Reviews (Отзывы гостей)
    -- Соответствует блоку Reviews на диаграмме.
    -- Привязана к совершенному бронированию (booking_id), что защищает от накрутки.
    -- ====================================================================
    -- • booking_id INTEGER: ссылка на бронь в таблице bookings.
    -- • rating_location, rating_cleanliness, rating_value: баллы от 1 до 10
    --   по ключевым критериям (расположение, чистота, соотношение цена/качество).
    -- • comment TEXT: текст отзыва гостя.
    -- • host_reply TEXT: официальный ответ хозяина жилья на отзыв (может быть пустым).
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

    # Фиксация изменений в файле БД
    conn.commit()
    conn.close()
    print("Database schema initialized successfully matching the diagram 100%.")

if __name__ == "__main__":
    init_db()
