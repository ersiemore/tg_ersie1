import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! 👋 Я бот проекта SmartNation. Напиши /help, чтобы узнать, что я умею.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "📋 Доступные команды:\n/start — начать\n/help — помощь\n/info — информация о проекте")

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, "Этот бот создан как часть учебного проекта. Автор: ersiemore.")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

print("Бот запущен...")
bot.polling()
