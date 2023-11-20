from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from datetime import datetime, timedelta
from typing import List
import keyboards
import asyncio
import classes
import tokens
import defs
import re
import db

TOKEN = tokens.TBotTokens[0]
db.create_tables()
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
group1 = []
group2 = []
eric = tokens.ids[0]
admin_id = [eric, tokens.ids[1]]
drop_id = db.get_users_list('seller')
buyer_id = db.get_users_list('buyer')
ban_id = db.get_users_list('ban')
WALLET_ADRESS = tokens.WALLETS[0]
admin_link = "t.me/united002765"
pending_requests = set()
media_groups = {}
empty_table_msg = "Таблица пуста"
no_rights = "У вас недостаточно прав для использования этой функции."
rep_msg = ["Выберите период отчета:", "Выберите произвольный период или используйте текущ"]

async def check_queue():
    while True:
        await asyncio.sleep(60)  # Проверка каждую минуту
        active_user = db.get_active_user()
        if active_user:
            status, start_time = db.get_user_status(active_user)
            if datetime.now() - datetime.fromisoformat(start_time) >= timedelta(minutes=5):
                await bot.send_message(active_user, "Время на загрузку истекло. Попробуйте снова")
                # Время истекло, начнем следующую загрузку из очереди
                next_user = db.get_next_in_queue()
                if next_user:
                    db.set_user_status(next_user, "loading_account", datetime.now())
                    await bot.send_message(next_user, "Загрузите анкету. У вас есть на это 5 минут.")
                db.reset_user_status(active_user)
        else:
            next_user = db.get_next_in_queue()
            if next_user:
                db.set_user_status(next_user, "loading_account", datetime.now())
                await bot.send_message(next_user, "Загрузите анкету. У вас есть на это 5 минут.")

async def check_booking():
    while True:
        await asyncio.sleep(300)
        print("proverka na booking")
        expired_bookings = db.get_expired_bookings()
        users_notified = set()  # Сет для отслеживания оповещенных пользователей
        expired_ids = [e_id for e_id, _ in expired_bookings]  # Получаем список идентификаторов
        if expired_ids:
            print(f"udalenie ob'ekta(ov) {expired_ids}")
            db.clear_expired_bookings(expired_ids)  # Очищаем истекшие бронирования
            for _, user_id in expired_bookings:
                if user_id not in users_notified:
                    await bot.send_message(user_id, "Ваша бронь аннулирована из-за истечения времени.")
                    users_notified.add(user_id)

async def on_startup(dp):
    #await bot.send_message(chat_id=eric, text="Бот запущен")
    asyncio.create_task(check_queue())
    asyncio.create_task(check_booking())

@dp.callback_query_handler(lambda message: message.from_user.id in ban_id)
async def ban_user(message: types.Message):
    await message.answer("Вы в черном списке")

@dp.callback_query_handler(lambda c: c.from_user.id in ban_id)
async def request_seller_command(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Вы в черном списке")

@dp.message_handler(commands=['start'])
async def show_appropriate_keyboard(message: types.Message):
    user_id = message.from_user.id
    reply_markup = None

    if user_id in ban_id:
        await message.answer("Вы в черном списке")
        return
    elif user_id in admin_id:
        reply_markup = keyboards.admin_kb
    elif user_id in buyer_id:
        reply_markup = keyboards.user_kb
    elif user_id in drop_id:
        reply_markup = keyboards.seller_kb
    else:
        reply_markup = keyboards.newbie_kb

    await message.answer("Выберите действие:", reply_markup=reply_markup)

@dp.message_handler(lambda message: (message.text.startswith('/ban') or message.text.startswith('/unban')) and message.from_user.id in admin_id)
async def ban_unban_user(message: types.Message):
    parts = message.text.split(" ")
    if len(parts) != 2:
        await message.answer("Пожалуйста, укажите команду и ID пользователя (например, /ban 12345).")
        return

    command, user_id_str = parts
    try:
        user_id = int(user_id_str)  # Преобразовываем ID пользователя в число
    except ValueError:
        await message.answer("ID пользователя должен быть числом.")
        return

    msg = "оставлен без изменений"
    if command == '/ban':
        if user_id not in ban_id: 
            db.ban_user(user_id, "ban")
            ban_id.append(user_id)
            msg = "заблокирован"
    elif command == '/unban':
        if user_id in ban_id: 
            db.ban_user(user_id, "unban") 
            ban_id.remove(user_id)
            msg = "разблокирован"
        else:
            msg = "не найден в списке заблокированных"
    await message.answer(f"Пользователь {user_id} {msg}")
                      
@dp.callback_query_handler(lambda c: c.data.startswith('_user_request'))
async def request_seller_command(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username

    user_type = "продавца" if callback_query.data.endswith('_seller') else "покупателя"
    key_type = "seller" if callback_query.data.endswith('_seller') else "buyer"

    if user_id in pending_requests:
        await callback_query.message.answer("Вы уже отправили запрос. Пожалуйста, дождитесь ответа.")
        await callback_query.answer()
        return

    if user_id not in drop_id:
        # Добавляем user_id в набор ожидающих запросов
        pending_requests.add(user_id)

        # Сначала отправьте сообщение
        sent_message = await bot.send_message(eric, f"Запрос на {user_type} от @{username} (ID: {user_id})")
        
        # Затем используйте message_id в reply_markup
        await bot.edit_message_reply_markup(chat_id=eric, message_id=sent_message.message_id,
                                            reply_markup=keyboards.confirm_level_kb(key_type, sent_message.message_id, user_id))
    else:
        await callback_query.message.answer(f"Вы уже являетесь {user_type}.")
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('approve_seller_') or c.data.startswith('approve_buyer_'))
async def approve_request(callback_query: types.CallbackQuery):
    user_id, message_id = map(int, callback_query.data.split('_')[2:4])
    user_type = "продавца" if "seller" in callback_query.data else "покупателя"
    await callback_query.answer(f"Запрос на {user_type} одобрен. Введите имя {user_type}.")

    # Определяем состояние в зависимости от типа пользователя
    state_type = classes.ReportState.UserName
    state = dp.current_state(user=callback_query.from_user.id)
    await state.set_state(state_type)
    async with state.proxy() as data:
        data['user_id'] = user_id
        data['type'] = "seller" if "seller" in callback_query.data else "buyer"
        await bot.delete_message(chat_id=eric, message_id=message_id)

@dp.message_handler(lambda message: message.chat.type in ['private'],
                    state=classes.ReportState.UserName)
async def process_user_name(message: types.Message, state: FSMContext):
    global drop_id, buyer_id
    async with state.proxy() as data:
        user_id = data['user_id']
        user_name = message.text
        user_type = data['type']

        db.add_user(user_id, user_name, user_type)  # Используйте обновленную функцию
        drop_id = db.get_users_list('seller')
        buyer_id = db.get_users_list('buyer')   

        reply_text = "Продавец успешно добавлен." if user_type == "seller" else "Покупатель успешно добавлен."
        user_type_txt = "продавец" if user_type == "seller" else "покупатель"
        reply_kb = keyboards.seller_kb if user_type == "seller" else keyboards.user_kb
        await message.reply(reply_text)
        await bot.send_message(user_id, f"Вы теперь {user_type_txt}!", reply_markup=reply_kb)

    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('reject_'))
async def reject_request(callback_query: types.CallbackQuery):
    user_id, message_id = map(int, callback_query.data.split('_')[2:4])
    await callback_query.answer("Запрос отклонен.")
    await bot.send_message(callback_query.from_user.id, "Запрос отклонен.")
    await bot.send_message(user_id, "Вам отказано.")
    await bot.delete_message(chat_id=eric, message_id=message_id)

@dp.callback_query_handler(lambda c: c.data.startswith('_add_account'))
async def start_loading(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in drop_id:

        # Проверяем, есть ли активные загрузки
        active_user = db.get_active_user()
        if active_user:  # Если есть активная загрузка
            if active_user == user_id:
                await callback_query.message.answer("Сейчас уже ваша очередь!")
            else:
                # Помещаем текущего пользователя в очередь
                db.set_user_status(user_id, "in_queue")
                await callback_query.message.answer("Другой пользователь сейчас загружает анкету. Пожалуйста, подождите.")
        else:
            # Начинаем процесс загрузки для текущего пользователя
            db.set_user_status(user_id, "loading_account", datetime.now().isoformat())
            await callback_query.message.answer("Загрузите анкету. У вас есть на это 10 минут.")
    else:
        await callback_query.message.answer(no_rights)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == '_history_user')
async def send_all(callback_query: types.CallbackQuery):
    # Получение user_id из информации о пользователе Telegram
    user_id = callback_query.from_user.id
    user_history = db.get_account_by_id(user_id, "buyer")  # Эта функция должна использовать user_id для запроса
    if user_history:
        response_text = "\n\n".join([f"ID заказа: {row['id']}\nФИО: {defs.extract_account_data(row['form_data'])[0]}\nДата покупки: {row['sold_date']}" for row in user_history])
    else:
        response_text = "Ничего не найдено"
    await callback_query.message.answer(response_text, reply_markup=keyboards.user_kb)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == '_history_seller')
async def send_all(callback_query: types.CallbackQuery):
    # Получение имени продавца из контекста или каким-либо другим способом
    seller_name = callback_query.from_user.id  # или другой идентификатор, если username не используется для имен продавцов
    seller_history = db.get_account_by_id(seller_name, "seller")  # Эта функция должна использовать имя продавца для запроса
    if seller_history:
        response_text = "\n".join([f"{row['month']} – {row['count']} аккаунт(ов)" for row in seller_history])
    else:
        response_text = "Ничего не найдено"
    await callback_query.message.answer(response_text, reply_markup=keyboards.seller_kb)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == '_accounts' and (c.from_user.id in admin_id or c.from_user.id in drop_id))
async def send_all(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Аккаунты на продажу:")
    all_accounts = db.get_all_accounts()

    if not all_accounts:
        await callback_query.message.answer(empty_table_msg)
        return
    await callback_query.message.answer("==================")
    for account in all_accounts:
        account_name, phone_number, gender, age = defs.extract_account_data(account['form_data'])
        seller_name = account['seller_name']
        user_id = callback_query.from_user.id
        if user_id in drop_id:
            if seller_name == db.get_seller_name(user_id):
                response_text = f"Имя: {account_name}\nВозраст: {age}, Пол: {gender.upper()}\nНомер: {phone_number}\nПродавец: {seller_name}"
                await callback_query.message.answer(response_text)
            reply_markup=keyboards.seller_kb
        else:
            response_text = f"Имя: {account_name}\nВозраст: {age}, Пол: {gender.upper()}\nНомер: {phone_number}\nПродавец: {seller_name}"
            await callback_query.message.answer(response_text)
            reply_markup=keyboards.admin_kb
    await callback_query.message.answer("==================", reply_markup=reply_markup)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == '_sold' and c.from_user.id in admin_id)
async def send_sold(callback_query: types.CallbackQuery):
    await classes.SoldAccountsState.FilterType.set()
    await callback_query.message.answer("Выберите тип отбора:", reply_markup=keyboards.filter_choice_kb)

@dp.callback_query_handler(lambda c: c.data in ['_by_buyer', '_by_seller'] and c.from_user.id in admin_id, state=classes.SoldAccountsState.FilterType)
async def select_filter_type(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type = 'buyer' if callback_query.data == '_by_buyer' else 'seller'
    names = defs.get_unique_names(filter_type)
    await classes.SoldAccountsState.SelectName.set()
    await state.update_data(filter_type=filter_type)
    reply_markup = keyboards.create_names_keyboard(names, filter_type)
    if reply_markup == None:
       await callback_query.message.answer("Пользователей нет", reply_markup=keyboards.admin_kb)
       await state.finish() 
    else:
        await callback_query.message.answer("Выберите имя:", reply_markup=reply_markup)

@dp.callback_query_handler(lambda c: c.data.startswith('_select_name_') and c.from_user.id in admin_id, state=classes.SoldAccountsState.SelectName)
async def select_name(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    filter_type = user_data.get('filter_type')
    # Исправленное разделение callback_data для получения имени, предполагая что имя состоит из одной части
    parts = callback_query.data.split('_')
    # Соединяем все части после 'name', 'buyer' или 'seller', которые составляют имя
    name = '_'.join(parts[4:])
    sold_accounts = db.get_filtered_sold_accounts(name, filter_type)
    await callback_query.message.answer("==================")
    for account in sold_accounts:
        account_name, phone_number, gender, age = defs.extract_account_data(account['form_data'])
        seller_name = account['seller_name']
        buyer_name = account['booking_status']
        response_text = f"Имя: {account_name}\nВозраст: {age}, Пол: {gender.upper()}\nНомер: {phone_number}\nПродавец: {seller_name}\nПокупатель: {buyer_name}"
        await callback_query.message.answer(response_text)
    await callback_query.message.answer("==================", reply_markup=keyboards.admin_kb)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == '_sold' and c.from_user.id in admin_id)
async def send_sold(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Проданные аккаунты:")
    all_sold_accounts = db.get_all_sold_accounts()
    if not all_sold_accounts:
        await callback_query.message.answer(empty_table_msg)
    for account in all_sold_accounts:
        account_name, phone_number, gender, age = defs.extract_account_data(account['form_data'])
        seller_name = account['seller_name']
        response_text = f"Имя: {account_name}\nВозраст: {age}, Пол: {gender.upper()}\nНомер: {phone_number}\nПродавец: {seller_name}"
        await callback_query.message.answer(response_text)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('_rep'))
async def handle_rep_command(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in admin_id:
        await callback_query.message.answer("Выберите тип отчета:", reply_markup=keyboards.type_choice_kb)
    else:
        await callback_query.message.answer(no_rights)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == '_change_level' and c.from_user.id in admin_id)
async def handle_change_level(callback_query: types.CallbackQuery):
    users = db.get_all_users()
    markup = InlineKeyboardMarkup()
    for user in users:
        user_id, name, level = user
        button_text = f"{name} (ID: {user_id}, Уровень: {level})"
        markup.add(InlineKeyboardButton(button_text, callback_data=f"user_{user_id}"))
    await bot.send_message(callback_query.from_user.id, "Выберите пользователя для изменения уровня:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('user_'))
async def select_user_level(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[1]
    levels = db.get_all_levels()
    markup = InlineKeyboardMarkup()
    for level in levels:
        markup.add(InlineKeyboardButton(level, callback_data=f"level_{user_id}_{level}"))
    await bot.send_message(callback_query.from_user.id, "Выберите новый уровень пользователя:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('level_'))
async def set_new_user_level(callback_query: types.CallbackQuery):
    user_id, new_level = callback_query.data.split('_')[1:]
    db.update_user_level(user_id, new_level)
    await bot.send_message(callback_query.from_user.id, f"Уровень пользователя {user_id} изменен на {new_level}")

@dp.callback_query_handler(lambda c: c.data == '_change_prices' and c.from_user.id in admin_id)
async def handle_change_prices(callback_query: types.CallbackQuery):
    levels = db.get_all_levels()
    markup = InlineKeyboardMarkup()
    for level in levels:
        price = db.get_price(level)
        button_text = f"{level} - Цена: {price}"
        markup.add(InlineKeyboardButton(button_text, callback_data=f"price_{level}"))
    await bot.send_message(callback_query.from_user.id, "Выберите статус для изменения цены:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('price_'))
async def request_new_price(callback_query: types.CallbackQuery, state: FSMContext):
    level = callback_query.data.split('_')[1]
    await classes.UpdatePriceState.WaitingForNewPrice.set()
    await state.update_data(level=level)
    await bot.send_message(callback_query.from_user.id, f"Введите новую цену для уровня {level}")

@dp.message_handler(state=classes.UpdatePriceState.WaitingForNewPrice)
async def set_new_price(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    level = user_data['level']
    new_price = message.text
    try:
        new_price = int(new_price)
        db.update_price(level, new_price)
        await bot.send_message(message.from_user.id, f"Цена для уровня {level} обновлена до {new_price}")
    except ValueError:
        await bot.send_message(message.from_user.id, "Пожалуйста, введите числовое значение для цены.")
    await state.finish()

@dp.message_handler(lambda message: message.text == "По дроповодам" and message.from_user.id in admin_id, state=None)
async def handle_dropovods_choice(message: types.Message, state: FSMContext):
    await classes.ReportState.Type.set()  # Устанавливаем состояние Type
    await state.update_data(report_type="sellers")
    await message.answer(rep_msg[0], reply_markup=keyboards.period_choice_kb)

@dp.message_handler(lambda message: message.text == "По покупателям" and message.from_user.id in admin_id, state=None)
async def handle_customers_choice(message: types.Message, state: FSMContext):
    await classes.ReportState.Type.set()  # Устанавливаем состояние Type
    await state.update_data(report_type="buyers")
    await message.answer(rep_msg[0], reply_markup=keyboards.period_choice_kb)

@dp.message_handler(lambda message: message.text == "Месяц" and message.from_user.id in admin_id, state=classes.ReportState.Type)
async def handle_month_choice(message: types.Message, state: FSMContext):
    await classes.ReportState.Period.set()  # Устанавливаем состояние Period
    await state.update_data(period="month")  # Сохраняем выбранный период в FSMContext
    await message.answer(f"{rep_msg[1]}ий месяц:", reply_markup=keyboards.date_choice_kb)

@dp.message_handler(lambda message: message.text == "Неделя" and message.from_user.id in admin_id, state=classes.ReportState.Type)
async def handle_week_choice(message: types.Message, state: FSMContext):
    await classes.ReportState.Period.set()
    await state.update_data(period="week")
    await message.answer(f"{rep_msg[1]}ую неделю:", reply_markup=keyboards.date_choice_kb)

@dp.message_handler(lambda message: message.text == "День" and message.from_user.id in admin_id, state=classes.ReportState.Type)
async def handle_day_choice(message: types.Message, state: FSMContext):
    await classes.ReportState.Period.set()
    await state.update_data(period="day")
    await message.answer(f"{rep_msg[1]}ий день:", reply_markup=keyboards.date_choice_kb)

@dp.message_handler(lambda message: message.text == "Текущий" and message.from_user.id in admin_id, state=classes.ReportState.Period)
async def handle_current_choice(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    report_type = user_data.get("report_type")
    period = user_data.get("period")
    
    report_data = defs.generate_report_for_current(report_type, period)
    
    # Здесь вы можете форматировать report_data в строку и отправлять ее пользователю
    await message.answer(defs.format_report_data(report_data, report_type), reply_markup=keyboards.admin_kb)
    
    await state.finish()

@dp.message_handler(lambda message: message.text == "Указать даты" and message.from_user.id in admin_id, state=classes.ReportState.Period)
async def handle_date_choice(message: types.Message, state: FSMContext):
    await classes.ReportState.Date.set()
    await message.answer("Введите даты в формате дд.мм.гг - дд.мм.гг", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: re.match(r"\d{2}.\d{2}.\d{2} - \d{2}.\d{2}.\d{2}", message.text) and message.from_user.id in admin_id, state=classes.ReportState.Date)
async def handle_date_input(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    report_type = user_data.get("report_type")
    start_date_str, end_date_str = message.text.split(" - ")
    period = user_data.get("period")
    
    report_data = defs.generate_report_by_dates(report_type, start_date_str, end_date_str, period)
    
    # Здесь вы можете форматировать report_data в строку и отправлять ее пользователю
    await message.answer(defs.format_report_data(report_data, report_type), reply_markup=keyboards.admin_kb)
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('_drop_booked'))
async def handle_clear_command(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in admin_id:
        db.drop_booked_stats()
    else:
        await callback_query.message.answer(no_rights)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('_buy'))
async def handle_buy_command(callback_query: types.CallbackQuery):
    stats = db.get_account_stats()
    
    await callback_query.message.answer(f"""👥 Доступные анкеты:
    М до 18 лет: {stats['М']['under_18']}
    М старше 18 лет: {stats['М']['over_18']}
    Ж до 18 лет: {stats['Ж']['under_18']}
    Ж старше 18 лет: {stats['Ж']['over_18']}""")
    user_id = callback_query.from_user.id
    if not db.is_account_booked_by_user(user_id):
        db.initiate_buyer_status(user_id)
        await callback_query.message.answer("Выберите пол", reply_markup=keyboards.gender_kb)
    else:
        await callback_query.message.answer("У вас уже есть забронированный аккаунт. Отправьте id транзакции для получения")
    await callback_query.answer()

@dp.message_handler(lambda message: message.text in ["М", "Ж", "Любой пол"])
async def handle_gender_choice(message: types.Message):
    user_id = message.from_user.id
    gender = message.text
    db.update_buyer_gender(user_id, gender.upper())
    await message.answer("Выберите возраст", reply_markup=keyboards.age_kb)

@dp.message_handler(lambda message: message.text in ["<18", ">18", "Любой возраст"])
async def handle_age_choice(message: types.Message):
    user_id = message.from_user.id
    age = message.text
    db.update_buyer_age(user_id, age)
    gender = db.get_gender(user_id)
    available_qty = db.get_available_quantity(gender.upper(), age)
    db.update_buyer_av_quantity(user_id, available_qty)
    await message.answer(f"Выберите количество (доступно: {available_qty})", reply_markup=keyboards.quantity_kb(available_qty))

@dp.message_handler(lambda message: message.text.isdigit() and 1 <= int(message.text) <= db.get_buyer_av_quantity(message.from_user.id))
async def handle_quantity_choice(message: types.Message):
    user_id = message.from_user.id
    qty = int(message.text)
    db.update_buyer_quantity(user_id, qty)
    await message.answer(f"Подтвердите заказ: {qty} аккаунтов за {defs.price(user_id) * qty} USDT", reply_markup=keyboards.confirm_kb)

@dp.message_handler(lambda message: message.text == "Подтвердить")
async def handle_confirmation(message: types.Message):
    user_id = message.from_user.id
    db.book_accounts_for_user(user_id)
    await message.answer(f"Отправьте USDT TRC20 на кошелек: {WALLET_ADRESS} и пришлите ID транзакции.", reply_markup=keyboards.cancel_kb)

@dp.message_handler(lambda message: defs.is_valid_hash(message.text))
async def handle_payment(message: types.Message):
    user_id = message.from_user.id
    if db.is_user_in_process(user_id):
        payment_hash = message.text
        is_used, date = db.is_hash_used(payment_hash)
        if is_used:
            await message.answer(f"Этот хэш уже был использован {date}. Пожалуйста, пришлите новый.")
        else:
            qty_booked = int(db.get_qty(user_id))
            price = defs.price(user_id)
            flag, real_value = defs.check_transaction(WALLET_ADRESS, payment_hash, (qty_booked * price))
            if flag != 0:
                if real_value >= price-1:
                    db.record_payment(user_id, payment_hash, real_value)
                    qty = int(real_value/price)

                    accounts = db.get_data_buyer(user_id, qty)
                    await message.answer(f"Спасибо за платеж. Поступило {real_value}$ за {qty} аккаунт(ов). Если вы выбрали меньше, чем заплатили - пишите {admin_link}. Ваш(и) аккаунт(ы):")
                    if accounts:
                        for account in accounts:
                            # Отправляем фотографии
                            photo_ids = [
                                account[1],  # Photo Account 1
                                account[2],  # Photo Account 2
                                account[3],  # Photo Linked Account
                                account[4]   # Photo QR Sim
                            ]
                            for photo_id in photo_ids:
                                if photo_id:  # Проверяем, что фото существует
                                    await message.answer_photo(photo_id)
                            
                            # Формируем текстовую информацию и отправляем
                            text_data = f"""
{account[5]}
Пол: {account[6]}
Возраст: {account[7]}
Имя продавца: {account[8]}
Номер анкеты: {account[0]}
                                            """
                            await message.answer(text_data)
                            db.move_to_sold_accounts(user_id, account[0])
                    db.clear_buyer_status(user_id)
                else:
                    await message.answer(f"Сумма ({real_value}) меньше минимальной, обратитесь к {admin_link}")
            else:
                await message.answer("Транзакция не найдена")

@dp.message_handler(lambda message: message.text == "Отмена")
async def handle_cancel(message: types.Message):
    user_id = message.from_user.id

    # Очищаем запись в таблице buyers_status
    db.clear_buyer_status(user_id)

    # Отправляем приветственное сообщение и клавиатуру как при /start
    if user_id in admin_id:
        kb = keyboards.admin_kb
    elif user_id in drop_id:
        kb = keyboards.seller_kb
    elif user_id in ban_id:
        return
    elif user_id in buyer_id:
        kb = keyboards.user_kb
    else:
        kb = keyboards.newbie_kb
    await message.answer("Действие отменено. Чем могу помочь?", reply_markup=kb)

@dp.message_handler(lambda message:message.from_user.id in drop_id, content_types=types.ContentType.ANY)
async def handle_albums(message: types.Message, album: List[types.Message]):
    user_id = message.from_user.id
    status, start_time = db.get_user_status(user_id)

    if status == "loading_account":
        if datetime.now() - datetime.fromisoformat(start_time) < timedelta(minutes=5):
            photos = [msg.photo[-1].file_id for msg in album if msg.photo]
            if len(photos) == 4:  # Проверка на 4 фото
                try:
                    data = {
                        'photo_acc1': photos[0],
                        'photo_acc2': photos[1],
                        'photo_linked_acc': photos[2],
                        'photo_qr_sim': photos[3],
                        'form_data': message.caption
                    }
                    
                    gender, age = defs.extract_account_data(data['form_data'])[2:]
                    if age is None:
                       raise ValueError("Возраст не найден или неккоректен")
                    seller_name = db.get_seller_name(user_id)
                    data.update({
                        'gender': gender.upper(),
                        'age': age,
                        'seller_name': seller_name
                    })
                    
                    db.save_account_data(data)
                    await message.answer("Данные сохранены!")
                    db.reset_user_status(user_id)
                except Exception as e:
                    await message.answer(f"Произошла ошибка: {e}")
            else:
                await message.answer("Пожалуйста, отправьте 4 фото в альбоме.")
        else:
            # Превышено время ожидания
            db.reset_user_status(user_id)
            await message.answer("Время ожидания истекло. Пожалуйста, начните заново с /add_account.")
    else:
        await message.answer("Сначала начните загрузку с /add_account.")

if __name__ == "__main__":
    db.initialize_prices()
    dp.middleware.setup(classes.AlbumMiddleware())
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
