import telebot
from telebot import types
import csv
import datetime
import threading
import time

TOKEN = '7840762508:AAGoLhJhDW-mebn2VojRmDcSpybMmn7PAHo'
ADMIN_ID = 

bot = telebot.TeleBot(TOKEN)
user_data = {}

FAQ = {
    "Адрес": "Наш адрес: ул. Сатпаева 22, ГУК КАЗНИТУ, 2 этаж, кабинет 206а, Международная Академия Робототехники.\nВход с улицы Байтурсынова. Как заходите слева лестница и сразу на второй этаж к нам попадете.",
    "График": "Мы работаем:\n - Со вторника по пятницу с 15:00 до 20:00\n - В субботу и воскресенье с 9:00 до 19:00.",
}

lesson_times_by_age = {
    "5-6": {
        "Sunday": ["17:00 - 18:00", "18:00 - 19:00"],
    },
    "7-10": {
        "Saturday": ["9:30 - 10:30", "10:30 - 11:30", "12:00 - 13:00", "13:00 - 14:00"],
        "Sunday": ["9:30 - 10:30", "10:30 - 11:30", "12:00 - 13:00", "13:00 - 14:00"]
    },
    "11-13": {
        "Tuesday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Wednesday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Thursday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Friday": ["14:30 - 15:30", "16:00 - 17:00"],
        "Saturday": ["15:00 - 16:00"],
        "Sunday": ["15:00 - 16:00"],
    },
    "14-16": {
        "Saturday": ["12:00 - 13:00"],
        "Sunday": ["12:00 - 13:00"],
    }
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

course_info = {
    "🤖 Робототехника": "🛠🤖 Курсы по робототехнике:\n 1) *VEX GO / LEGO* — 5 000 ₸ за урок. При записи на 8 уроков — 9-й урок бесплатно!\n 2) Вводный курс VEX IQ — длительность 2 месяца, по 8 уроков в месяц. Стоимость — 40 000 ₸ в месяц.\n 3) Подготовка к соревнованиям VEX IQ и VEX V5:\n - Оплата по количеству посещённых уроков.\n - Стандартная цена: 8 уроков в месяц — 40 000 ₸ (IQ) или 48 000 ₸ (V5).\n - Подписка: неограниченное количество уроков в месяц — 68 000 ₸ (IQ) или 76 000 ₸ (V5).",
    "💻 Курсы": "💻 Мы предлагаем курсы по программированию, искусственному интеллекту, геймдеву и Python. Возраст: 9–16 лет.",
    "🌞 Летний лагерь": "🌞 Летний лагерь проходит с июня по август. В программе робототехника, программирование, ИИ и развлекательные мероприятия. Смена длится 2 недели."
}

def get_age_group(age):
    if 5 <= age <= 6:
        return "5-6"
    elif 7 <= age <= 10:
        return "7-10"
    elif 11 <= age <= 13:
        return "11-13"
    elif 14 <= age <= 16:
        return "14-16"
    else:
        return None

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ Записаться", "ℹ️ Информация о курсах", "📍 Адрес")
    bot.send_message(message.chat.id, "Привет! Я бот International Robotics Academy. Чем могу помочь?", reply_markup=markup)

@bot.message_handler(commands=["list"])
def send_list_to_admin(message):
    if message.chat.id != ADMIN_ID:
        return
    response = "📋 Список записей:\n\n"
    try:
        with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            for parts in reader:
                if len(parts) < 6:
                    continue
                response += f"👤 {parts[1]}, {parts[2]} лет\n📅 {parts[3]} в {parts[4]}\n\n"
    except FileNotFoundError:
        response = "Записей пока нет."
    bot.send_message(ADMIN_ID, response)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip().lower()

    # Главное меню
    if text in ["✅ записаться", "записаться"]:
        user_data[message.chat.id] = {"step": "name"}
        bot.send_message(message.chat.id, "Введите имя ребёнка:")
        return

    if text in ["📍 адрес", "адрес"]:
        bot.send_message(message.chat.id, FAQ["Адрес"])
        return

    if text in ["ℹ️ информация о курсах", "информация о курсах"]:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🤖 Робототехника", "💻 Курсы", "🌞 Летний лагерь")
        markup.add("🏠 Главное меню")
        bot.send_message(message.chat.id, "Выберите интересующее направление:", reply_markup=markup)
        return

    if text == "💻 курсы":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👨‍💻 Программирование", "🎨 3D Моделирование")
        markup.add("🔌 Электроника", "🧠 ИИ")
        markup.add("🇬🇧 Английский (начальный)", "🇬🇧 Английский (продвинутый)")
        markup.add("🔙 Назад к направлениям", "🏠 Главное меню")
        bot.send_message(message.chat.id, "Выберите курс для просмотра подробностей:", reply_markup=markup)
        return

    if text == "🔙 назад к направлениям":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🤖 Робототехника", "💻 Курсы", "🌞 Летний лагерь")
        markup.add("🏠 Главное меню")
        bot.send_message(message.chat.id, "Выберите интересующее направление:", reply_markup=markup)
        return
    if text == "🏠 главное меню":
        start(message)
        return

    if message.text.strip() in course_info_texts:
        bot.send_message(message.chat.id, course_info_texts[message.text.strip()])
        return

    if "стоимость" in text:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for course in courses:
            markup.add(course)
        bot.send_message(message.chat.id, "Пожалуйста, выберите интересующий курс:", reply_markup=markup)
        user_data[message.chat.id] = {"step": "price_inquiry"}
        return

    for key in FAQ:
        if key.lower() in text:
            bot.send_message(message.chat.id, FAQ[key])
            return

    # Логика записи
    if message.chat.id in user_data:
        step = user_data[message.chat.id].get("step")

        if step == "name":
            user_data[message.chat.id]["name"] = message.text.strip()
            user_data[message.chat.id]["step"] = "age"
            bot.send_message(message.chat.id, "Введите возраст ребёнка:")

        elif step == "age":
            try:
                age = int(message.text.strip())
                age_group = get_age_group(age)
                if age_group is None:
                    bot.send_message(message.chat.id, "Мы принимаем детей от 5 до 16 лет.")
                    return
                user_data[message.chat.id]["age"] = age
                user_data[message.chat.id]["age_group"] = age_group
                user_data[message.chat.id]["step"] = "date"

                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                for day in lesson_times_by_age[age_group]:
                    markup.add(day)
                bot.send_message(message.chat.id, "Выберите дату:", reply_markup=markup)
            except ValueError:
                bot.send_message(message.chat.id, "Пожалуйста, введите возраст числом.")

        elif step == "date":
            age_group = user_data[message.chat.id]["age_group"]
            if message.text in lesson_times_by_age[age_group]:
                user_data[message.chat.id]["date"] = message.text
                user_data[message.chat.id]["step"] = "time"

                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                for t in lesson_times_by_age[age_group][message.text]:
                    markup.add(t)
                bot.send_message(message.chat.id, "Теперь выберите время:", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, выберите дату из предложенных.")

        elif step == "time":
            age_group = user_data[message.chat.id]["age_group"]
            date = user_data[message.chat.id]["date"]
            if message.text in lesson_times_by_age[age_group][date]:
                user_data[message.chat.id]["time"] = message.text
                username = message.from_user.username or ''
                with open("trial_lessons.csv", "a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        message.chat.id,
                        user_data[message.chat.id]["name"],
                        user_data[message.chat.id]["age"],
                        date,
                        message.text,
                        username
                    ])
                bot.send_message(message.chat.id,
                                 f"✅ Вы записаны на пробный урок {date} в {message.text}. Мы напомним вам за день.")
                bot.send_message(ADMIN_ID, f"📥 Новая запись: {user_data[message.chat.id]['name']}, {user_data[message.chat.id]['age']} лет, {date} в {message.text}.")
                user_data.pop(message.chat.id)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, выберите время из предложенных.")

    if user_data.get(message.chat.id, {}).get("step") == "price_inquiry":
        course_name = message.text.strip()
        if course_name in courses:
            bot.send_message(message.chat.id, courses[course_name])
            user_data.pop(message.chat.id)
        else:
            bot.send_message(message.chat.id, "Пожалуйста, выберите курс из предложенного списка.")
        return

# Напоминание за день до занятия (в 9 утра)
def reminder_worker():
    sent_today = set()
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute < 5:
            tomorrow = (now + datetime.timedelta(days=1)).strftime("%A")
            try:
                with open("trial_lessons.csv", newline='', encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) < 6:
                            continue
                        chat_id = int(row[0])
                        child_name = row[1]
                        lesson_day = row[3]
                        time_str = row[4]
                        key = f"{chat_id}_{lesson_day}_{time_str}"
                        if lesson_day == tomorrow and key not in sent_today:
                            try:
                                bot.send_message(chat_id, f"🔔 Напоминаем: завтра у вас пробный урок в {time_str}.")
                                sent_today.add(key)
                            except Exception as e:
                                print(f"Ошибка при отправке напоминания: {e}")
            except FileNotFoundError:
                pass
            time.sleep(300)
        else:
            time.sleep(60)

threading.Thread(target=reminder_worker, daemon=True).start()
bot.polling(none_stop=True)
