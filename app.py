import os
import telebot
import sqlite3
import time

TOKEN = os.environ.get('TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports
        (user_id INTEGER, username TEXT, message TEXT, status TEXT)
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
    bot.send_message(
        ADMIN_ID,
        f"📩 Новое сообщение от @{username or 'пользователя без username'} (ID: {user_id}):\n\n{message}"
    )

last_message_time = {}
SPAM_DELAY = 5

def check_spam(user_id):
    now = time.time()
    last_time = last_message_time.get(user_id, 0)
    if now - last_time < SPAM_DELAY:
        return True
    last_message_time[user_id] = now
    return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋 Я твой менеджер-бот. Если тебе ограничили доступ, можешь написать мне, и я передам сообщение админу.\n\nИспользуй команду /report, чтобы отправить сообщение."
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "📋 Команды:\n/start — начать\n/help — помощь\n/report — написать админу"
    )

@bot.message_handler(commands=['report'])
def report_command(message):
    bot.send_message(message.chat.id, "✏️ Напиши своё сообщение, и я передам его админу.")
    bot.register_next_step_handler(message, handle_report_message)

def handle_report_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_message = message.text

    if check_spam(user_id):
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, не спамьте. Подождите несколько секунд.")
        return

    save_report(user_id, username, user_message)
    notify_admin(user_id, username, user_message)
    bot.send_message(message.chat.id, "✅ Спасибо! Твоё сообщение отправлено админу.")

@bot.message_handler(commands=['view_reports'])
def view_reports(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 У вас нет прав для этой команды.")
        return

    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE status = 'new'")
    reports = c.fetchall()
    conn.close()

    if not reports:
        bot.send_message(message.chat.id, "📭 Нет новых сообщений.")
    else:
        for report in reports:
            user_id, username, msg, status = report
            bot.send_message(message.chat.id, f"📨 От @{username} (ID: {user_id}):\n{msg}")

@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    bot.reply_to(message, "Не понял команду. Напиши /help для списка команд.")

if __name__ == "__main__":
    init_db()
    print("Бот запущен...")
    bot.polling(none_stop=True)
