"""
Realistic Seed Dataset for Sutochno, Booking & Airbnb Clone.
Features:
- Categorized authentic amenities (kitchen, comfort, tech, bathroom, security, view)
- Multiple high-res photos per property (5-6 photos each)
- Real user accounts with avatars and cities
- Real reviews with 1:1 match between reviews_count on main page and detailed reviews
- Aspect-based sentiment extractions (ABSA) for AI assistant
"""

import json
import uuid
import datetime
from src.db.schema_sqlite import get_connection, init_db

def seed_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    tables = [
        "ai_chat_messages", "ai_chat_sessions", "property_search_fts",
        "property_sentiment_summary", "review_aspects", "reviews",
        "bookings", "unit_calendar", "rate_plans", "property_photos",
        "property_amenities", "amenities", "property_units", "properties", "users"
    ]
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t};")
    cur.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()

    init_db()
    conn = get_connection()
    cur = conn.cursor()

    # 1. AMENITIES (Categorized by Sutochno / Booking / Airbnb standards)
    amenities_data = [
        # View & Outdoor
        ("sea_view", "view", "Прямой вид на море", "🌊"),
        ("mountain_view", "view", "Вид на горы", "🏔️"),
        ("yard_view", "view", "Вид в тихий зеленый двор", "🌳"),
        ("balcony", "view", "Балкон с зоной отдыха", "🪑"),
        # Work & Internet
        ("high_speed_wifi", "work", "Скоростной Wi-Fi (до 500 Мбит/с)", "📶"),
        ("dedicated_workspace", "work", "Рабочее место с удобным креслом", "💻"),
        ("smart_tv", "tech", "Smart TV (Кинопоиск, YouTube)", "📺"),
        # Climate & Comfort
        ("air_conditioning", "comfort", "Сплит-система / Кондиционер", "❄️"),
        ("soundproofing", "comfort", "Усиленная звукоизоляция", "🔇"),
        ("floor_heating", "comfort", "Подогрев полов", "♨️"),
        ("blackout_curtains", "comfort", "Плотные шторы блэкаут", "🌙"),
        ("iron", "comfort", "Утюг и гладильная доска", "👔"),
        # Kitchen
        ("kitchen_full", "kitchen", "Оборудованная кухня", "🍳"),
        ("dishwasher", "kitchen", "Посудомоечная машина", "🍽️"),
        ("refrigerator", "kitchen", "Большой холодильник", "🧊"),
        ("microwave", "kitchen", "Микроволновая печь", "🍿"),
        ("coffee_machine", "kitchen", "Кофемашина Nespresso", "☕"),
        ("kettle", "kitchen", "Электрический чайник", "🫖"),
        # Bathroom
        ("washing_machine", "bathroom", "Стиральная машина", "🧺"),
        ("hairdryer", "bathroom", "Фен для волос", "💨"),
        ("water_heater", "bathroom", "Бойлер (горячая вода всегда)", "🚿"),
        ("toiletries", "bathroom", "Шампунь, гель и полотенца", "🧴"),
        # Building & Security
        ("self_checkin", "security", "Бесконтактное заселение (смарт-замок)", "🔑"),
        ("elevator", "building", "Бесшумный лифт", "🛗"),
        ("parking", "building", "Бесплатная парковка у дома", "🅿️"),
        ("cctv", "security", "Видеонаблюдение в подъезде", "📹"),
        # Rules
        ("pets_allowed", "rules", "Можно с питомцами", "🐾"),
        ("baby_crib", "family", "Детская кроватка", "👶"),
    ]

    amenity_id_map = {}
    for code, cat, name, icon in amenities_data:
        cur.execute(
            "INSERT INTO amenities (code, category, name_ru, icon_name) VALUES (?, ?, ?, ?) RETURNING id;",
            (code, cat, name, icon)
        )
        row = cur.fetchone()
        amenity_id_map[code] = row[0]

    # 2. USERS (Hosts with verified badges and Guests with avatars and cities)
    users = [
        # Hosts
        ("u_host_elena", "elena@sochirealty.ru", "+79180010011", "Елена", "Соколова", "Сочи", 
         "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=250&q=80", "host", 1, 4.98, 99, 5),
        ("u_host_mikhail", "mikhail@spbrest.ru", "+79211112233", "Михаил", "Романов", "Санкт-Петербург", 
         "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=250&q=80", "host", 1, 4.95, 96, 12),
        ("u_host_dmitry", "dmitry@baltichome.ru", "+79062223344", "Дмитрий", "Белов", "Зеленоградск", 
         "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=250&q=80", "host", 1, 4.99, 100, 3),
        ("u_host_artyom", "artyom@partyrent.ru", "+79183334455", "Артём", "Кузнецов", "Сочи", 
         "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=250&q=80", "host", 0, 4.10, 82, 45),
        ("u_host_anna", "anna@kazanlux.ru", "+79874445566", "Анна", "Сафина", "Казань", 
         "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80", "host", 1, 4.92, 98, 15),

        # Guests (with avatars and cities, plus one without avatar for fallback testing)
        ("u_guest_alex", "alex.it@gmail.com", "+79998883344", "Александр", "Смирнов", "Москва", 
         "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_olga", "olga.travel@yandex.ru", "+79998881122", "Ольга", "Морозова", "Екатеринбург", 
         "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_kate", "kate.novikova@mail.ru", "+79998885566", "Екатерина", "Новикова", "Санкт-Петербург", 
         "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_ivan", "ivan.nomad@ya.ru", "+79998887788", "Иван", "Волков", "Новосибирск", 
         "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_daria", "daria.art@gmail.com", "+79998889900", "Дарья", "Васильева", "Казань", 
         "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_sergey", "sergey.it@mail.ru", "+79997771122", "Сергей", "Ковалёв", "Нижний Новгород", 
         "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_marina", "marina.samara@ya.ru", "+79997773344", "Марина", "Полякова", "Самара", 
         "https://images.unsplash.com/photo-1534751516642-a171edd2521d?auto=format&fit=crop&w=250&q=80", "guest", 0, 5.0, 100, 0),
        ("u_guest_timur", "timur.ufa@gmail.com", "+79997775566", "Тимур", "Ильясов", "Уфа", 
         None, "guest", 0, 5.0, 100, 0), # No avatar test
    ]

    for uid, email, phone, fn, ln, city, avatar, role, ver, rating, resp_pct, resp_time in users:
        cur.execute("""
            INSERT INTO users (id, email, phone, first_name, last_name, city, avatar_url, role, is_verified_host, host_rating, response_rate_pct, response_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, email, phone, fn, ln, city, avatar, role, ver, rating, resp_pct, resp_time))

    # 3. PROPERTIES DATASET WITH MULTIPLE PHOTOS & AUTHENTIC SUTOCHO / BOOKING SPECS
    properties_raw = [
        # --- 1. SOCHI SEA VIEW PANORAMIC ---
        {
            "id": "prop_sochi_panoramic_sea",
            "host_id": "u_host_elena",
            "title": "Панорамная студия у моря с балконом в ЖК «Морской Бриз»",
            "property_type": "apartment",
            "city": "Сочи",
            "district": "Хостинский район",
            "address": "Курортный проспект, д. 108/6",
            "latitude": 43.56012,
            "longitude": 39.75489,
            "distance_to_center_km": 3.5,
            "distance_to_sea_m": 80,
            "distance_to_metro_m": None,
            "description": "Роскошная видовая студия на 16 этаже жилого комплекса премиум-класса «Морской Бриз». Прямой панорамный вид на Черное море и закаты прямо с кровати и террасы. Здание расположено на первой береговой линии: окна смотрят на воду, а Курортный проспект и железнодорожная ветка скрыты за горным рельефом с противоположной стороны дома. Оборудована полноценная рабочая зона с эргономичным креслом и оптоволоконным интернетом со скоростью 200 Мбит/с. Бесконтактный умный замок для заезда в любое время суток.",
            "instant_booking": 1,
            "deposit_amount": 5000.0,
            "cleaning_fee": 1500.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "parties_allowed": 0,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "14:00",
            "check_out_to": "12:00",
            "amenities": [
                "sea_view", "balcony", "high_speed_wifi", "dedicated_workspace", "smart_tv",
                "air_conditioning", "soundproofing", "floor_heating", "blackout_curtains", "iron",
                "kitchen_full", "dishwasher", "refrigerator", "microwave", "coffee_machine", "kettle",
                "washing_machine", "hairdryer", "water_heater", "toiletries",
                "self_checkin", "elevator", "cctv"
            ],
            "photos": [
                ("https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=85", "view_window", "Панорамный вид на Черное море и терраса", 1),
                ("https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=80", "bedroom", "Двуспальная кровать King-Size с ортопедическим матрасом", 0),
                ("https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80", "living_room", "Светлая гостиная зона и рабочий стол", 0),
                ("https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=800&q=80", "kitchen", "Кухня с кофемашиной и посудомоечной машиной", 0),
                ("https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=800&q=80", "bathroom", "Ванная комната с тропическим душем", 0),
                ("https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80", "balcony", "Балкон со столиком для закатов", 0)
            ],
            "unit": {
                "id": "unit_sochi_panoramic_sea",
                "name": "Видовая студия Deluxe (16 этаж)",
                "total_area_sqm": 42.0,
                "floor": 16,
                "total_floors": 18,
                "has_elevator": 1,
                "max_guests": 2,
                "bedrooms_count": 1,
                "beds_count": 1,
                "beds_configuration": json.dumps([{"type": "Двуспальная кровать King-Size (180x200)", "count": 1}]),
                "base_price_night": 6500.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_alex",
                    "created_at": "2026-10-22 14:15:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 9, "host": 10,
                    "pros": "Потрясающий прямой вид на море! Сидели на балконе каждый вечер и встречали закат. Шума от дороги вообще нет — дом стоит так, что окна смотрят на воду, слышен только прибой. Интернет 200 Мбит, проводил зум-колы на удаленке целыми днями без единого лага.",
                    "cons": "Лифт иногда приходится подождать 2-3 минуты в час пик.",
                    "comment": "Один из лучших вариантов для спокойного отдыха и удаленной работы в Сочи. Вернемся обязательно!",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Потрясающий прямой вид на море, закат с балкона"),
                        ("noise_street", "positive", 0.98, "Шума дороги вообще нет, слышен только легкий прибой"),
                        ("wifi_speed", "positive", 1.0, "Интернет 200 Мбит, зум-колы целыми днями без единого лага"),
                        ("bed_comfort", "positive", 0.95, "Огромная двуспальная кровать с мягким матрасом"),
                    ]
                },
                {
                    "guest_id": "u_guest_olga",
                    "created_at": "2026-09-15 11:30:00",
                    "rating_overall": 9.8,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 9, "host": 10,
                    "pros": "Вид из окна захватывает дух. Чистейшая квартира, всё новое: от сковородок до белья. Очень тихо ночью, спали как младенцы с открытой лоджией.",
                    "cons": "Парковка на придомовой территории платная, если на авто.",
                    "comment": "Чудесные апартаменты, фото соответствуют на все 100%. Хозяйка Елена на связи за 5 минут.",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Вид из окна захватывает дух, море прямо перед тобой"),
                        ("cleanliness", "positive", 0.99, "Чистейшая квартира, всё новое и свежее"),
                        ("noise_street", "positive", 0.95, "Очень тихо ночью, спали как младенцы"),
                    ]
                },
                {
                    "guest_id": "u_guest_sergey",
                    "created_at": "2026-08-04 18:20:00",
                    "rating_overall": 9.6,
                    "cleanliness": 10, "location": 9, "comfort": 10, "wifi": 10, "value": 9, "host": 10,
                    "pros": "Бесконтактный замок очень удобен, заселились глубокой ночью без звонков. Кофемашина с капсулами порадовала с утра.",
                    "cons": "До центра Сочи лучше ехать на такси или автобусе (минут 10).",
                    "comment": "Отличная локация, если хотите релакса и морского бриза.",
                    "aspects": [
                        ("checkin_ease", "positive", 1.0, "Бесконтактный замок удобен, заселились ночью без звонков"),
                        ("kitchen_amenities", "positive", 0.95, "Кофемашина с капсулами порадовала"),
                    ]
                },
                {
                    "guest_id": "u_guest_daria",
                    "created_at": "2026-07-19 16:40:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 10, "host": 10,
                    "pros": "Красивейший интерьер, стильная посуда и бокалы, вид на море незабываемый. Теплый пол в ванной.",
                    "cons": "Неделя пролетела слишком быстро.",
                    "comment": "Идеально для романтических выходных вдвоем.",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Вид на море незабываемый"),
                        ("cleanliness", "positive", 1.0, "Стильная чистая посуда, свежий ремонт"),
                    ]
                }
            ]
        },

        # --- 2. SOCHI NOISY CENTER (Yachts & Karaoke Bar) ---
        {
            "id": "prop_sochi_noisy_center",
            "host_id": "u_host_artyom",
            "title": "Апартаменты в центре у Морвокзала с боковым видом",
            "property_type": "apartment",
            "city": "Сочи",
            "district": "Центральный район",
            "address": "ул. Войкова, д. 3",
            "latitude": 43.58120,
            "longitude": 39.71980,
            "distance_to_center_km": 0.2,
            "distance_to_sea_m": 120,
            "distance_to_metro_m": None,
            "description": "Центр светской и клубной жизни Сочи. Набережная Морпорта, бутики, лучшие рестораны и ночные заведения прямо у входа в дом. С балкона открывается частичный вид на марину с яхтами. Дизайнерский ремонт в стиле модерн, барная стойка, кондиционер.",
            "instant_booking": 1,
            "deposit_amount": 3000.0,
            "cleaning_fee": 1000.0,
            "pets_allowed": 1,
            "smoking_allowed": 1,
            "parties_allowed": 0,
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "14:00",
            "check_out_to": "12:00",
            "amenities": [
                "sea_view", "balcony", "smart_tv", "air_conditioning", "kitchen_full",
                "refrigerator", "microwave", "washing_machine", "elevator", "parking"
            ],
            "photos": [
                ("https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85", "living_room", "Гостиная с барной стойкой и выходом на балкон", 1),
                ("https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80", "bedroom", "Спальня с двуспальной кроватью", 0),
                ("https://images.unsplash.com/photo-1507652313519-d4e9174996dd?auto=format&fit=crop&w=800&q=80", "bathroom", "Современный санузел", 0),
                ("https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=800&q=80", "balcony", "Вид с балкона на огни набережной", 0)
            ],
            "unit": {
                "id": "unit_sochi_noisy_center",
                "name": "Апартаменты у Морпорта",
                "total_area_sqm": 48.0,
                "floor": 3,
                "total_floors": 9,
                "has_elevator": 1,
                "max_guests": 3,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "Двуспальная кровать", "count": 1}, {"type": "Диван-кровать", "count": 1}]),
                "base_price_night": 7200.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_kate",
                    "created_at": "2026-09-28 10:10:00",
                    "rating_overall": 4.5,
                    "cleanliness": 7, "location": 9, "comfort": 3, "wifi": 4, "value": 4, "host": 5,
                    "pros": "Расположение топовое, до набережной 1 минута пешком. Кусочек моря с балкона действительно виден.",
                    "cons": "УЖАСНО шумно! Прямо под окнами караоке-бар и веранда ресторана. Басы долбят до 4-5 утра ежедневно, стеклопакеты не спасают вообще, вибрация по полу. Вай-фай постоянно обрывался, видеозвонки не тянет.",
                    "comment": "Если вы приехали тусить ночами — супер. Если спать или работать — обходите стороной.",
                    "aspects": [
                        ("sea_view", "positive", 0.7, "Кусочек моря с балкона между домами виден"),
                        ("noise_street", "negative", 1.0, "Ужасно шумно, басы караоке-бара долбят до 4 утра, спать невозможно"),
                        ("wifi_speed", "negative", 0.9, "Вай-фай постоянно обрывался, видеозвонки не тянет"),
                    ]
                },
                {
                    "guest_id": "u_guest_timur",
                    "created_at": "2026-08-14 19:40:00",
                    "rating_overall": 5.0,
                    "cleanliness": 8, "location": 9, "comfort": 4, "wifi": 5, "value": 5, "host": 6,
                    "pros": "Квартира красивая, все бары рядом, не надо брать такси после тусовок.",
                    "cons": "Очень шумно с улицы всю ночь. Заснуть получилось только под утро в берушах.",
                    "comment": "Для молодежных тусовок ок, для семейного отдыха точно нет.",
                    "aspects": [
                        ("noise_street", "negative", 0.95, "Очень шумно с улицы всю ночь, басы"),
                    ]
                },
                {
                    "guest_id": "u_guest_ivan",
                    "created_at": "2026-07-02 12:00:00",
                    "rating_overall": 5.5,
                    "cleanliness": 7, "location": 10, "comfort": 5, "wifi": 4, "value": 5, "host": 6,
                    "pros": "Всё в шаговой доступности: пляж Маяк, рестораны, порт.",
                    "cons": "Интернет нестабильный, для удаленки не годится. Громкая музыка с улицы.",
                    "comment": "Место шумное, учитывайте это при бронировании.",
                    "aspects": [
                        ("wifi_speed", "negative", 0.85, "Интернет нестабильный, для удаленки не годится"),
                        ("noise_street", "negative", 0.9, "Громкая музыка с улицы"),
                    ]
                }
            ]
        },

        # --- 3. SOCHI RIVIERA (FAKE SEA VIEW) ---
        {
            "id": "prop_sochi_fake_view",
            "host_id": "u_host_artyom",
            "title": "Уютная однушка «Морской Бриз» у парка Ривьера",
            "property_type": "apartment",
            "city": "Сочи",
            "district": "Центральный район",
            "address": "ул. Виноградная, д. 22",
            "latitude": 43.59540,
            "longitude": 39.71210,
            "distance_to_center_km": 1.1,
            "distance_to_sea_m": 450,
            "distance_to_metro_m": None,
            "description": "Квартира расположена в тихом зеленом районе рядом с парком Ривьера. 2 этаж, кондиционер, стиральная машина, стандартный набор посуды.",
            "instant_booking": 0,
            "deposit_amount": 2000.0,
            "cleaning_fee": 800.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "parties_allowed": 0,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "14:00",
            "check_out_to": "12:00",
            "amenities": ["air_conditioning", "kitchen_full", "refrigerator", "washing_machine", "kettle"],
            "photos": [
                ("https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=85", "living_room", "Комната с диваном и окном во двор", 1),
                ("https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=800&q=80", "kitchen", "Кухонная зона", 0),
                ("https://images.unsplash.com/photo-1620626011761-996317b8d101?auto=format&fit=crop&w=800&q=80", "bathroom", "Санузел", 0)
            ],
            "unit": {
                "id": "unit_sochi_fake_view",
                "name": "1-комнатная квартира",
                "total_area_sqm": 35.0,
                "floor": 2,
                "total_floors": 5,
                "has_elevator": 0,
                "max_guests": 2,
                "bedrooms_count": 1,
                "beds_count": 1,
                "beds_configuration": json.dumps([{"type": "Двуспальная кровать", "count": 1}]),
                "base_price_night": 3900.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_ivan",
                    "created_at": "2026-08-25 15:00:00",
                    "rating_overall": 5.5,
                    "cleanliness": 7, "location": 8, "comfort": 5, "wifi": 6, "value": 6, "host": 6,
                    "pros": "До парка Ривьера и пляжа близко, пешком 10 минут под горку.",
                    "cons": "Никакого вида на море нет! Из окон видна только серая стена гаражей и кусты. В описании обман. Матрас продавлен посередине, болела спина.",
                    "comment": "Обычная старая квартира, вид на море — маркетинг хозяина.",
                    "aspects": [
                        ("sea_view", "negative", 1.0, "Никакого вида на море нет, окна в стену гаражей"),
                        ("bed_comfort", "negative", 0.9, "Матрас продавлен посередине, болела спина"),
                    ]
                },
                {
                    "guest_id": "u_guest_marina",
                    "created_at": "2026-06-18 10:20:00",
                    "rating_overall": 6.0,
                    "cleanliness": 7, "location": 7, "comfort": 6, "wifi": 7, "value": 6, "host": 6,
                    "pros": "Недорого для сезона, горячая вода была без перебоев.",
                    "cons": "Моря из окна и близко не видно, окна выходят в глухую стену.",
                    "comment": "За свои деньги нормально, но не ждите красивых видов.",
                    "aspects": [
                        ("sea_view", "negative", 0.9, "Моря из окна не видно, вид в стену"),
                    ]
                }
            ]
        },

        # --- 4. SPB QUIET COURTYARD (REMOTE WORK HEAVEN) ---
        {
            "id": "prop_spb_quiet_courtyard",
            "host_id": "u_host_mikhail",
            "title": "Тихие видовые апартаменты с камином на набережной Фонтанки",
            "property_type": "apartment",
            "city": "Санкт-Петербург",
            "district": "Центральный район",
            "address": "наб. реки Фонтанки, д. 34",
            "latitude": 59.93428,
            "longitude": 30.34560,
            "distance_to_center_km": 0.8,
            "distance_to_sea_m": None,
            "distance_to_metro_m": 450,
            "description": "Исторический центр Санкт-Петербурга. Окна спальни выходят в закрытый зеленый питерский дворик-колодец: уличный шум, трафик и туристы не доходят совсем. Высота потолков 3.8 метра, аутентичный камин, толстые метровые кирпичные стены с исключительной звукоизоляцией. Оборудован рабочий кабинет с монитором 27 дюймов, эргономичным креслом и оптоволокном 500 Мбит/с. До Невского проспекта 7 минут пешком.",
            "instant_booking": 1,
            "deposit_amount": 5000.0,
            "cleaning_fee": 1500.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "parties_allowed": 0,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "14:00",
            "check_out_to": "12:00",
            "amenities": [
                "yard_view", "high_speed_wifi", "dedicated_workspace", "smart_tv",
                "soundproofing", "blackout_curtains", "floor_heating", "iron",
                "kitchen_full", "dishwasher", "refrigerator", "microwave", "coffee_machine", "kettle",
                "washing_machine", "hairdryer", "water_heater", "toiletries",
                "self_checkin", "cctv"
            ],
            "photos": [
                ("https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=85", "living_room", "Просторная гостиная с камином и высокими потолками", 1),
                ("https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=800&q=80", "bedroom", "Уютная спальня с видом в тихий двор-колодец", 0),
                ("https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80", "dedicated_workspace", "Рабочий кабинет с монитором и быстрым интернетом", 0),
                ("https://images.unsplash.com/photo-1556912172-45b7abe8b7e1?auto=format&fit=crop&w=800&q=80", "kitchen", "Кухня с техникой Bosch и кофемашиной", 0),
                ("https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?auto=format&fit=crop&w=800&q=80", "bathroom", "Просторная ванная комната", 0)
            ],
            "unit": {
                "id": "unit_spb_quiet_courtyard",
                "name": "Евродвушка с кабинетом на Фонтанке",
                "total_area_sqm": 60.0,
                "floor": 3,
                "total_floors": 4,
                "has_elevator": 0,
                "max_guests": 3,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "Кровать King-Size", "count": 1}, {"type": "Диван-кровать", "count": 1}]),
                "base_price_night": 5800.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_alex",
                    "created_at": "2026-10-10 17:00:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 10, "host": 10,
                    "pros": "Поразительно тихо для самого центра Питера! Окна во внутренний закрытый двор-колодец, ночью абсолютная тишина, даже птиц слышно. Шумоизоляция идеальная — соседей не слышали ни разу. Рабочий стол просто сказка, интернет 500 Мбит летал.",
                    "cons": "Нет лифта, но 3 этаж с пологими ступенями — не проблема.",
                    "comment": "Образец того, какими должны быть квартиры для путешественников и айтишников.",
                    "aspects": [
                        ("noise_street", "positive", 1.0, "Поразительно тихо для центра Питера, окна во внутренний закрытый двор"),
                        ("noise_neighbors", "positive", 0.95, "Шумоизоляция идеальная, соседей не слышали ни разу"),
                        ("wifi_speed", "positive", 1.0, "Интернет 500 Мбит летал, продуктивный ворккейшн"),
                        ("bed_comfort", "positive", 1.0, "Ортопедический матрас, спали глубоко и сладко"),
                        ("cleanliness", "positive", 1.0, "Безупречная чистота"),
                    ]
                },
                {
                    "guest_id": "u_guest_daria",
                    "created_at": "2026-09-03 13:20:00",
                    "rating_overall": 9.9,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 10, "host": 10,
                    "pros": "Волшебная атмосфера старого Петербурга, камин добавляет уюта прохладными вечерами. Очень чистое белье и полотенца.",
                    "cons": "Минусов нет совершенно.",
                    "comment": "Михаил встретил, помог с вещами, рассказал про лучшие кофейни рядом.",
                    "aspects": [
                        ("cleanliness", "positive", 1.0, "Очень чистое белье и полотенца"),
                        ("noise_street", "positive", 1.0, "Тихий дворик, никакой суеты"),
                    ]
                },
                {
                    "guest_id": "u_guest_sergey",
                    "created_at": "2026-07-28 09:45:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 9, "host": 10,
                    "pros": "Провел неделю в рабочей командировке. Монитор на столе — огромный плюс, спина не уставала.",
                    "cons": "Не заметил.",
                    "comment": "Лучший выбор для удаленной работы в СПб.",
                    "aspects": [
                        ("wifi_speed", "positive", 1.0, "Отличный интернет для созвонов"),
                        ("noise_street", "positive", 1.0, "Тишина полнейшая"),
                    ]
                }
            ]
        },

        # --- 5. SPB NOISY RUBINSTEIN (BAR STREET) ---
        {
            "id": "prop_spb_noisy_rubinstein",
            "host_id": "u_host_mikhail",
            "title": "Лофт на главной барной улице Рубинштейна",
            "property_type": "apartment",
            "city": "Санкт-Петербург",
            "district": "Центральный район",
            "address": "ул. Рубинштейна, д. 15",
            "latitude": 59.92980,
            "longitude": 30.34420,
            "distance_to_center_km": 1.2,
            "distance_to_sea_m": None,
            "distance_to_metro_m": 300,
            "description": "Стильный лофт с кирпичными стенами в эпицентре ресторанной и барной культуры Санкт-Петербурга. Окна выходят прямо на улицу Рубинштейна. Кондиционер, барная стойка, Bluetooth-колонка.",
            "instant_booking": 1,
            "deposit_amount": 3000.0,
            "cleaning_fee": 1200.0,
            "pets_allowed": 1,
            "smoking_allowed": 0,
            "parties_allowed": 1,
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "14:00",
            "check_out_to": "12:00",
            "amenities": ["balcony", "kitchen_full", "air_conditioning", "washing_machine", "refrigerator", "smart_tv"],
            "photos": [
                ("https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1200&q=85", "living_room", "Стильный лофт с кирпичной кладкой", 1),
                ("https://images.unsplash.com/photo-1540518614846-7ede433c4ef7?auto=format&fit=crop&w=800&q=80", "bedroom", "Спальная зона лофта", 0),
                ("https://images.unsplash.com/photo-1584622781564-1d987f7333c1?auto=format&fit=crop&w=800&q=80", "bathroom", "Санузел", 0)
            ],
            "unit": {
                "id": "unit_spb_noisy_rubinstein",
                "name": "Лофт на Рубинштейна",
                "total_area_sqm": 50.0,
                "floor": 2,
                "total_floors": 5,
                "has_elevator": 0,
                "max_guests": 4,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "Двуспальная кровать", "count": 1}, {"type": "Диван", "count": 1}]),
                "base_price_night": 6200.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_kate",
                    "created_at": "2026-09-18 11:00:00",
                    "rating_overall": 5.0,
                    "cleanliness": 8, "location": 10, "comfort": 4, "wifi": 8, "value": 5, "host": 7,
                    "pros": "Интерьер крутой, атмосфера города, все лучшие бары прямо под порогом.",
                    "cons": "Спать с пятницы по воскресенье невозможно вообще. Пьяные крики, песни, гитары и разборки прямо под окнами до 6 утра. Беруши не помогают, так как окна старинные деревянные без шумоизоляции.",
                    "comment": "Только для тусовщиков без претензий на сон.",
                    "aspects": [
                        ("noise_street", "negative", 1.0, "Спать невозможно, пьяные крики и песни под окнами до 6 утра"),
                    ]
                },
                {
                    "guest_id": "u_guest_timur",
                    "created_at": "2026-08-01 16:30:00",
                    "rating_overall": 5.8,
                    "cleanliness": 9, "location": 10, "comfort": 5, "wifi": 7, "value": 6, "host": 8,
                    "pros": "Шикарная тусовочная атмосфера, рядом десятки гастробаров.",
                    "cons": "Очень шумно по ночам, шум от дороги и людей.",
                    "comment": "Отличный лофт для уикенда с друзьями.",
                    "aspects": [
                        ("noise_street", "negative", 0.9, "Шумно по ночам от людей и баров"),
                    ]
                }
            ]
        },

        # --- 6. BALTIC ZEN SEA (ZELENOGRADSK) ---
        {
            "id": "prop_baltic_zen_sea",
            "host_id": "u_host_dmitry",
            "title": "Вилла-Апартаменты у первой линии Балтики в Зеленоградске",
            "property_type": "apartment",
            "city": "Зеленоградск",
            "district": "Побережье",
            "address": "ул. Гагарина, д. 41",
            "latitude": 54.96020,
            "longitude": 20.48510,
            "distance_to_center_km": 0.6,
            "distance_to_sea_m": 40,
            "distance_to_metro_m": None,
            "description": "Первая береговая линия Балтийского моря в тихой западной части курортного Зеленоградска. Из панорамного эркера и просторного балкона открывается фронтальный вид на песчаные дюны и набегающие волны. В радиусе километра нет ночных клубов и баров: слышен только целебный шум балтийского прибоя и соснового бора. Теплые полы во всей квартире, дизайнерская кухня, кофемашина Nespresso, скоростной интернет.",
            "instant_booking": 1,
            "deposit_amount": 5000.0,
            "cleaning_fee": 1500.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "parties_allowed": 0,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "14:00",
            "check_out_to": "12:00",
            "amenities": [
                "sea_view", "balcony", "high_speed_wifi", "dedicated_workspace", "smart_tv",
                "soundproofing", "floor_heating", "blackout_curtains", "iron",
                "kitchen_full", "dishwasher", "refrigerator", "microwave", "coffee_machine", "kettle",
                "washing_machine", "hairdryer", "water_heater", "toiletries",
                "self_checkin", "parking", "cctv"
            ],
            "photos": [
                ("https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?auto=format&fit=crop&w=1200&q=85", "view_window", "Балтийское море и песчаный пляж в 40 метрах от дома", 1),
                ("https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=800&q=80", "bedroom", "Спальня с видом на морские дюны", 0),
                ("https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=800&q=80", "living_room", "Гостиная с панорамным эркером", 0),
                ("https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&w=800&q=80", "kitchen", "Кухня с техникой и посудой", 0),
                ("https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=800&q=80", "bathroom", "Ванная комната с подогревом полов", 0)
            ],
            "unit": {
                "id": "unit_baltic_zen_sea",
                "name": "Апартаменты с видом на волны Балтики",
                "total_area_sqm": 55.0,
                "floor": 4,
                "total_floors": 5,
                "has_elevator": 1,
                "max_guests": 3,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "Кровать King-Size", "count": 1}, {"type": "Односпальная кровать", "count": 1}]),
                "base_price_night": 7900.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_olga",
                    "created_at": "2026-10-05 15:30:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 10, "host": 10,
                    "pros": "Невероятный вид на Балтийское море прямо с кровати! Море буквально в 40 метрах. Никаких клубов и толп, абсолютное спокойствие, засыпали под шум прибоя. В квартире тепло, полы с подогревом, на кухне есть вообще всё, даже специи и капсулы для кофе.",
                    "cons": "Не хотелось уезжать вообще никуда.",
                    "comment": "Эталон отдыха на Балтике. 10 из 10.",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Невероятный вид на Балтийское море прямо с кровати"),
                        ("noise_street", "positive", 1.0, "Никаких клубов и толп, абсолютное спокойствие, шум прибоя"),
                        ("kitchen_amenities", "positive", 1.0, "Полы с подогревом, специи, кофемашина, все до мелочей"),
                        ("cleanliness", "positive", 1.0, "Кристальная чистота"),
                        ("wifi_speed", "positive", 0.95, "Стабильный интернет, фильмы в 4K без задержек"),
                    ]
                },
                {
                    "guest_id": "u_guest_alex",
                    "created_at": "2026-09-12 18:00:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 10, "host": 10,
                    "pros": "Потрясающий воздух, шум прибоя, закаты прямо перед глазами. Дмитрий — идеальный хозяин.",
                    "cons": "Всё безупречно.",
                    "comment": "Обязательно приедем снова весной.",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Закаты на море прямо перед глазами"),
                        ("noise_street", "positive", 1.0, "Шум прибоя и тишина"),
                    ]
                },
                {
                    "guest_id": "u_guest_marina",
                    "created_at": "2026-08-20 12:40:00",
                    "rating_overall": 9.8,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 9, "value": 10, "host": 10,
                    "pros": "Очень уютная и продуманная квартира. Пляж широкий, чистый, сразу за калиткой.",
                    "cons": "В ветреную погоду прохладно на балконе, но внутри очень тепло.",
                    "comment": "Прекрасный отдых душой и телом.",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Пляж сразу за калиткой"),
                        ("cleanliness", "positive", 1.0, "Очень чистая и уютная"),
                    ]
                }
            ]
        },

        # --- 7. KRASNAYA POLYANA CHALET ---
        {
            "id": "prop_polyana_chalet_mountains",
            "host_id": "u_host_elena",
            "title": "Горное Шале с камином, сауной и панорамой Кавказских вершин",
            "property_type": "house",
            "city": "Красная Поляна",
            "district": "Эсто-Садок",
            "address": "ул. Защитников Кавказа, д. 77",
            "latitude": 43.68210,
            "longitude": 40.21040,
            "distance_to_center_km": 1.5,
            "distance_to_sea_m": 45000,
            "distance_to_metro_m": None,
            "description": "Просторное деревянное альпийское шале площадью 110 м² с дровяным камином, собственной финской сауной и открытой террасой с панорамным видом на Кавказский хребет Аибга. Закрытая охраняемая территория, реликтовый лес вокруг, мангальная зона со всеми принадлежностями.",
            "instant_booking": 1,
            "deposit_amount": 10000.0,
            "cleaning_fee": 3000.0,
            "pets_allowed": 1,
            "smoking_allowed": 0,
            "parties_allowed": 0,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "check_in_from": "15:00",
            "check_out_to": "12:00",
            "amenities": [
                "mountain_view", "balcony", "high_speed_wifi", "smart_tv", "soundproofing",
                "kitchen_full", "dishwasher", "refrigerator", "microwave", "coffee_machine", "kettle",
                "washing_machine", "hairdryer", "water_heater", "toiletries",
                "self_checkin", "parking", "cctv", "pets_allowed"
            ],
            "photos": [
                ("https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85", "exterior", "Деревянное шале с террасой на фоне заснеженных гор", 1),
                ("https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=800&q=80", "living_room", "Гостиная с дровяным камином и мягкими диванами", 0),
                ("https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80", "bedroom", "Мастер-спальня с панорамным окном на горы", 0),
                ("https://images.unsplash.com/photo-1584622781564-1d987f7333c1?auto=format&fit=crop&w=800&q=80", "bathroom", "Санузел и вход в сауну", 0),
                ("https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=800&q=80", "kitchen", "Кухня столовая на 6 персон", 0)
            ],
            "unit": {
                "id": "unit_polyana_chalet_mountains",
                "name": "Шале с сауной и камином целиком",
                "total_area_sqm": 110.0,
                "floor": 1,
                "total_floors": 2,
                "has_elevator": 0,
                "max_guests": 6,
                "bedrooms_count": 2,
                "beds_count": 4,
                "beds_configuration": json.dumps([{"type": "Кровать King-Size", "count": 2}, {"type": "Односпальная кровать", "count": 2}]),
                "base_price_night": 14500.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_ivan",
                    "created_at": "2026-10-18 20:00:00",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 9, "comfort": 10, "wifi": 9, "value": 9, "host": 10,
                    "pros": "Вид на горы потрясающий, камин топили каждый вечер. Воздух сладкий, тишина звенящая. Сауна в доме чистая и жаркая.",
                    "cons": "До подъемников нужно ехать 7 минут на такси.",
                    "comment": "Отличный отдых для перезагрузки от мегаполиса.",
                    "aspects": [
                        ("mountain_view", "positive", 1.0, "Вид на горы потрясающий, панорама вершин"),
                        ("noise_street", "positive", 1.0, "Тишина звенящая, реликтовый лес вокруг"),
                        ("cleanliness", "positive", 0.98, "Сауна в доме чистая, белье свежее"),
                    ]
                },
                {
                    "guest_id": "u_guest_daria",
                    "created_at": "2026-08-30 14:15:00",
                    "rating_overall": 9.8,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 9, "value": 9, "host": 10,
                    "pros": "Отдыхали большой семьей с детьми. Места много, посуды хватает на всех, терраса с видом на миллион.",
                    "cons": "Никаких замечаний.",
                    "comment": "Вернемся зимой на горнолыжный сезон!",
                    "aspects": [
                        ("mountain_view", "positive", 1.0, "Терраса с видом на миллион"),
                        ("cleanliness", "positive", 1.0, "Очень чисто и ухоженно"),
                    ]
                }
            ]
        }
    ]

    today = datetime.date.today()

    # 4. INSERT PROPERTIES, PHOTOS, REVIEWS AND SYNC REVIEW COUNTS
    for prop in properties_raw:
        # Initial insert
        cur.execute("""
            INSERT INTO properties (
                id, host_id, title, property_type, city, district, address, latitude, longitude,
                distance_to_center_km, distance_to_sea_m, distance_to_metro_m, description,
                instant_booking, deposit_amount, cleaning_fee, pets_allowed, smoking_allowed, parties_allowed,
                quiet_hours_start, quiet_hours_end, check_in_from, check_out_to,
                rating_total, reviews_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 0)
        """, (
            prop["id"], prop["host_id"], prop["title"], prop["property_type"], prop["city"],
            prop["district"], prop["address"], prop["latitude"], prop["longitude"],
            prop["distance_to_center_km"], prop["distance_to_sea_m"], prop["distance_to_metro_m"],
            prop["description"], prop["instant_booking"], prop["deposit_amount"],
            prop["cleaning_fee"], prop["pets_allowed"], prop["smoking_allowed"], prop["parties_allowed"],
            prop["quiet_hours_start"], prop["quiet_hours_end"], prop["check_in_from"], prop["check_out_to"]
        ))

        # Amenities
        amenities_str_list = []
        for code in prop["amenities"]:
            if code in amenity_id_map:
                cur.execute("INSERT OR IGNORE INTO property_amenities (property_id, amenity_id) VALUES (?, ?);",
                            (prop["id"], amenity_id_map[code]))
                amenities_str_list.append(code)

        # Unit
        u = prop["unit"]
        cur.execute("""
            INSERT INTO property_units (
                id, property_id, name, total_area_sqm, floor, total_floors, has_elevator,
                max_guests, bedrooms_count, beds_count, beds_configuration, base_price_night
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            u["id"], prop["id"], u["name"], u["total_area_sqm"], u["floor"], u["total_floors"], u["has_elevator"],
            u["max_guests"], u["bedrooms_count"], u["beds_count"], u["beds_configuration"], u["base_price_night"]
        ))

        # Photos
        for sort_idx, (photo_url, tag, caption, is_cov) in enumerate(prop["photos"]):
            cur.execute("""
                INSERT INTO property_photos (id, property_id, photo_url, tag, caption, is_cover, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), prop["id"], photo_url, tag, caption, is_cov, sort_idx))

        # Rate Plan
        cur.execute("""
            INSERT INTO rate_plans (id, property_id, title, cancellation_policy, discount_pct)
            VALUES (?, ?, 'Стандартный тариф (Бесплатная отмена за 48ч)', 'flexible_24h', 0.0)
        """, (str(uuid.uuid4()), prop["id"]))

        # Calendar generation for 60 days ahead
        for day_offset in range(60):
            cal_date = today + datetime.timedelta(days=day_offset)
            is_avail = 1
            reason = None
            if day_offset in (2, 3, 15, 16):
                is_avail = 0
                reason = "booking"

            cur.execute("""
                INSERT INTO unit_calendar (unit_id, date, price, is_available, unavailable_reason)
                VALUES (?, ?, ?, ?, ?)
            """, (u["id"], cal_date.isoformat(), u["base_price_night"], is_avail, reason))

        # Reviews & Aspects
        praised_aspects = []
        complaint_aspects = []
        sea_view_pos = 0
        noise_neg = 0
        wifi_pos = 0
        wifi_neg = 0

        for r in prop["reviews"]:
            booking_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO bookings (
                    id, unit_id, guest_id, check_in_date, check_out_date, nights_count, guests_count,
                    total_amount, prepayment_amount, platform_fee_amount, host_payout_amount, status
                ) VALUES (?, ?, ?, ?, ?, 3, 2, 15000, 3000, 2250, 12750, 'completed')
            """, (booking_id, u["id"], r["guest_id"], (today - datetime.timedelta(days=20)).isoformat(), (today - datetime.timedelta(days=17)).isoformat()))

            review_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO reviews (
                    id, booking_id, property_id, guest_id, rating_overall, rating_cleanliness,
                    rating_location, rating_comfort, rating_wifi, rating_value_for_money, rating_host,
                    pros_text, cons_text, general_comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, booking_id, prop["id"], r["guest_id"], r["rating_overall"],
                r["cleanliness"], r["location"], r["comfort"], r["wifi"], r["value"], r["host"],
                r["pros"], r["cons"], r["comment"], r.get("created_at", datetime.datetime.now().isoformat())
            ))

            for aspect_code, sentiment, conf, excerpt in r["aspects"]:
                cur.execute("""
                    INSERT INTO review_aspects (review_id, property_id, aspect_code, sentiment, confidence, excerpt)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (review_id, prop["id"], aspect_code, sentiment, conf, excerpt))

                if sentiment == "positive":
                    praised_aspects.append(f"{aspect_code}: {excerpt}")
                    if aspect_code == "sea_view":
                        sea_view_pos += 1
                    if aspect_code == "wifi_speed":
                        wifi_pos += 1
                elif sentiment == "negative":
                    complaint_aspects.append(f"{aspect_code}: {excerpt}")
                    if aspect_code in ("noise_street", "noise_neighbors"):
                        noise_neg += 1
                    if aspect_code == "wifi_speed":
                        wifi_neg += 1

        # Strict synchronization of reviews_count and rating_total with actual review rows!
        cur.execute("""
            UPDATE properties
            SET reviews_count = (SELECT COUNT(*) FROM reviews WHERE property_id = properties.id),
                rating_total = COALESCE((SELECT ROUND(AVG(rating_overall), 2) FROM reviews WHERE property_id = properties.id), 0.0)
            WHERE id = ?;
        """, (prop["id"],))

        # Sentiment summary
        has_verified_sea = 1 if sea_view_pos > 0 else 0
        cur.execute("""
            INSERT INTO property_sentiment_summary (
                property_id, has_verified_sea_view, sea_view_positive_count,
                noise_negative_count, wifi_positive_count, wifi_negative_count,
                top_praised_summary, top_complaints_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prop["id"], has_verified_sea, sea_view_pos, noise_neg, wifi_pos, wifi_neg,
            " | ".join(praised_aspects) if praised_aspects else "Нет данных",
            " | ".join(complaint_aspects) if complaint_aspects else "Жалоб нет"
        ))

        # Full Text Search virtual table populate
        cur.execute("""
            INSERT INTO property_search_fts (
                property_id, title, city, district, description, amenities_list, ai_praised, ai_complaints
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prop["id"], prop["title"], prop["city"], prop["district"], prop["description"],
            " ".join(amenities_str_list), " ".join(praised_aspects), " ".join(complaint_aspects)
        ))

    conn.commit()
    conn.close()
    print("Database seeded with full photos, avatars, and strictly synchronized reviews!")

if __name__ == "__main__":
    seed_database()
