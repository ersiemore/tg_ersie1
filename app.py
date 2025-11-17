import telebot
import sqlite3
import time
from config import TOKEN, ADMIN_ID
from telebot import types

bot = telebot.TeleBot(TOKEN)

last_message_time = {}
SPAM_DELAY = 5

def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            user_id INTEGER,
            username TEXT,
            message TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_report(user_id, username, message):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO reports (user_id, username, message, status) VALUES (?, ?, ?, ?)",
        (user_id, username, message, 'new')
    )
    conn.commit()
    conn.close()

def notify_admin(user_id, username, message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Ответить", callback_data=f"reply|{user_id}")
    markup.add(btn)
    bot.send_message(
        ADMIN_ID,
        f"📩 Новое сообщение от @{username or 'без username'} (ID: {user_id}):\n\n{message}",
        reply_markup=markup
    )

def check_spam(user_id):
    now = time.time()
    last = last_message_time.get(user_id, 0)
    if now - last < SPAM_DELAY:
        return True
    last_message_time[user_id] = now
    return False

@bot.message_handler(commands=['start'])
def main_menu(message):
    markup = types.InlineKeyboardMarkup()
    btn_report = types.InlineKeyboardButton("📝 Написать сообщение", callback_data="menu_report")
    btn_help = types.InlineKeyboardButton("❓ Помощь", callback_data="menu_help")
    markup.add(btn_report, btn_help)
    bot.send_message(message.chat.id, "Выберите пункт меню:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_menu(call):
    data = call.data
    if data == "menu_report":
        markup = types.InlineKeyboardMarkup()
        btn_send = types.InlineKeyboardButton("Отправить сообщение", callback_data="do_report")
        btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        markup.add(btn_send, btn_back)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Что делаем дальше?",
                              reply_markup=markup)
    elif data == "menu_help":
        markup = types.InlineKeyboardMarkup()
        btn_about = types.InlineKeyboardButton("О боте", callback_data="help_about")
        btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        markup.add(btn_about, btn_back)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Помощь:",
                              reply_markup=markup)
    elif data == "do_report":
        bot.send_message(call.message.chat.id, "✏️ Напиши своё сообщение:")
        bot.register_next_step_handler(call.message, handle_report_message)
    elif data.startswith("reply|"):
        parts = data.split("|")
        if len(parts) == 2:
            target_user_id = int(parts[1])
            bot.send_message(call.message.chat.id, f"Напиши сообщение для пользователя {target_user_id}:")
            bot.register_next_step_handler(call.message, reply_to_user, target_user_id)
    elif data == "help_about":
        bot.send_message(call.message.chat.id, "Я — бот, который передаёт сообщения Ивану.")
    elif data == "back_to_main":
        main_menu(call.message)

def handle_report_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_message = message.text
    if check_spam(user_id):
        bot.send_message(message.chat.id, "⚠️ Подожди немного, пожалуйста.")
        return
    save_report(user_id, username, user_message)
    notify_admin(user_id, username, user_message)
    bot.send_message(message.chat.id, "✅ Твоё сообщение отправлено Ивану.")

def reply_to_user(message, target_user_id):
    text = message.text
    bot.send_message(target_user_id, f"📬 Ответ от Ивана:\n\n{text}")
    bot.send_message(message.chat.id, "Ответ отправлен.")

@bot.message_handler(commands=['view_reports'])
def view_reports(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 У вас нет прав.")
        return
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("SELECT user_id, username, message, status FROM reports WHERE status = 'new'")
    reports = c.fetchall()
    conn.close()
    if not reports:
        bot.send_message(message.chat.id, "📭 Нет новых сообщений.")
    else:
        for (user_id, username, msg, status) in reports:
            bot.send_message(message.chat.id, f"📨 От @{username} (ID: {user_id}):\n{msg}")

@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    bot.reply_to(message, "Не понял. Напиши /start.")

if __name__ == "__main__":
    init_db()
    bot.delete_webhook()
    print("Бот запущен")
    bot.polling(none_stop=True)
