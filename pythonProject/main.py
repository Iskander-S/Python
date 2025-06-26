import telebot
from telebot import types
import csv
import datetime
import threading
import time
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

# Конфигурация с обработкой ошибок
try:
    TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    TEACHER_GROUP_IDS = [int(x) for x in os.getenv("TEACHER_GROUP_IDS", "").split(",") if x]
except (ValueError, TypeError) as e:
    logger.error(f"Ошибка загрузки конфигурации: {e}")
    exit(1)

if not TOKEN:
    logger.error("Токен бота не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
user_data = {}
user_data_lock = threading.Lock()

# Данные бота
FAQ = {
    "Адрес": "Наш адрес: ул. Сатпаева 22, ГУК КАЗНИТУ, 2 этаж, кабинет 206а, Международная Академия Робототехники.\nВход с улицы Байтурсынова. Как заходите слева лестница и сразу на второй этаж к нам попадете. \nhttps://go.2gis.com/gBgLO",
    "График": "Мы работаем:\n - Со вторника по пятницу с 15:00 до 20:00\n - В субботу и воскресенье с 9:00 до 19:00.",
}

# Исправленные названия дней недели (английские для strftime)
lesson_times_by_age = {
    "5-6": {
        "Sunday": ["17:00 - 18:00", "18:00 - 19:00"]
    },
    "7-10": {
        "Saturday": ["9:30 - 10:30", "10:30 - 11:30", "12:00 - 13:00", "13:00 - 14:00"],
        "Sunday": ["9:30 - 10:30", "10:30 - 11:30", "12:00 - 13:00", "13:00 - 14:00"]
    },
    "11-13": {
        "Tuesday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Wednesday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Thursday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Saturday": ["15:00 - 16:00"],
        "Sunday": ["15:00 - 16:00"],
    },
    "14-16": {
        "Saturday": ["12:00 - 13:00"],
        "Sunday": ["12:00 - 13:00"],
    }
}

# Словарь для перевода английских дней недели в русские
weekday_translation = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

course_info_texts = {
    "🤖 Робототехника": "🛠🤖 Курсы по робототехнике:\n 1) VEX GO / LEGO — 5 000 ₸ за урок. При записи на 8 уроков — 9-й урок бесплатно!\n 2) Вводный курс VEX IQ — длительность 2 месяца, по 8 уроков в месяц. Стоимость — 40 000 ₸ в месяц.\n 3) Подготовка к соревнованиям VEX IQ и VEX V5:\n - Оплата по количеству посещённых уроков.\n - Стандартная цена: 8 уроков в месяц — 40 000 ₸ (IQ) или 48 000 ₸ (V5).\n - Подписка: неограниченное количество уроков в месяц — 68 000 ₸ (IQ) или 76 000 ₸ (V5).",
    "💻 Курсы": "💻 Мы предлагаем курсы по программированию, искусственному интеллекту, геймдеву и Python. Возраст: 9–16 лет.",
    "🌞 Летний лагерь": "🌞 Летний лагерь проходит с июня по август. В программе робототехника, программирование, ИИ и развлекательные мероприятия. Смена длится 2 недели.",
    "👨‍💻 Программирование": "🧠 Программирование:\n- Длительность: 2 месяца\n- Стоимость: 80 000 ₸\n- Урок: 90 минут\n- 8 уроков в месяц",
    "🎨 3D Моделирование": "🎨 3D Моделирование:\n- Длительность: 1 месяц\n- Стоимость: 40 000 ₸\n- Урок: 90 минут\n- 8 уроков в месяц",
    "🔌 Электроника": "🔌 Электроника:\n- Длительность: 2 месяца\n- Стоимость: 80 000 ₸\n- Урок: 90 минут\n- 8 уроков в месяц",
    "🧠 ИИ": "🤖 Искусственный интеллект:\n- Длительность: 1 месяц\n- Стоимость: 40 000 ₸\n- Урок: 90 минут\n- 8 уроков в месяц",
    "🇬🇧 Английский (начальный)": "🇬🇧 Английский для Робототехники (начальный):\n- Длительность: 2 месяца\n- Стоимость: 40 000 ₸\n- Урок: 90 минут\n- 8 уроков в месяц",
    "🇬🇧 Английский (продвинутый)": "🇬🇧 Английский для Робототехники (продвинутый):\n- Длительность: 2 месяца\n- Стоимость: 40 000 ₸\n- Урок: 90 минут\n- 8 уроков в месяц",
}

CSV_HEADER = ["chat_id", "name", "age", "date", "time", "username", "status"]

# Вспомогательные функции
def get_age_group(age):
    if 5 <= age <= 6:
        return "5-6"
    elif 7 <= age <= 10:
        return "7-10"
    elif 11 <= age <= 13:
        return "11-13"
    elif 14 <= age <= 16:
        return "14-16"
    return None


def get_user_active_registrations(chat_id):
    """Возвращает активные записи пользователя"""
    active_registrations = []
    if os.path.exists("trial_lessons.csv"):
        try:
            with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["chat_id"] == str(chat_id) and row.get("status", "active") == "active":
                        active_registrations.append(row)
        except Exception as e:
            logger.error(f"Ошибка чтения CSV: {e}")
    return active_registrations


def cancel_registration(record_id):
    """Отменяет запись по ID"""
    try:
        rows = []
        with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        for row in rows:
            if f"{row['date']}_{row['time']}" == record_id:
                row["status"] = "cancelled"

        with open("trial_lessons.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        logger.error(f"Ошибка отмены записи: {e}")
        return False


def get_active_registrations():
    """Возвращает все активные записи"""
    active = []
    if os.path.exists("trial_lessons.csv"):
        try:
            with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("status", "active") == "active":
                        active.append(row)
        except Exception as e:
            logger.error(f"Ошибка чтения CSV: {e}")
    return active

def get_available_dates(age_group, days_ahead=14):
    """Возвращает доступные даты для указанной возрастной группы"""
    today = datetime.date.today()
    result = {}
    for i in range(days_ahead):
        date = today + datetime.timedelta(days=i)
        weekday = date.strftime("%A")
        if weekday in lesson_times_by_age[age_group]:
            # Переводим день недели на русский для отображения пользователю
            russian_weekday = weekday_translation.get(weekday, weekday)
            result[date.strftime("%Y-%m-%d")] = {
                "times": lesson_times_by_age[age_group][weekday],
                "weekday": russian_weekday
            }
    return result

def load_existing_slots():
    booked = set()
    if os.path.exists("trial_lessons.csv"):
        try:
            with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "date" in row and "time" in row:
                        booked.add((row["date"], row["time"]))
        except Exception as e:
            logger.error(f"Ошибка чтения CSV: {e}")
    return booked
def save_registration(chat_id, name, age, date, time, username):
    try:
        file_exists = os.path.exists("trial_lessons.csv")
        with open("trial_lessons.csv", "a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "chat_id": chat_id,
                "name": name,
                "age": age,
                "date": date,
                "time": time,
                "username": username or "",
                "status": "active"
            })
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

@bot.message_handler(commands=["mybookings"])
def show_user_bookings(message):
    registrations = get_user_active_registrations(message.chat.id)

    if not registrations:
        bot.send_message(message.chat.id, "У вас нет активных записей.")
        return

    markup = types.InlineKeyboardMarkup()
    for reg in registrations:
        btn_text = f"{reg['date']} {reg['time']} - {reg['name']}, {reg['age']} лет"
        callback_data = f"edit_{reg['date']}_{reg['time']}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))

    bot.send_message(message.chat.id, "Ваши активные записи:", reply_markup=markup)


# Обработчик callback для кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("edit_"):
        record_id = call.data[5:]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ Изменить", callback_data=f"change_{record_id}"))
        markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{record_id}"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Запись: {record_id.replace('_', ' ')}\nВыберите действие:",
            reply_markup=markup
        )

    elif call.data.startswith("cancel_"):
        record_id = call.data[7:]
        if cancel_registration(record_id):
            bot.answer_callback_query(call.id, "Запись отменена!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="✅ Запись отменена"
            )
        else:
            bot.answer_callback_query(call.id, "Ошибка отмены записи!")

    elif call.data.startswith("change_"):
        record_id = call.data[7:]
        # Здесь можно добавить логику изменения записи
        bot.answer_callback_query(call.id, "Функция изменения пока в разработке")

def notify_teachers(text):
    for group_id in TEACHER_GROUP_IDS:
        try:
            bot.send_message(group_id, text)
        except Exception as e:
            logger.error(f"Ошибка отправки учителям: {e}")

def clean_old_records(days_threshold=30):
    """Удаляет записи старше указанного количества дней"""
    threshold_date = datetime.date.today() - datetime.timedelta(days=days_threshold)
    try:
        if os.path.exists("trial_lessons.csv"):
            with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                valid_rows = []
                for row in reader:
                    try:
                        record_date = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
                        if record_date >= threshold_date:
                            valid_rows.append(row)
                    except ValueError:
                        continue

            with open("trial_lessons.csv", "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
                writer.writeheader()
                writer.writerows(valid_rows)

            logger.info(f"Удалены записи старше {days_threshold} дней. Осталось {len(valid_rows)} записей.")
            return len(valid_rows)
    except Exception as e:
        logger.error(f"Ошибка очистки старых записей: {e}")
    return 0


# Обработчики команд
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["✅ Записаться", "ℹ️ Информация о курсах", "📍 Адрес"]

    if message.chat.id == ADMIN_ID:
        buttons.append("🧹 Очистить записи")

    markup.add(*buttons)
    bot.send_message(message.chat.id,
                     "Привет! Я бот International Robotics Academy. Чем могу помочь?",
                     reply_markup=markup)


@bot.message_handler(commands=["clear"])
def clear_all_records(message):
    """Обработчик команды очистки всех записей"""
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет прав на эту операцию")
        return

    try:
        with open("trial_lessons.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
        bot.reply_to(message, "✅ Все записи успешно очищены")
        logger.info(f"Администратор {message.from_user.id} очистил все записи")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при очистке: {e}")
        logger.error(f"Ошибка очистки записей: {e}")


@bot.message_handler(func=lambda m: m.text == "🧹 Очистить записи" and m.chat.id == ADMIN_ID)
def clear_records_button(message):
    clear_all_records(message)


@bot.message_handler(commands=["list"])
def send_list_to_admin(message):
    if message.chat.id != ADMIN_ID:
        return

    try:
        with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        if not records:
            bot.send_message(ADMIN_ID, "Записей пока нет.")
            return

        response = ["📋 Список записей:"]
        for row in records:
            response.append(
                f"👤 {row.get('name', 'N/A')}, {row.get('age', 'N/A')} лет\n"
                f"📅 {row.get('date', 'N/A')} в {row.get('time', 'N/A')}\n"
                f"💬 @{row.get('username', '')}\n"
            )

        bot.send_message(ADMIN_ID, "\n".join(response))
    except Exception as e:
        logger.error(f"Ошибка получения списка: {e}")
        bot.send_message(ADMIN_ID, "Ошибка при получении списка записей.")

# Обработчики текстовых сообщений
@bot.message_handler(func=lambda m: m.text.strip().lower() in ["✅ записаться", "записаться"])
def start_registration(message):
    # Проверяем активные записи пользователя
    user_registrations = get_user_active_registrations(message.chat.id)

    # Проверяем, есть ли записи на текущую неделю
    current_week = datetime.date.today().isocalendar()[1]
    has_weekly_booking = any(
        datetime.datetime.strptime(reg["date"], "%Y-%m-%d").date().isocalendar()[1] == current_week
        for reg in user_registrations
    )

    if has_weekly_booking:
        bot.send_message(message.chat.id,
                         "Вы уже записаны на пробный урок на этой неделе. Можно записаться только 1 раз в неделю.")
        return

    with user_data_lock:
        user_data[message.chat.id] = {"step": "name"}
    bot.send_message(message.chat.id, "Запись на пробный урок")
    bot.send_message(message.chat.id, "Введите имя ребёнка:")


@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "name")
def get_name(message):
    with user_data_lock:
        user_data[message.chat.id] = {
            "name": message.text.strip(),
            "step": "age"
        }
    bot.send_message(message.chat.id, "Введите возраст ребёнка:")


@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "age")
def get_age(message):
    try:
        age = int(message.text.strip())
        age_group = get_age_group(age)
        if not age_group:
            return bot.send_message(message.chat.id, "Мы принимаем детей от 5 до 16 лет.")

        with user_data_lock:
            user_data[message.chat.id].update({
                "age": age,
                "age_group": age_group,
                "step": "date"
            })

        available_dates = get_available_dates(age_group)
        booked = load_existing_slots()
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

        for date_str, times in available_dates.items():
            if any((date_str, t) not in booked for t in times):
                markup.add(date_str)

        if not markup.keyboard:
            bot.send_message(message.chat.id, "К сожалению, нет доступных дат для записи.")
            with user_data_lock:
                user_data.pop(message.chat.id, None)
            return start(message)

        bot.send_message(message.chat.id, "Выберите дату урока:", reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите возраст числом.")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "date")
def choose_date(message):
    selected_date = message.text.strip()
    with user_data_lock:
        user_info = user_data.get(message.chat.id, {})
        age_group = user_info.get("age_group")

    available_dates = get_available_dates(age_group)
    if selected_date not in available_dates:
        bot.send_message(message.chat.id, "Пожалуйста, выберите дату из предложенных.")
        return

    with user_data_lock:
        user_data[message.chat.id].update({
            "date": selected_date,
            "step": "time"
        })

    booked = load_existing_slots()
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    weekday = available_dates[selected_date]["weekday"]
    for time_slot in available_dates[selected_date]["times"]:
        if (selected_date, time_slot) not in booked:
            markup.add(f"{time_slot} ({weekday})")

    if not markup.keyboard:
        bot.send_message(message.chat.id, "Нет доступных временных слотов на выбранную дату.")
        with user_data_lock:
            user_data.pop(message.chat.id, None)
        return start(message)

    bot.send_message(message.chat.id, "Выберите время урока:", reply_markup=markup)

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "time")
def choose_time(message):
    selected_time_with_weekday = message.text.strip()
    # Удаляем день недели из выбранного времени
    selected_time = selected_time_with_weekday.split(" (")[0]

    chat_id = message.chat.id
    with user_data_lock:
        user_info = user_data.get(chat_id, {})
        date = user_info.get("date")
        name = user_info.get("name")
        age = user_info.get("age")
        username = message.from_user.username or ""

    booked = load_existing_slots()
    if (date, selected_time) in booked:
        bot.send_message(chat_id, "Это время уже занято. Пожалуйста, выберите другое.")
        return

    if save_registration(chat_id, name, age, date, selected_time, username):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🏠 Главное меню")

        bot.send_message(
            chat_id,
            f"✅ Вы записаны на пробный урок:\n"
            f"📅 Дата: {date}\n"
            f"⏰ Время: {selected_time}\n"
            f"👶 Ребёнок: {name}, {age} лет\n\n"
            f"Ждём вас по адресу:\n{FAQ['Адрес']}",
            reply_markup=markup
        )

        notify_text = (
            f"📥 Новая запись:\n"
            f"👶 {name}, {age} лет\n"
            f"📅 {date} в {selected_time}\n"
            f"👤 @{username}" if username else ""
        )
        bot.send_message(ADMIN_ID, notify_text)
        notify_teachers(notify_text)
    else:
        bot.send_message(chat_id, "Ошибка при сохранении записи. Пожалуйста, попробуйте ещё раз.")

    with user_data_lock:
        user_data.pop(chat_id, None)

@bot.message_handler(func=lambda m: m.text.strip().lower() in ["📍 адрес", "адрес"])
def send_address(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏠 Главное меню")
    bot.send_message(message.chat.id, FAQ["Адрес"], reply_markup=markup)


@bot.message_handler(func=lambda m: m.text.strip().lower() in ["ℹ️ информация о курсах", "информация о курсах"])
def show_courses(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🤖 Робототехника", "💻 Курсы", "🌞 Летний лагерь")
    markup.add("🏠 Главное меню")
    bot.send_message(message.chat.id, "Выберите направление:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text.strip() in course_info_texts)
def send_course_info(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏠 Главное меню")
    bot.send_message(message.chat.id, course_info_texts[message.text.strip()], reply_markup=markup)


@bot.message_handler(func=lambda m: m.text.strip().lower() in ["🏠 главное меню", "главное меню"])
def main_menu(message):
    start(message)

# Система напоминаний и автоматической очистки
def maintenance_worker():
    """Фоновая задача для напоминаний и очистки старых записей"""
    while True:
        now = datetime.datetime.now()

        if now.hour == 9:
            # Отправка напоминаний только для активных записей
            tomorrow = (now + datetime.timedelta(days=1)).date()
            try:
                active_registrations = get_active_registrations()
                for reg in active_registrations:
                    try:
                        lesson_date = datetime.datetime.strptime(reg["date"], "%Y-%m-%d").date()
                        if lesson_date == tomorrow:
                            try:
                                bot.send_message(
                                    reg["chat_id"],
                                    f"🔔 Напоминание: завтра в {reg['time']} у вас пробный урок!"
                                )
                            except Exception as e:
                                logger.error(f"Ошибка напоминания: {e}")
                    except ValueError:
                        continue
            except Exception as e:
                logger.error(f"Ошибка отправки напоминаний: {e}")

            if now.weekday() == 0:  # Понедельник
                remaining = clean_old_records(30)
                logger.info(f"Автоочистка: осталось {remaining} актуальных записей")

            time.sleep(82800)
        else:
            time.sleep(1800)


if __name__ == "__main__":
    # Первоначальная очистка при запуске
    clean_old_records(30)

    # Запуск фоновых задач
    threading.Thread(target=maintenance_worker, daemon=True).start()

    # Запуск бота
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")