from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# 1. Клавиатура после /rep
type_choice_kb = ReplyKeyboardMarkup(resize_keyboard=True)
type_choice_kb.add(KeyboardButton("По дроповодам"))
type_choice_kb.add(KeyboardButton("По покупателям"))

# 2. Клавиатура для выбора периода
period_choice_kb = ReplyKeyboardMarkup(resize_keyboard=True)
period_choice_kb.add(KeyboardButton("Месяц"))
period_choice_kb.add(KeyboardButton("Неделя"))
period_choice_kb.add(KeyboardButton("День"))

# 3. Клавиатура для выбора даты
date_choice_kb = ReplyKeyboardMarkup(resize_keyboard=True)
date_choice_kb.add(KeyboardButton("Указать даты"))
date_choice_kb.add(KeyboardButton("Текущий"))

# Клавиатура запроса
def confirm_level_kb(type, message_id, user_id):
    confirm_seller_kb = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Одобрить", callback_data=f"approve_{type}_{user_id}_{message_id}"), 
                InlineKeyboardButton("Отказать", callback_data=f"reject_{type}_{user_id}_{message_id}"))
    return confirm_seller_kb

# Клавиатура для админов
admin_kb = InlineKeyboardMarkup(resize_keyboard=True)
admin_kb.add(InlineKeyboardButton("Анкеты на продажу", callback_data="_accounts"))
admin_kb.add(InlineKeyboardButton("Проданные", callback_data="_sold"), 
             InlineKeyboardButton("Отчеты", callback_data="_rep"))
admin_kb.add(InlineKeyboardButton("Сбросить бронь", callback_data="_drop_booked"))
admin_kb.add(InlineKeyboardButton("Сменить ур. клиента", callback_data="_change_level"),
             InlineKeyboardButton("Сменить цены", callback_data="_change_prices"))

# Клавиатура для продавцов
seller_kb = InlineKeyboardMarkup(resize_keyboard=True)
seller_kb.add(InlineKeyboardButton("Добавить анкету", callback_data="_add_account"))
seller_kb.add(InlineKeyboardButton("Анкеты на продажу", callback_data="_accounts"))
seller_kb.add(InlineKeyboardButton("История продаж", callback_data="_history_seller"))

# Клавиатура для покупателей
user_kb = InlineKeyboardMarkup(resize_keyboard=True)
user_kb.add(InlineKeyboardButton("Купить аккаунт", callback_data="_buy"))
user_kb.add(InlineKeyboardButton("История покупок", callback_data="_history_user"))

# Клавиатура для обычных пользователей
newbie_kb = InlineKeyboardMarkup(resize_keyboard=True)
newbie_kb.add(InlineKeyboardButton("Запросить статус покупателя", callback_data="_user_request_buyer"))
newbie_kb.add(InlineKeyboardButton("Запросить статус продавца",  callback_data="_user_request_seller"))

# Клавиатура для выбора гендера
gender_kb = ReplyKeyboardMarkup(resize_keyboard=True)
gender_kb.add(KeyboardButton("М"))
gender_kb.add(KeyboardButton("Ж"))
gender_kb.add(KeyboardButton("Любой пол"))
gender_kb.add(KeyboardButton("Отмена"))

# Клавиатура для выбора возраста
age_kb = ReplyKeyboardMarkup(resize_keyboard=True)
age_kb.add(KeyboardButton("<18"))
age_kb.add(KeyboardButton(">18"))
age_kb.add(KeyboardButton("Любой возраст"))
age_kb.add(KeyboardButton("Отмена"))

# Клавиатура для выбора количества
def quantity_kb(available_qty):
    quantity_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, min(available_qty, 5) + 1):
        quantity_keyboard.add(KeyboardButton(str(i)))
    quantity_keyboard.add(KeyboardButton("Отмена"))
    return quantity_keyboard

# Клавиатура для подтверждения
confirm_kb = ReplyKeyboardMarkup(resize_keyboard=True)
confirm_kb.add(KeyboardButton("Подтвердить"))
confirm_kb.add(KeyboardButton("Отмена"))

cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_kb.add(KeyboardButton("Отмена"))

def create_names_keyboard(names, filter_type):
    keyboard = InlineKeyboardMarkup(row_width=1)  # Вы можете настроить количество кнопок в ряду
    if names:
        for name in names:
            callback_data = f"_select_name_{filter_type}_{name}"
            keyboard.add(InlineKeyboardButton(text=name, callback_data=callback_data))
        return keyboard
    else:
        return None

filter_choice_kb = InlineKeyboardMarkup(row_width=2)
filter_choice_kb.add(
    InlineKeyboardButton(text="По покупателю", callback_data='_by_buyer'),
    InlineKeyboardButton(text="По продавцу", callback_data='_by_seller')
)
