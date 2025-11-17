import telebot
import sqlite3
import time
from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN)
user_last_message = {}

def init_db():
    with sqlite3.connect("messages.db") as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                text TEXT,
                status TEXT,
                admin_reply TEXT
            )
        """)
        conn.commit()

def save_report(user_id, username, text):
    with sqlite3.connect("messages.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO reports (user_id, username, text, status) VALUES (?, ?, ?, ?)",
                  (user_id, username, text, "new"))
        conn.commit()

def notify_admin(user_id, username, text):
    formatted = (
        "📨 *Новое сообщение*\n\n"
        f"👤 *От:* @{username or 'без имени'}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"💬 *Текст:* {text}"
    )
    bot.send_message(ADMIN_ID, formatted, parse_mode="Markdown")

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет 👋\n\n"
        "Если у тебя ограничен доступ в ТГ, можешь написать мне — я передам сообщение админу.\n\n"
        "Нажми /report чтобы отправить сообщение."
    )

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "📘 Команды:\n"
        "/start — начало\n"
        "/help — помощь\n"
        "/report — написать админу"
    )

@bot.message_handler(commands=["report"])
def report(message):
    bot.send_message(message.chat.id, "✏️ Напиши своё сообщение сюда.")
    bot.register_next_step_handler(message, handle_report)

def handle_report(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    text = message.text

    now = time.time()
    if user_id in user_last_message and now - user_last_message[user_id] < 10:
        return bot.send_message(message.chat.id, "⏳ Подожди немного перед следующей отправкой.")
    user_last_message[user_id] = now

    save_report(user_id, username, text)
    notify_admin(user_id, username, text)

    bot.send_message(
        message.chat.id,
        "✅ Сообщение отправлено админу. Ожидай ответа."
    )

@bot.message_handler(commands=["view"])
def view(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "🚫 Нет доступа.")
    
    with sqlite3.connect("messages.db") as conn:
        c = conn.cursor()
        c.execute("SELECT id, user_id, username, text FROM reports WHERE status='new'")
        data = c.fetchall()

    if not data:
        return bot.send_message(message.chat.id, "📭 Новых сообщений нет.")

    for row in data:
        rid, uid, uname, text = row
        bot.send_message(
            message.chat.id,
            f"📥 *ID отчёта:* `{rid}`\n"
            f"👤 @{uname}\n"
            f"🆔 {uid}\n"
            f"💬 {text}",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=["reply"])
def reply(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "🚫 Нет доступа.")

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return bot.send_message(message.chat.id, "Использование: /reply user_id текст")

    user_id = parts[1]
    text = parts[2]

    try:
        bot.send_message(int(user_id), f"📬 *Ответ от админа:*\n{text}", parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ Ответ отправлен.")
    except:
        bot.send_message(message.chat.id, "⚠️ Не удалось отправить сообщение пользователю.")

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(message.chat.id, "Не понял. Используй /help.")

init_db()
bot.polling()
