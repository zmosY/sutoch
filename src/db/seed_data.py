"""
Seed realistic demonstration data into the 7 tables matching the project architecture:
  1. users (USER)
  2. properties (Properties)
  3. property_embeddings (Property Embeddings - Шаг 1 пайплайна RAG)
  4. bookings (Bookings)
  5. chats (Messages chats)
  6. messages (Messages messages)
  7. reviews (Reviews)
"""

import os
import sys
import json

# Обеспечиваем импорт модулей проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from db.schema_sqlite import get_connection, init_db
from ai_engine.search_engine import RAGSearchEngine

def seed_database():
    print("Инициализация таблиц базы данных...")
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    print("Заполнение таблицы users (USER)...")
    users = [
        # Хозяева (hosts)
        (1, "host_elena@sutoch.ru", "pbkdf2_sha256$host123", "+7 (918) 123-45-67", "Елена", "Смирнова", "host"),
        (2, "host_maxim@sutoch.ru", "pbkdf2_sha256$host456", "+7 (921) 987-65-43", "Максим", "Волков", "host"),
        (3, "host_olga@sutoch.ru", "pbkdf2_sha256$host789", "+7 (985) 555-12-34", "Ольга", "Кузнецова", "host"),
        (4, "host_alex@sutoch.ru", "pbkdf2_sha256$host321", "+7 (911) 444-99-88", "Александр", "Морозов", "host"),
        # Гости (guests)
        (5, "guest_ivan@mail.ru", "pbkdf2_sha256$guest111", "+7 (903) 111-22-33", "Иван", "Петров", "guest"),
        (6, "guest_anna@yandex.ru", "pbkdf2_sha256$guest222", "+7 (916) 222-33-44", "Анна", "Соколова", "guest"),
        (7, "guest_dmitry@gmail.com", "pbkdf2_sha256$guest333", "+7 (925) 333-44-55", "Дмитрий", "Романов", "guest"),
        # Администратор (admin)
        (8, "admin@sutoch.ru", "pbkdf2_sha256$admin999", "+7 (800) 555-35-35", "Сергей", "Администратор", "admin")
    ]

    cursor.executemany("""
        INSERT INTO users (id, email, password_hash, phone, first_name, last_name, role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, users)
    conn.commit()

    print("Заполнение таблицы properties (Properties)...")
    properties = [
        (
            1, 1,
            "Панорамные апартаменты у моря «Black Sea View»",
            "Роскошные видовые апартаменты на первой береговой линии в центре Сочи. Прямой панорамный вид на море и закат с просторной террасы. Идеальная тишина, дизайнерский ремонт, скоростной Wi-Fi 200 Мбит/с, ортопедический матрас King-size и закрытая территория.",
            "apartment",
            7500.0,
            43.5786, 39.7288,
            "г. Сочи, ул. Черноморская, 10",
            4, 1
        ),
        (
            2, 2,
            "Дизайнерская студия у Невского проспекта",
            "Тихая и стильная квартира в историческом центре Санкт-Петербурга. Окна выходят в тихий закрытый зеленый двор без машин. 3 минуты пешком до метро Маяковская и Невского проспекта. Оснащена полноценной кухней, кондиционером и удобным рабочим местом.",
            "apartment",
            4900.0,
            59.9311, 30.3546,
            "г. Санкт-Петербург, ул. Марата, 14",
            3, 1
        ),
        (
            3, 3,
            "Премиум-апартаменты в башне Москва-Сити",
            "Апартаменты на 48 этаже башни «Федерация» с головокружительным видом на ночную Москву. Премиальная шумоизоляция, система умный дом, кофемашина Nespresso, ванна с панорамным окном и круглосуточная консьерж-служба.",
            "apartment",
            14500.0,
            55.7497, 37.5375,
            "г. Москва, Пресненская наб., 12",
            2, 1
        ),
        (
            4, 4,
            "Уютный дом-шале в сосновом бору у озера",
            "Атмосферный загородный деревянный дом с дровяным камином, русской баней на дровах и зоной барбекю. Уединенное место посреди реликтового леса, чистейший воздух, тишина и пение птиц. Прекрасно для семейного отдыха с детьми.",
            "house",
            11200.0,
            60.1982, 29.8921,
            "Ленинградская обл., пос. Рощино, Сосновая ул., 8",
            6, 1
        ),
        (
            5, 1,
            "Светлая студия в Адлере рядом с Олимпийским парком",
            "Уютная студия с балконом в 10 минутах ходьбы от моря и Имеретинской набережной. Рядом парк аттракционов «Сочи Парк», рестораны и пляж «Имеретинский». Отличный выбор для отдыха пары или соло-путешественников.",
            "apartment",
            3800.0,
            43.4025, 39.9654,
            "г. Сочи, Адлер, Парусная ул., 21",
            2, 1
        ),
        (
            6, 4,
            "Комната в бутик-отеле у Куршской косы",
            "Уютная комната в аутентичном деревянном коттедже на побережье Балтийского моря в Зеленоградске. Аромат хвои, свежий морской бриз, прокат велосипедов и домашние завтраки включены.",
            "room",
            3200.0,
            54.9587, 20.4789,
            "Калининградская обл., г. Зеленоградск, Курортный пр-т, 5",
            2, 1
        )
    ]

    cursor.executemany("""
        INSERT INTO properties (
            id, host_id, title, description, type,
            price_per_night, latitude, longitude, address,
            max_guests, is_available
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, properties)
    conn.commit()
    conn.close()

    print("Шаг 1: Векторизация базы в property_embeddings (Embedding Model 1536d)...")
    search_engine = RAGSearchEngine(get_connection)
    for prop in properties:
        p_id = prop[0]
        title = prop[2]
        desc = prop[3]
        search_engine.vectorize_and_store_property(p_id, title, desc)
        print(f"  -> Векторизован объект #{p_id}: '{title[:35]}...' (1536d)")

    conn = get_connection()
    cursor = conn.cursor()

    print("Заполнение таблицы bookings (Bookings)...")
    bookings = [
        (1, 1, 5, "2026-06-10", "2026-06-15", 37500.0, "completed"),
        (2, 2, 6, "2026-07-01", "2026-07-05", 19600.0, "completed"),
        (3, 3, 7, "2026-08-12", "2026-08-14", 29000.0, "completed"),
        (4, 4, 5, "2026-09-05", "2026-09-08", 33600.0, "completed"),
        (5, 1, 6, "2026-11-20", "2026-11-25", 37500.0, "confirmed")
    ]
    cursor.executemany("""
        INSERT INTO bookings (id, property_id, guest_id, check_in_date, check_out_date, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, bookings)

    print("Заполнение таблицы Messages (chats & messages)...")
    chats = [
        (1, 1, 5, 1),
        (2, 2, 6, 2)
    ]
    cursor.executemany("""
        INSERT INTO chats (id, property_id, guest_id, host_id)
        VALUES (?, ?, ?, ?)
    """, chats)

    messages = [
        (1, 1, 5, "Здравствуйте! Подскажите, есть ли возможность раннего заезда в 11 утра?", 1),
        (2, 1, 1, "Добрый день, Иван! Да, конечно, номер будет готов, встретим вас!", 1),
        (3, 2, 6, "Добрый вечер! Скажите, окна точно выходят во двор, тихо ли ночью?", 1),
        (4, 2, 2, "Здравствуйте, Анна! Да, дом с закрытым двором-колодцем, никакого шума с Марата нет вообще.", 1)
    ]
    cursor.executemany("""
        INSERT INTO messages (id, chat_id, sender_id, message_text, is_read)
        VALUES (?, ?, ?, ?, ?)
    """, messages)

    print("Заполнение таблицы reviews (Reviews)...")
    reviews = [
        (
            1, 1, 10, 10, 10,
            "Вид на море с террасы просто потрясающий! Засыпали и просыпались под шум прибоя. В квартире кристальная чистота, мебель новая, постельное белье премиум. Обязательно вернемся снова!",
            "Иван, спасибо большое за теплые слова! Всегда будем рады видеть вас снова!"
        ),
        (
            2, 2, 10, 9, 10,
            "Идеальное расположение — до Невского пару шагов, но в квартире абсолютная тишина благодаря закрытому двору. Очень стильный ремонт, есть капсульная кофеварка и быстрый интернет.",
            "Анна, благодарим за отзыв! Рады, что вам было комфортно!"
        ),
        (
            3, 3, 9, 10, 9,
            "Космический вид на вечернюю Москву с 48 этажа. Сервис на уровне пятизвездочного отеля. Ванна у панорамного окна — отдельное удовольствие.",
            "Дмитрий, спасибо! Ждем вас в гости снова."
        ),
        (
            4, 4, 10, 10, 10,
            "Отличное шале в лесу! Тишина, аромат сосен, баня просто великолепная. Вечером разжигали камин. Прекрасный хозяин Александр.",
            "Спасибо за отзыв! Приезжайте зимой на снежные выходные."
        )
    ]
    cursor.executemany("""
        INSERT INTO reviews (id, booking_id, rating_location, rating_cleanliness, rating_value, comment, host_reply)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, reviews)

    conn.commit()
    conn.close()
    print("[OK] База данных успешно заполнена реалистичными данными для всех 7 таблиц!")

if __name__ == "__main__":
    seed_database()
