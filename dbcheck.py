import sqlite3
from datetime import datetime

DATABASE_NAME = "accounts.db"
table_names = ['accounts', 'sold_accounts', 'chat_status', 'ban_ids', 'sellers_ids', 'buyers_ids', 'prices', 'buyers_status', 'payments']  # Добавьте имена всех таблиц, которые вы хотите просмотреть

def connect_to_db():
    return sqlite3.connect(DATABASE_NAME)

def fetch_all_from_table(table_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data

def clear_table(table_name):
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()  # Если произошла ошибка, отменяем изменения
    finally:
        conn.close()

def add_to_accs():
    conn = connect_to_db()
    cursor = conn.cursor()
    # Данные для вставки
    data = (
        1,
        'AgACAgIAAxkBAAIHkGU697YQ6_r-KVJyKS47T4e7W4ciAALE1DEbmDbQSfEwPGhGrBAPAQADAgADeQADMAQ',
        'AgACAgIAAxkBAAIHkWU697ZYO3g2sPNreJk3Sbnb6bEbAALF1DEbmDbQSVUyo_qUgoNIAQADAgADeQADMAQ',
        'AgACAgIAAxkBAAIHkmU697aypsawxA1PT1SMkTzd32pOAALH1DEbmDbQSZxKaVR6XGNBAQADAgADeQADMAQ',
        'AgACAgIAAxkBAAIHk2U697bO_JjnUh-8a6diTnTbKVk7AAKFzDEbmDbYSZwq-nmpf_2KAQADAgADeQADMAQ',
        'Тинькофф: 2200 7009 2148 4100\n1 Привязан: 89018572295\n2 м - тут обязательны проверка, должно быть только м или ж\n3 Баталов Евгений Олегович\n4 14.07.2007 полных 16\n5 Закончил 9 классов 60 школы\n6 контактный: 89014312639\n7 Прописан: Мичурина 30\n8 Фактический:Авиаторов 1 \n9 перепревязывал карту 03.10.23\n10 первый раз стал клиентом 2022 году, курьер фоткал в машине\n11 Ранее заходил с IPhone xr\n12 кодовое: ручка\n13 пин:6228\n14 эл почта: a34606543@gmail.com\n15 Контрольные вопросы (если есть): нету\n16 Карта вывода: ВТБ:2200 2460 7258 2904',
        'М',
        16,
        'Daniiii',
        datetime.now(),
        'not booked',
        None
    )

    # SQL-запрос на вставку данных
    sql = '''
        INSERT INTO accounts (
            id,
            photo_acc1,
            photo_acc2,
            photo_linked_acc,
            photo_qr_sim,
            form_data,
            gender,
            age,
            seller_name,
            date,
            booking_status,
            booking_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    # Выполнение запроса
    cursor.execute(sql, data)

    # Фиксация изменений в базе данных
    conn.commit()

    # Закрытие соединения с базой данных
    conn.close()

def add_buyer():
    conn = connect_to_db()
    cursor = conn.cursor()
    # Данные для вставки
    data = (119485896, "Daniel")
    cursor.execute("INSERT INTO buyers_ids (user_id, name) VALUES (?, ?)", data)
    conn.commit()
    conn.close()

def update_booking_status_names():
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Получаем все записи из sold_accounts
        cursor.execute("SELECT id, booking_status FROM sold_accounts")
        sold_accounts = cursor.fetchall()

        # Обновляем booking_status для каждой записи
        for account in sold_accounts:
            account_id, client_id = account

            # Получаем имя клиента из таблицы buyers_ids по client_id
            cursor.execute("SELECT name FROM buyers_ids WHERE user_id=?", (client_id,))
            client_name = cursor.fetchone()
            if client_name:
                client_name = client_name[0]
            else:
                client_name = "Неизвестный"  # или любое другое значение по умолчанию

            # Обновляем booking_status в sold_accounts
            cursor.execute("UPDATE sold_accounts SET booking_status=? WHERE id=?", (client_name, account_id))

        # Сохраняем изменения в базе данных
        conn.commit()


    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()  # Если произошла ошибка, отменяем изменения
    finally:
        conn.close()

def by_id(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sellers_ids WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data    

def by_id(user_id_or_name, role):
    conn = connect_to_db()  # предполагается, что у вас есть функция для подключения к БД
    cursor = conn.cursor()
    
    if role == "buyer":
        # Предполагаем, что `user_id` хранится в таблице и используется для поиска купленных аккаунтов
        cursor.execute("""
            SELECT id, form_data, sold_date
            FROM sold_accounts
            WHERE booking_status = (SELECT name FROM buyers_ids WHERE user_id = ?) #ИСПРАВИТЬ НА ID В БУДУЩЕМ
        """, (user_id_or_name,))
    elif role == "seller":
        # Предполагаем, что `seller_name` используется для поиска проданных аккаунтов
        cursor.execute("""
            SELECT strftime('%Y-%m', sold_date) as month, COUNT(*) as count
            FROM sold_accounts
            WHERE seller_name = (SELECT name FROM sellers_ids WHERE user_id = ?)
            GROUP BY month
            ORDER BY month DESC
        """, (user_id_or_name,))
    else:
        conn.close()
        return None  # или поднимите исключение, если роль неподходящая
    
def delete_byid(id, table_name):
    # Проверяем, что имя таблицы безопасно
    if table_name not in table_names:
        raise ValueError(f"Недопустимое имя таблицы: {table_name}")

    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        # Используем параметризованный запрос для 'id'
        cursor.execute(f"DELETE FROM {table_name} WHERE hash = ?", (id,))
        conn.commit()
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    #add_to_accs()


    for table_name in table_names:
        print(f"===== {table_name.upper()} =====")
        rows = fetch_all_from_table(table_name)
        for row in rows:
            print(row)
        print("\n\n")

    delete_byid(input('Какой id записи удалить?'), "payments")
    #update_booking_status_names()
    
    clear_table(input('Какую таблицу очистить?\n'))


if __name__ == "__main__":
    main()
