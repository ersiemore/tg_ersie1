import telebot
import sqlite3
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

# === ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (user_id INTEGER, username TEXT, message TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# === СОХРАНЕНИЕ СООБЩЕНИЯ В БАЗЕ ===
def save_report(user_id, username, message):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("INSERT INTO reports (user_id, username, message, status) VALUES (?, ?, ?, ?)",
              (user_id, username, message, 'new'))
    conn.commit()
    conn.close()

# === ОТПРАВКА СООБЩЕНИЯ АДМИНУ ===
def notify_admin(user_id, username, message):
    admin_id = 8219861530
    bot.send_message(admin_id, f"📩 Новое сообщение от @{username or 'пользователя без username'} (ID: {user_id}):\n\n{message}")

# === КОМАНДЫ БОТА ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! 👋 Я твой менеджер-бот. Если тебе ограничили доступ, ты можешь написать мне, и я передам сообщение админу.\n\nИспользуй команду /report, чтобы отправить сообщение.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "📋 Команды:\n/start — начать\n/help — помощь\n/report — написать админу")

@bot.message_handler(commands=['report'])
def report_command(message):
    bot.send_message(message.chat.id, "✏️ Напиши своё сообщение, и я передам его админу.")
    bot.register_next_step_handler(message, handle_report_message)

# === ОБРАБОТКА ОТПРАВЛЕННОГО СООБЩЕНИЯ ===
def handle_report_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_message = message.text

    save_report(user_id, username, user_message)
    notify_admin(user_id, username, user_message)

    bot.send_message(message.chat.id, "✅ Спасибо! Твоё сообщение отправлено админу.")

# === КОМАНДА ДЛЯ ПРОСМОТРА СООБЩЕНИЙ (ТОЛЬКО ДЛЯ АДМИНА) ===
@bot.message_handler(commands=['view_reports'])
def view_reports(message):
    admin_id = 123456789  # 👈 Замени на свой Telegram ID
    if message.from_user.id != admin_id:
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

# === ЕСЛИ СООБЩЕНИЕ НЕ РАСПОЗНАНО ===
@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    bot.reply_to(message, "Не понял команду. Напиши /help для списка команд.")

# === ЗАПУСК ===
init_db()
print("Бот запущен...")
bot.polling()
