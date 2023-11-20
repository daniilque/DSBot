from datetime import datetime, timedelta
import requests
import re
import db

def price(user_id):
    status = db.get_user_level(user_id)
    price = db.get_price(status)
    return price

def calculate_age(dob_str):
    today = datetime.today()
    dob = datetime.strptime(dob_str, "%d.%m.%Y")
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def extract_account_data(text):
    lines = text.split('\n')

    # Извлечение имени
    account_name_match = re.search(r'([А-Яа-яЁё]+\s[А-Яа-яЁё]+\s[А-Яа-яЁё]+)', lines[3], re.MULTILINE)
    account_name = account_name_match.group(1).strip() if account_name_match else None

    # Извлечение номера телефона
    phone_number_match = re.search(r'([87+9]\d[\d\s\(\)-]*)', lines[1], re.MULTILINE)
    phone_number = phone_number_match.group(1) if phone_number_match else None
    if phone_number:
        # Удаление всех пробелов, скобок и дефисов для стандартизации номера
        phone_number = re.sub(r'[\s\(\)-]', '', phone_number)

    # Извлечение гендера
    gender_match = re.search(r'\b(мужчина|мужской|м|парень|п)\b|\b(женщина|женский|ж|девушка|д)\b', lines[2], re.IGNORECASE)
    gender = "м" if gender_match and gender_match.group(1) else "ж" if gender_match and gender_match.group(2) else None

    # Извлечение даты рождения
    dob_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', lines[4])
    dob = dob_match.group(1) if dob_match else None
    age = calculate_age(dob) if dob else None

    return account_name, phone_number, gender, age

def generate_report_for_current(report_type: str, period: str) -> str:
    today = datetime.today()
    
    if period == "day":
        start_date = end_date = today.strftime('%Y-%m-%d')
    if period == "week":
        start_date = today - timedelta(days=today.weekday())  # Начало текущей недели (понедельник)
        end_date = start_date + timedelta(days=6)  # Конец текущей недели (воскресенье)
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')

    elif period == "month":
        start_date = datetime(today.year, today.month, 1).strftime('%Y-%m-%d')  # Первый день текущего месяца
        next_month = today.month % 12 + 1  # Следующий месяц
        year = today.year + today.month // 12  # Год следующего месяца
        end_date = (datetime(year, next_month, 1) - timedelta(days=1)).strftime('%Y-%m-%d')  # Последний день текущего месяца
    return db.generate_report(report_type, period, start_date, end_date)

def convert_date_format(date_str: str) -> str:
    """Преобразование даты из формата 'дд.мм.гг' в 'YYYY-MM-DD'."""
    day, month, year = map(int, date_str.split('.'))
    if year < 100:  # предположим, что годы меньше 100 относятся к 2000-м
        year += 2000
    return f"{year}-{month:02d}-{day:02d}"

def generate_report_by_dates(report_type: str, start_date_str: str, end_date_str: str, period: str) -> str:
    start_date = convert_date_format(start_date_str)
    end_date = convert_date_format(end_date_str)
    return db.generate_report(report_type, period, start_date, end_date)

def format_report_data(report_data, report_type):
    if not report_data:
        return "Данные отсутствуют за выбранный период."

    formatted_data = ["Отчет:"]
    for row in report_data:
        if report_type == 'sellers':
            key_name = 'seller_name'
        else:  # для 'buyers'
            key_name = 'booking_status'  # используем имя покупателя вместо booking_status

        formatted_data.append(f"{row[key_name]} ({row['period']}): {row['count']} аккаунтов")

    return "\n".join(formatted_data)

def is_valid_hash(hash):
    return len(hash) == 64  # Eсли ожидается хэш длиной 64 символа

def check_transaction(address, transaction_id_to_check, value_to_check):
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
    response = requests.get(url)
    
    if response.status_code != 200:
        return 0, None
    
    data = response.json()

    if 'data' not in data:
        return 0, None
    
    for transaction in data['data']:
        transaction_id = transaction.get('transaction_id', '')
        value = transaction.get('value', 0)
        
        # Преобразование значения из строки в число и деление на 10^6 (так как decimals = 6)
        value = int(value) / 1e6
        
        if transaction_id == transaction_id_to_check:
            if (value >= int(value_to_check) or value >= int(value_to_check) - 1):
                return 1, value
    else:
        return 0, None
    
def get_unique_names(filter_type):
    if filter_type == 'buyer':
        return db.get_unique_buyer_names()
    elif filter_type == 'seller':
        return db.get_unique_seller_names()
    else:
        return []
