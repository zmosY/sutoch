"""
Realistic Seed Dataset for Sutochno & Booking Clone
Populates Russian properties (Sochi, SPb, Zelenogradsk, Kazan, Krasnaya Polyana)
with real-world nuances: sea views, noise complaints, quiet yards, fast Wi-Fi, etc.
"""

import json
import uuid
import datetime
from src.db.schema_sqlite import get_connection, init_db

def seed_database():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    print("Clearing old data...")
    cur.execute("DELETE FROM ai_chat_messages;")
    cur.execute("DELETE FROM ai_chat_sessions;")
    cur.execute("DELETE FROM property_search_fts;")
    cur.execute("DELETE FROM property_sentiment_summary;")
    cur.execute("DELETE FROM review_aspects;")
    cur.execute("DELETE FROM reviews;")
    cur.execute("DELETE FROM bookings;")
    cur.execute("DELETE FROM unit_calendar;")
    cur.execute("DELETE FROM rate_plans;")
    cur.execute("DELETE FROM property_photos;")
    cur.execute("DELETE FROM property_amenities;")
    cur.execute("DELETE FROM amenities;")
    cur.execute("DELETE FROM property_units;")
    cur.execute("DELETE FROM properties;")
    cur.execute("DELETE FROM users;")

    # 1. AMENITIES
    amenities_data = [
        ("sea_view", "view", "Вид на море", "waves"),
        ("mountain_view", "view", "Вид на горы", "mountain"),
        ("yard_view", "view", "Вид в тихий двор", "trees"),
        ("balcony", "comfort", "Балкон / Лоджия", "balcony"),
        ("high_speed_wifi", "work", "Скоростной Wi-Fi (от 100 Мбит)", "wifi"),
        ("dedicated_workspace", "work", "Рабочее место с удобным креслом", "desk"),
        ("air_conditioning", "comfort", "Кондиционер", "snowflake"),
        ("soundproofing", "comfort", "Шумоизоляция", "shield"),
        ("kitchen_full", "kitchen", "Оборудованная кухня", "utensils"),
        ("dishwasher", "kitchen", "Посудомоечная машина", "dishwasher"),
        ("washing_machine", "comfort", "Стиральная машина", "washing_machine"),
        ("elevator", "building", "Лифт", "elevator"),
        ("parking", "comfort", "Бесплатная парковка", "car"),
        ("self_checkin", "comfort", "Бесконтактное заселение", "key"),
        ("pets_allowed", "rules", "Можно с питомцами", "paw"),
        ("baby_crib", "family", "Детская кроватка", "baby"),
    ]

    amenity_id_map = {}
    for code, cat, name, icon in amenities_data:
        cur.execute(
            "INSERT INTO amenities (code, category, name_ru, icon_name) VALUES (?, ?, ?, ?) RETURNING id;",
            (code, cat, name, icon)
        )
        row = cur.fetchone()
        amenity_id_map[code] = row[0]

    # 2. USERS (Hosts and Guests)
    users = [
        ("u_host_elena", "elena@sochirealty.ru", "+79180010011", "Елена", "Сочи Эксперт", "host", 1, 4.95, 98, 10),
        ("u_host_mikhail", "mikhail@spbrest.ru", "+79211112233", "Михаил", "Северная Столица", "host", 1, 4.88, 95, 20),
        ("u_host_dmitry", "dmitry@baltichome.ru", "+79062223344", "Дмитрий", "Балтик Вилла", "host", 1, 4.98, 100, 5),
        ("u_host_artyom", "artyom@partyrent.ru", "+79183334455", "Артём", "Центр Сочи Апарт", "host", 0, 4.20, 80, 60),
        ("u_host_anna", "anna@kazanlux.ru", "+79874445566", "Анна", "Казань Риэлти", "host", 1, 4.92, 99, 15),
        ("u_guest_olga", "olga.travel@yandex.ru", "+79998881122", "Ольга", "Смирнова", "guest", 0, 5.0, 100, 0),
        ("u_guest_alex", "alex.it@gmail.com", "+79998883344", "Александр", "Петров", "guest", 0, 5.0, 100, 0),
        ("u_guest_kate", "kate.novikova@mail.ru", "+79998885566", "Екатерина", "Новикова", "guest", 0, 5.0, 100, 0),
        ("u_guest_ivan", "ivan.nomad@ya.ru", "+79998887788", "Иван", "Волков", "guest", 0, 5.0, 100, 0),
    ]

    for uid, email, phone, fn, ln, role, ver, rating, resp_pct, resp_time in users:
        cur.execute("""
            INSERT INTO users (id, email, phone, first_name, last_name, role, is_verified_host, host_rating, response_rate_pct, response_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, email, phone, fn, ln, role, ver, rating, resp_pct, resp_time))

    # 3. PROPERTIES DATASET
    properties_raw = [
        {
            "id": "prop_sochi_panoramic_sea",
            "host_id": "u_host_elena",
            "title": "Панорамная студия у моря с балконом в ЖК «Морской Бриз»",
            "property_type": "apartment",
            "city": "Сочи",
            "district": "Хостинский район",
            "address": "ул. Курортный проспект, д. 108/6",
            "latitude": 43.56012,
            "longitude": 39.75489,
            "distance_to_center_km": 3.5,
            "distance_to_sea_m": 80,
            "distance_to_metro_m": None,
            "description": "Роскошная видовая студия на 16 этаже с прямым фронтальным видом на Черное море и закат. Просторный балкон со стеклянными ограждениями и шезлонгами. Тихое место, окна выходят прямо на море, трасса и железная дорога скрыты за домом. Оборудованное рабочее место, оптоволоконный интернет 200 Мбит/с. Идеально для пары или удаленной работы.",
            "instant_booking": 1,
            "deposit_amount": 5000.0,
            "cleaning_fee": 1500.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "rating_total": 4.96,
            "reviews_count": 28,
            "amenities": ["sea_view", "balcony", "high_speed_wifi", "dedicated_workspace", "air_conditioning", "soundproofing", "kitchen_full", "dishwasher", "washing_machine", "elevator", "self_checkin"],
            "unit": {
                "id": "unit_sochi_panoramic_sea",
                "name": "Студия Deluxe с панорамным видом на море",
                "total_area_sqm": 42.0,
                "floor": 16,
                "total_floors": 18,
                "max_guests": 2,
                "bedrooms_count": 1,
                "beds_count": 1,
                "beds_configuration": json.dumps([{"type": "king_size", "count": 1}]),
                "base_price_night": 6500.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_alex",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 9, "host": 10,
                    "pros": "Потрясающий прямой вид на море! Сидели на балконе каждый вечер и встречали закат. Шума от дороги вообще нет — дом стоит так, что окна смотрят на воду, слышен только прибой. Интернет 200 Мбит, проводил зум-колы на удаленке целыми днями без единого лага.",
                    "cons": "Лифт иногда приходится подождать 2-3 минуты в час пик.",
                    "comment": "Лучший опыт отдыха в Сочи. Вернемся обязательно!",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Потрясающий прямой вид на море, закат с балкона"),
                        ("noise_street", "positive", 0.98, "Шума от дороги вообще нет, слышен только легкий прибой"),
                        ("wifi_speed", "positive", 1.0, "Интернет 200 Мбит, зум-колы целыми днями без единого лага"),
                        ("bed_comfort", "positive", 0.95, "Огромная двуспальная кровать с мягким матрасом"),
                    ]
                },
                {
                    "guest_id": "u_guest_olga",
                    "rating_overall": 9.8,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 9, "host": 10,
                    "pros": "Вид из окна захватывает дух. Чистейшая квартира, всё новое: от сковородок до постельного белья. Очень тихо ночью, спали как младенцы.",
                    "cons": "Парковка во дворе платная, если на машине.",
                    "comment": "Чудесные апартаменты, фото соответствуют на 100%.",
                    "aspects": [
                        ("sea_view", "positive", 1.0, "Вид из окна захватывает дух, море прямо перед тобой"),
                        ("cleanliness", "positive", 0.99, "Чистейшая квартира, всё новое и свежее"),
                        ("noise_street", "positive", 0.95, "Очень тихо ночью, спали как младенцы"),
                    ]
                }
            ]
        },
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
            "description": "Эпицентр ночной жизни Сочи. Набережная, лучшие рестораны и клубы прямо у подъезда. С балкона видно яхты и кусочек моря. Дизайнерский ремонт, кондиционер, барная стойка.",
            "instant_booking": 1,
            "deposit_amount": 3000.0,
            "cleaning_fee": 1000.0,
            "pets_allowed": 1,
            "smoking_allowed": 1,
            "rating_total": 3.92,
            "reviews_count": 35,
            "amenities": ["sea_view", "balcony", "air_conditioning", "kitchen_full", "elevator"],
            "unit": {
                "id": "unit_sochi_noisy_center",
                "name": "Апартаменты с видом на Морпорт",
                "total_area_sqm": 48.0,
                "floor": 3,
                "total_floors": 9,
                "max_guests": 3,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "double_bed", "count": 1}, {"type": "sofa_bed", "count": 1}]),
                "base_price_night": 7200.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_kate",
                    "rating_overall": 5.0,
                    "cleanliness": 7, "location": 9, "comfort": 4, "wifi": 5, "value": 4, "host": 6,
                    "pros": "Расположение топовое, до набережной 1 минута пешком. Кусочек моря с балкона действительно виден.",
                    "cons": "УЖАСНО шумно! Прямо под окнами караоке-бар и веранда ресторана. Басы долбят до 4-5 утра ежедневно, стеклопакеты не спасают вообще, вибрация по полу. Вай-фай постоянно обрывался, видеозвонки не тянет.",
                    "comment": "Если вы приехали тусить ночами — супер. Если спать или работать — обходите стороной.",
                    "aspects": [
                        ("sea_view", "positive", 0.7, "Кусочек моря с балкона между домами виден"),
                        ("noise_street", "negative", 1.0, "Ужасно шумно, басы караоке-бара долбят до 4 утра, спать невозможно"),
                        ("wifi_speed", "negative", 0.9, "Вай-фай постоянно обрывался, видеозвонки не тянет"),
                    ]
                }
            ]
        },
        {
            "id": "prop_sochi_fake_view",
            "host_id": "u_host_artyom",
            "title": "Уютная однушка «Морской Бриз» у пляжа Ривьера",
            "property_type": "apartment",
            "city": "Сочи",
            "district": "Центральный район",
            "address": "ул. Виноградная, д. 22",
            "latitude": 43.59540,
            "longitude": 39.71210,
            "distance_to_center_km": 1.1,
            "distance_to_sea_m": 450,
            "distance_to_metro_m": None,
            "description": "Квартира рядом с парком Ривьера. В описании хозяин указал 'вид на море', но квартира находится на 2 этаже среди высоких кипарисов.",
            "instant_booking": 0,
            "deposit_amount": 2000.0,
            "cleaning_fee": 800.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "rating_total": 4.10,
            "reviews_count": 12,
            "amenities": ["air_conditioning", "kitchen_full", "washing_machine"],
            "unit": {
                "id": "unit_sochi_fake_view",
                "name": "1-комнатная квартира",
                "total_area_sqm": 35.0,
                "floor": 2,
                "total_floors": 5,
                "max_guests": 2,
                "bedrooms_count": 1,
                "beds_count": 1,
                "beds_configuration": json.dumps([{"type": "double_bed", "count": 1}]),
                "base_price_night": 3900.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_ivan",
                    "rating_overall": 6.0,
                    "cleanliness": 8, "location": 8, "comfort": 6, "wifi": 7, "value": 6, "host": 6,
                    "pros": "До парка Ривьера и пляжа близко, пешком 10 минут под горку.",
                    "cons": "Никакого вида на море нет! Из окон видна только серая стена гаражей и кусты. В описании обман. Матрас продавлен посередине, болела спина.",
                    "comment": "Обычная старая квартира, вид на море — маркетинг хозяина.",
                    "aspects": [
                        ("sea_view", "negative", 1.0, "Никакого вида на море нет, окна в стену гаражей"),
                        ("bed_comfort", "negative", 0.9, "Матрас продавлен посередине, болела спина"),
                    ]
                }
            ]
        },
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
            "description": "Исторический центр Петербурга. Спальня выходит в тишайший зелёный закрытый питерский дворик: никакой уличный шум и машины не доходят. Высокие потолки 3.8м, толстые кирпичные стены с идеальной звукоизоляцией. Выделенная рабочая зона с монитором и эргономичным креслом, интернет 500 Мбит/с. До Невского проспекта 7 минут пешком.",
            "instant_booking": 1,
            "deposit_amount": 5000.0,
            "cleaning_fee": 1500.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "rating_total": 4.97,
            "reviews_count": 42,
            "amenities": ["yard_view", "high_speed_wifi", "dedicated_workspace", "soundproofing", "kitchen_full", "dishwasher", "washing_machine", "self_checkin"],
            "unit": {
                "id": "unit_spb_quiet_courtyard",
                "name": "Просторная евродвушка с кабинетом",
                "total_area_sqm": 60.0,
                "floor": 3,
                "total_floors": 4,
                "max_guests": 3,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "king_size", "count": 1}, {"type": "sofa_bed", "count": 1}]),
                "base_price_night": 5800.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_alex",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 10, "value": 10, "host": 10,
                    "pros": "Поразительно тихо для самого центра Питера! Окна во внутренний двор-колодец, ночью абсолютная тишина, даже птиц слышно. Шумоизоляция идеальная — соседей не слышали ни разу. Рабочий стол просто сказка, интернет летал, провел 4 дня ворккешена с максимальной продуктивностью.",
                    "cons": "Нет лифта, но 3 этаж с пологими ступенями — не проблема.",
                    "comment": "Образец того, какими должны быть квартиры для путешественников и айтишников.",
                    "aspects": [
                        ("noise_street", "positive", 1.0, "Поразительно тихо для центра Питера, окна во внутренний закрытый двор"),
                        ("noise_neighbors", "positive", 0.95, "Шумоизоляция идеальная, соседей не слышали ни разу"),
                        ("wifi_speed", "positive", 1.0, "Интернет 500 Мбит летал, продуктивный ворккейшн"),
                        ("bed_comfort", "positive", 1.0, "Ортопедический матрас, спали глубоко и сладко"),
                        ("cleanliness", "positive", 1.0, "Безупречная чистота"),
                    ]
                }
            ]
        },
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
            "description": "Стильный лофт с кирпичными стенами в самом сердце барной культуры Санкт-Петербурга. Окна выходят прямо на улицу Рубинштейна.",
            "instant_booking": 1,
            "deposit_amount": 3000.0,
            "cleaning_fee": 1200.0,
            "pets_allowed": 1,
            "smoking_allowed": 0,
            "rating_total": 4.15,
            "reviews_count": 31,
            "amenities": ["balcony", "kitchen_full", "air_conditioning", "washing_machine"],
            "unit": {
                "id": "unit_spb_noisy_rubinstein",
                "name": "Лофт-апартаменты",
                "total_area_sqm": 50.0,
                "floor": 2,
                "total_floors": 5,
                "max_guests": 4,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "double_bed", "count": 1}, {"type": "sofa_bed", "count": 1}]),
                "base_price_night": 6200.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_kate",
                    "rating_overall": 6.0,
                    "cleanliness": 9, "location": 10, "comfort": 5, "wifi": 8, "value": 6, "host": 8,
                    "pros": "Интерьер крутой, атмосфера города, все бары прямо под порогом.",
                    "cons": "Спать с пятницы по воскресенье невозможно вообще. Пьяные крики, песни, гитары и разборки прямо под окнами до 6 утра. Беруши не помогают, так как окна старинные деревянные без шумоизоляции.",
                    "comment": "Только для тусовщиков без претензий на сон.",
                    "aspects": [
                        ("noise_street", "negative", 1.0, "Спать невозможно, пьяные крики и песни под окнами до 6 утра"),
                        ("noise_neighbors", "neutral", 0.7, "Соседей не слышно, но уличный шум заглушает всё"),
                    ]
                }
            ]
        },
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
            "description": "Первая береговая линия Балтийского моря! Панорамный эркер и балкон с прямым видом на песчаный пляж и волны. Тихий спальный район Зеленоградска без ночных заведений. Слышен только терапевтический шум прибоя и сосен. Теплый пол, посудомойка, кофемашина Nespresso, отличный интернет.",
            "instant_booking": 1,
            "deposit_amount": 5000.0,
            "cleaning_fee": 1500.0,
            "pets_allowed": 0,
            "smoking_allowed": 0,
            "rating_total": 4.99,
            "reviews_count": 39,
            "amenities": ["sea_view", "balcony", "high_speed_wifi", "dedicated_workspace", "soundproofing", "kitchen_full", "dishwasher", "washing_machine", "parking", "self_checkin"],
            "unit": {
                "id": "unit_baltic_zen_sea",
                "name": "Апартаменты с видом на волны Балтики",
                "total_area_sqm": 55.0,
                "floor": 4,
                "total_floors": 5,
                "max_guests": 3,
                "bedrooms_count": 1,
                "beds_count": 2,
                "beds_configuration": json.dumps([{"type": "king_size", "count": 1}, {"type": "single_bed", "count": 1}]),
                "base_price_night": 7900.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_olga",
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
                }
            ]
        },
        {
            "id": "prop_polyana_chalet_mountains",
            "host_id": "u_host_elena",
            "title": "Горное Шале с панорамным видом на Кавказские вершины",
            "property_type": "house",
            "city": "Красная Поляна",
            "district": "Эсто-Садок",
            "address": "ул. Защитников Кавказа, д. 77",
            "latitude": 43.68210,
            "longitude": 40.21040,
            "distance_to_center_km": 1.5,
            "distance_to_sea_m": 45000,
            "distance_to_metro_m": None,
            "description": "Уютное деревянное шале с террасой, сауной и панорамным видом на заснеженные горы Аибга. Настоящий камин на дровах, мангальная зона, закрытая частная территория. Вокруг реликтовый лес и полнейшая тишина.",
            "instant_booking": 1,
            "deposit_amount": 10000.0,
            "cleaning_fee": 3000.0,
            "pets_allowed": 1,
            "smoking_allowed": 0,
            "rating_total": 4.94,
            "reviews_count": 22,
            "amenities": ["mountain_view", "balcony", "high_speed_wifi", "soundproofing", "kitchen_full", "dishwasher", "parking", "self_checkin"],
            "unit": {
                "id": "unit_polyana_chalet_mountains",
                "name": "Шале с сауной и камином",
                "total_area_sqm": 110.0,
                "floor": 1,
                "total_floors": 2,
                "max_guests": 6,
                "bedrooms_count": 2,
                "beds_count": 4,
                "beds_configuration": json.dumps([{"type": "king_size", "count": 2}, {"type": "single_bed", "count": 2}]),
                "base_price_night": 14500.0
            },
            "reviews": [
                {
                    "guest_id": "u_guest_ivan",
                    "rating_overall": 10.0,
                    "cleanliness": 10, "location": 10, "comfort": 10, "wifi": 9, "value": 9, "host": 10,
                    "pros": "Вид на горы потрясающий, камин топили каждый вечер. Воздух сладкий, тишина звенящая. Сауна в доме чистая и жаркая.",
                    "cons": "До подъемников нужно ехать 7 минут на такси.",
                    "comment": "Отличный отдых для перезагрузки от мегаполиса.",
                    "aspects": [
                        ("mountain_view", "positive", 1.0, "Вид на горы потрясающий, панорама вершин"),
                        ("noise_street", "positive", 1.0, "Тишина звенящая, реликтовый лес вокруг"),
                        ("cleanliness", "positive", 0.98, "Сауна в доме чистая, белье свежее"),
                    ]
                }
            ]
        }
    ]

    # Insert Properties, Units, Amenities, Photos, Rate Plans, Calendar, Reviews & Aspects
    today = datetime.date.today()
    
    for prop in properties_raw:
        cur.execute("""
            INSERT INTO properties (
                id, host_id, title, property_type, city, district, address, latitude, longitude,
                distance_to_center_km, distance_to_sea_m, distance_to_metro_m, description,
                instant_booking, deposit_amount, cleaning_fee, pets_allowed, smoking_allowed,
                rating_total, reviews_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prop["id"], prop["host_id"], prop["title"], prop["property_type"], prop["city"],
            prop["district"], prop["address"], prop["latitude"], prop["longitude"],
            prop["distance_to_center_km"], prop["distance_to_sea_m"], prop["distance_to_metro_m"],
            prop["description"], prop["instant_booking"], prop["deposit_amount"],
            prop["cleaning_fee"], prop["pets_allowed"], prop["smoking_allowed"],
            prop["rating_total"], prop["reviews_count"]
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
                id, property_id, name, total_area_sqm, floor, total_floors,
                max_guests, bedrooms_count, beds_count, beds_configuration, base_price_night
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            u["id"], prop["id"], u["name"], u["total_area_sqm"], u["floor"], u["total_floors"],
            u["max_guests"], u["bedrooms_count"], u["beds_count"], u["beds_configuration"], u["base_price_night"]
        ))

        # Photos
        photo_map = {
            "prop_sochi_panoramic_sea": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
            "prop_sochi_noisy_center": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80",
            "prop_sochi_fake_view": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
            "prop_spb_quiet_courtyard": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80",
            "prop_spb_noisy_rubinstein": "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=800&q=80",
            "prop_baltic_zen_sea": "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?auto=format&fit=crop&w=800&q=80",
            "prop_polyana_chalet_mountains": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80"
        }
        chosen_photo = photo_map.get(prop["id"], f"https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80")
        cur.execute("""
            INSERT INTO property_photos (id, property_id, photo_url, tag, caption, is_cover)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (str(uuid.uuid4()), prop["id"], chosen_photo, "view_window", prop["title"]))

        # Rate Plan
        cur.execute("""
            INSERT INTO rate_plans (id, property_id, title, cancellation_policy, discount_pct)
            VALUES (?, ?, 'Стандартный тариф (Бесплатная отмена за 48ч)', 'flexible_24h', 0.0)
        """, (str(uuid.uuid4()), prop["id"]))

        # Calendar generation for 60 days ahead
        for day_offset in range(60):
            cal_date = today + datetime.timedelta(days=day_offset)
            # Make a few dates booked to simulate reality
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
            # create dummy booking for FK
            cur.execute("""
                INSERT INTO bookings (
                    id, unit_id, guest_id, check_in_date, check_out_date, nights_count, guests_count,
                    total_amount, prepayment_amount, platform_fee_amount, host_payout_amount, status
                ) VALUES (?, ?, ?, ?, ?, 3, 2, 15000, 3000, 2250, 12750, 'completed')
            """, (booking_id, u["id"], r["guest_id"], (today - datetime.timedelta(days=10)).isoformat(), (today - datetime.timedelta(days=7)).isoformat()))

            review_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO reviews (
                    id, booking_id, property_id, guest_id, rating_overall, rating_cleanliness,
                    rating_location, rating_comfort, rating_wifi, rating_value_for_money, rating_host,
                    pros_text, cons_text, general_comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, booking_id, prop["id"], r["guest_id"], r["rating_overall"],
                r["cleanliness"], r["location"], r["comfort"], r["wifi"], r["value"], r["host"],
                r["pros"], r["cons"], r["comment"]
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
                    if aspect_code == "noise_street" or aspect_code == "noise_neighbors":
                        noise_neg += 1
                    if aspect_code == "wifi_speed":
                        wifi_neg += 1

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
    print("Realistic dataset with 7 key properties, reviews and AI aspects successfully seeded!")

if __name__ == "__main__":
    seed_database()
