import sqlite3
from datetime import datetime

DATABASE_NAME = "accounts.db"

def connect_to_db():
    return sqlite3.connect(DATABASE_NAME, timeout=10)

def create_tables():
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_acc1 TEXT,
            photo_acc2 TEXT,
            photo_linked_acc TEXT,
            photo_qr_sim TEXT,
            form_data TEXT,
            gender TEXT,
            age INTEGER,
            seller_name TEXT,
            date DATETIME,
            booking_status TEXT DEFAULT "not booked",
            booking_date DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sold_accounts (
            id INTEGER PRIMARY KEY,
            photo_acc1 TEXT,
            photo_acc2 TEXT,
            photo_linked_acc TEXT,
            photo_qr_sim TEXT,
            form_data TEXT,
            gender TEXT,
            age INTEGER,
            seller_name TEXT,
            date DATETIME,
            sold_date DATETIME,
            booking_status TEXT,
            user_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_status (
            user_id INTEGER UNIQUE,
            status TEXT,
            start_time DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ban_ids (
            user_id INTEGER UNIQUE
        )
    """)   

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sellers_ids (
            user_id INTEGER UNIQUE,
            name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyers_ids (
            user_id INTEGER UNIQUE,
            name TEXT,
            cat TEXT DEFAULT "usual"
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            status TEXT UNIQUE,
            price INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyers_status (
            user_id INTEGER UNIQUE,
            status TEXT,
            gender TEXT,
            age TEXT,
            qty TEXT,
            av_qty TEXT,
            value TEXT
            
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            user_id INTEGER UNIQUE,
            hash TEXT,
            date DATETIME,
            value TEXT
            
        )
    """)

    conn.commit()
    conn.close()

def initialize_prices():
    conn = connect_to_db()
    cursor = conn.cursor()

    # Проверка, пуста ли таблица
    cursor.execute("SELECT COUNT(*) FROM prices")
    if cursor.fetchone()[0] == 0:
        # Вставка начальных данных, если таблица пуста
        prices = [('usual', 180), ('vip1', 160), ('vip2', 140)]
        cursor.executemany("INSERT INTO prices (status, price) VALUES (?, ?)", prices)
        conn.commit()

    conn.close()

def get_all_levels():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM prices")
    data = cursor.fetchall()  # Изменено на fetchall()
    conn.close()
    return [item[0] for item in data]

def get_user_level(user_id):
    conn = connect_to_db() 
    cursor = conn.cursor() 
    cursor.execute("SELECT cat FROM buyers_ids WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None

def get_all_users():
    conn = connect_to_db() 
    cursor = conn.cursor() 
    cursor.execute("SELECT user_id, name, cat FROM buyers_ids")
    data = cursor.fetchall()
    conn.close()
    return data

def get_price(status):
    conn = connect_to_db() 
    cursor = conn.cursor() 
    cursor.execute("SELECT price FROM prices WHERE status=?", (status,))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None  

def update_user_level(user_id, new_level):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE buyers_ids SET cat=? WHERE user_id=?", (new_level, user_id))
    conn.commit()
    conn.close()

def update_price(level, new_price):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE prices SET price=? WHERE status=?", (new_price, level))
    conn.commit()
    conn.close()  

def dict_factory(cursor, row):
    """Функция для преобразования результатов запроса в словари."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_unique_seller_names():
    conn = connect_to_db() 
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT seller_name
        FROM sold_accounts
        WHERE sold_date >= date('now', '-30 day') AND seller_name IS NOT NULL
    """)
    names = [row[0] for row in cursor.fetchall()]  # row[0], так как мы ожидаем один столбец
    conn.close()
    return names

def get_unique_buyer_names():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT booking_status AS buyer_name
        FROM sold_accounts
        WHERE sold_date >= date('now', '-30 day') AND booking_status IS NOT NULL
    """)
    names = [row[0] for row in cursor.fetchall()]  # row[0], так как мы ожидаем один столбец
    conn.close()
    return names

def get_filtered_sold_accounts(name, filter_type):
    conn = connect_to_db()
    conn.row_factory = dict_factory  # Устанавливаем фабрику словарей для соединения
    cursor = conn.cursor()
    if filter_type == 'buyer':
        cursor.execute("""
            SELECT * 
            FROM sold_accounts
            WHERE booking_status = ? AND sold_date >= date('now', '-30 day')
        """, (name,))
    elif filter_type == 'seller':
        cursor.execute("""
            SELECT * 
            FROM sold_accounts
            WHERE seller_name = ? AND sold_date >= date('now', '-30 day')
        """, (name,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def save_account_data(data):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (photo_acc1, photo_acc2, photo_linked_acc, photo_qr_sim, form_data, gender, age, date, seller_name) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['photo_acc1'], data['photo_acc2'], data['photo_linked_acc'], data['photo_qr_sim'], data['form_data'], data['gender'], data['age'], datetime.now(), data['seller_name']))
    conn.commit()
    conn.close()

def get_account_data():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM accounts ORDER BY id DESC LIMIT 1")
    data = cursor.fetchone()
    conn.close()
    
    return data

def get_data_buyer(user_id, qty):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Используем LIMIT для ограничения количества возвращаемых строк
    cursor.execute("SELECT * FROM accounts WHERE booking_status=? LIMIT ?", (user_id, qty))
    data = cursor.fetchmany(qty)  # Используем fetchmany для получения указанного количества строк
    conn.close()
    
    return data

def get_expired_bookings():
    conn = connect_to_db()
    cursor = conn.cursor()
    # Получаем записи с истекшим временем брони
    cursor.execute("""
        SELECT id, booking_status
        FROM accounts
        WHERE booking_date IS NOT NULL AND 
        (strftime('%s', 'now') - strftime('%s', booking_date)) > 35 * 60
    """)
    expired_bookings = cursor.fetchall()
    conn.close()
    return expired_bookings

def clear_expired_bookings(expired_ids):
    conn = connect_to_db()
    cursor = conn.cursor()
    # Очищаем booking_status и booking_date для истекших броней
    cursor.executemany("""
        UPDATE accounts
        SET booking_status = "not booked", booking_date = NULL
        WHERE id = ?
    """, [(e_id,) for e_id in expired_ids])  # Исправлено здесь
    conn.commit()
    conn.close()

def drop_booked_stats():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE accounts
        SET booking_status='not booked', booking_date=NULL
    """)
    data = cursor.fetchone()
    conn.commit()
    conn.close()

def get_all_accounts():
    conn = connect_to_db()
    conn.row_factory = dict_factory  # Установка функции преобразования строк в словари
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, form_data, seller_name FROM accounts ORDER BY id")
    data = cursor.fetchall()
    conn.close()
    
    return data

def get_all_sold_accounts():
    conn = connect_to_db()
    conn.row_factory = dict_factory  # Установка функции преобразования строк в словари
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, form_data, seller_name, booking_status FROM sold_accounts ORDER BY id")
    data = cursor.fetchall()
    conn.close()
    
    return data

def set_user_status(user_id, status, start_time=None):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    if start_time:
        cursor.execute("INSERT OR REPLACE INTO chat_status (user_id, status, start_time) VALUES (?, ?, ?)", (user_id, status, start_time))
    else:
        cursor.execute("INSERT OR REPLACE INTO chat_status (user_id, status) VALUES (?, ?)", (user_id, status))
    
    conn.commit()
    conn.close()

def get_user_status(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, start_time FROM chat_status WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    
    if data:
        return data
    return None, None

def get_active_user():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM chat_status WHERE status=?", ("loading_account",))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None

def get_next_in_queue():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM chat_status WHERE status=? LIMIT 1", ("in_queue",))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None

def reset_user_status(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM chat_status WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def move_to_sold_accounts(client_id, acc_id):
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Получаем имя клиента из таблицы buyers_ids по client_id
        cursor.execute("SELECT name FROM buyers_ids WHERE user_id=?", (client_id,))
        client_name = cursor.fetchone()
        if client_name:
            client_name = client_name[0]
        else:
            client_name = "Неизвестный"  # или любое другое значение по умолчанию

        # Получаем данные из таблицы accounts по ID
        cursor.execute("SELECT * FROM accounts WHERE id=?", (acc_id,))
        account_data = cursor.fetchone()

        if account_data:
            # Вставляем данные в таблицу sold_accounts
            cursor.execute("""
                INSERT INTO sold_accounts (id, photo_acc1, photo_acc2, photo_linked_acc, photo_qr_sim, form_data, gender, age, seller_name, date, sold_date, booking_status, user_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*account_data[:-2], datetime.now(), client_name, client_id))

            # Удаляем запись из таблицы accounts
            cursor.execute("DELETE FROM accounts WHERE id=?", (acc_id,))
        
        # Сохраняем изменения в базе данных
        conn.commit()

    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()  # Если произошла ошибка, отменяем изменения
    finally:
        conn.close()

def generate_report(report_type, period, start_date=None, end_date=None):
    if report_type not in ['sellers', 'buyers']:
        return []

    if period not in ['day', 'week', 'month']:
        return []

    if report_type == 'buyers':
        date_column = "sold_date"
        group_by_column = "booking_status" 
    elif report_type == 'sellers':
        date_column = "date"
        group_by_column = "seller_name"

    if period == "day":
        date_format = "%Y-%m-%d"
    elif period == "week":
        date_format = "%Y-%W"
    else:
        date_format = "%Y-%m"

    query = f"""
        SELECT {group_by_column}, strftime('{date_format}', {date_column}) as period, COUNT(*) as count
        FROM sold_accounts
    """
    
    if start_date and end_date:
        query += f" WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'"

    query += f"""
        GROUP BY {group_by_column}, period
        ORDER BY period DESC, count DESC;
    """

    conn = connect_to_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    return data

def add_user(user_id, name, type):
    conn = connect_to_db()
    cursor = conn.cursor()
    table_name = "sellers_ids" if type == "seller" else "buyers_ids"
    cursor.execute(f"INSERT INTO {table_name} (user_id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    conn.close()

def get_users_list(type):
    conn = connect_to_db()
    cursor = conn.cursor()
    table_name = "sellers_ids" if type == "seller" else ("ban_ids" if type == "ban" else "buyers_ids")
    cursor.execute(f"SELECT user_id FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return [item[0] for item in data]

def get_account_stats():
    conn = connect_to_db()
    cursor = conn.cursor()

    query = """
    SELECT gender, 
           SUM(CASE WHEN age < 18 AND booking_status = "not booked" THEN 1 ELSE 0 END) AS under_18, 
           SUM(CASE WHEN age >= 18 AND booking_status = "not booked" THEN 1 ELSE 0 END) AS over_18
    FROM accounts
    GROUP BY gender;
    """

    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    stats = {'М': {'under_18': 0, 'over_18': 0}, 'Ж': {'under_18': 0, 'over_18': 0}}
    for row in data:
        gender = row[0].upper() 
        stats[gender]['under_18'] = row[1]
        stats[gender]['over_18'] = row[2]

    return stats

def is_account_booked_by_user(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE booking_status=?", (user_id,))
    booked_count = cursor.fetchone()[0]
    conn.close()
    return booked_count > 0

def is_user_in_process(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM buyers_status WHERE user_id=?", (user_id,))
    any_thing = cursor.fetchone()[0]
    conn.close()
    return any_thing > 0

def initiate_buyer_status(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Установка начального статуса покупателя
    cursor.execute("""
        INSERT INTO buyers_status (user_id, status, gender, age, qty, value)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET status=excluded.status
    """, (user_id, 'initiated', None, None, None, None))
    
    conn.commit()
    conn.close()

def get_gender(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT gender FROM buyers_status WHERE user_id=?", (user_id,))
    gender = cursor.fetchone()
    
    conn.close()
    
    return gender[0] if gender else None

def is_hash_used(hash):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT date FROM payments WHERE hash=?", (hash,))
    date = cursor.fetchone()
    
    conn.close()
    return (True, date[0]) if date else (False, None)

def update_buyer_gender(user_id, gender):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE buyers_status SET gender=? WHERE user_id=?", (gender, user_id))
    conn.commit()
    conn.close()

def update_buyer_age(user_id, age):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE buyers_status SET age=? WHERE user_id=?", (age, user_id))
    conn.commit()
    conn.close()

def get_available_quantity(gender, age):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    if age == "<18":
        age_query = "age < 18"
    elif age == ">18":
        age_query = "age >= 18"
    else:
        age_query = ""  # Для случая "Любой"

    if gender in ["М", "Ж"]:
        gender_query = f"(gender = '{gender.upper()}' OR gender = '{gender.lower()}')"
    else:
        gender_query = ""  # Для случая "Любой"

    query = "SELECT COUNT(*) FROM accounts WHERE booking_status = 'not booked'"
    if age_query:
        query += f" AND {age_query}"
    if gender_query:
        query += f" AND {gender_query}"
    
    cursor.execute(query)
    available_qty = cursor.fetchone()[0]
    
    conn.close()
    return available_qty

def update_buyer_av_quantity(user_id, qty):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE buyers_status SET av_qty=? WHERE user_id=?", (qty, user_id))
    conn.commit()
    conn.close()

def get_buyer_av_quantity(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT av_qty FROM buyers_status WHERE user_id=?", (user_id,))
    av_q_data = cursor.fetchone()

    if not av_q_data:
        conn.close()
        return 0 # Если данные покупателя отсутствуют, завершаем функцию
    elif int(av_q_data[0]) <= 5:
        conn.close()
        return int(av_q_data[0])
    else: 
        conn.close()
        return 5

def update_buyer_quantity(user_id, qty):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE buyers_status SET qty=? WHERE user_id=?", (qty, user_id))
    conn.commit()
    conn.close()

def record_payment(user_id, payment_hash, value):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO payments (user_id, hash, date, value) VALUES (?, ?, datetime('now'), ?)", (user_id, payment_hash, value))
    conn.commit()
    conn.close()

def get_qty(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT qty FROM buyers_status WHERE user_id=?", (user_id,))
    buyer_data = cursor.fetchone()[0]
    conn.commit()
    conn.close()   
    return buyer_data

def book_accounts_for_user(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Получаем параметры возраста, пола и количество из buyers_status
    cursor.execute("SELECT gender, age, qty FROM buyers_status WHERE user_id=?", (user_id,))
    buyer_data = cursor.fetchone()
    
    if not buyer_data:
        conn.close()
        return  # Если данные покупателя отсутствуют, завершаем функцию

    gender, age, qty = buyer_data

    qty = int(qty)

    # Формируем условие выборки по полу и возрасту
    gender_condition = f"gender='{gender}'" if gender != 'ЛЮБОЙ ПОЛ' else "gender IN ('М', 'Ж')"
    age_condition = "age<18" if age == '<18' else ("age>=18" if age == '>18' else "age>=0")

    # Бронирование доступных аккаунтов с учетом пола и возраста
    cursor.execute(f"""
        UPDATE accounts 
        SET booking_status=?, booking_date=datetime('now') 
        WHERE id IN (
            SELECT id FROM accounts
            WHERE booking_status='not booked' AND {gender_condition} AND {age_condition}
            LIMIT ?
        )
    """, (user_id, qty))

    conn.commit()
    conn.close()

def clear_buyer_status(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buyers_status WHERE user_id=?", (user_id,))
    cursor.execute("DELETE FROM buyers_status WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_seller_name(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sellers_ids WHERE user_id=?", (user_id,))
    seller_name = cursor.fetchone()[0]
    
    conn.close()
    return seller_name

def get_buyer_name(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM buyers_ids WHERE user_id=?", (user_id,))
    seller_name = cursor.fetchone()[0]
    
    conn.close()
    return seller_name   

def ban_user(user_id, action):
    conn = connect_to_db()
    cursor = conn.cursor()

    if action == "ban":
        # Проверяем, есть ли уже пользователь в таблице ban_ids
        cursor.execute("SELECT * FROM ban_ids WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            # Если пользователя нет в таблице, добавляем его
            cursor.execute("INSERT INTO ban_ids (user_id) VALUES (?)", (user_id,))
        else:
            # Если пользователь уже в таблице, можно обновить информацию или просто оставить как есть
            pass
    elif action == "unban":
        # Удаляем пользователя из таблицы ban_ids
        cursor.execute("DELETE FROM ban_ids WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def get_account_by_id(user_id, role):
    conn = connect_to_db()
    conn.row_factory = dict_factory  # Применяем dict_factory для возврата результатов в виде словаря
    cursor = conn.cursor()
    
    if role == "buyer":
        cursor.execute("""
            SELECT id, form_data, sold_date
            FROM sold_accounts
            WHERE booking_status = (SELECT name FROM buyers_ids WHERE user_id = ?)
        """, (user_id,))
    elif role == "seller":
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', sold_date) as month, 
                COUNT(*) as count
            FROM sold_accounts
            WHERE seller_name = (SELECT name FROM sellers_ids WHERE user_id = ?)
            AND sold_date >= datetime('now', '-60 days')
            GROUP BY month
            ORDER BY month DESC
        """, (user_id,))
    else:
        conn.close()
        return None

    accounts = cursor.fetchall()
    conn.close()
    return accounts
