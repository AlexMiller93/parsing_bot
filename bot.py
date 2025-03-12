import os
import sqlite3
import pandas as pd

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, 
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler,
    filters
    )

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Подключение к базе данных SQLite
def init_db():
    conn = sqlite3.connect('items.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            xpath TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton("Загрузить файл")
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Загрузите файл Excel с данными о сайтах для парсинга.", reply_markup=keyboard)


# Обработчик получения файла
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # file = update.message.document.get_file()
        # file_path = f"downloads/{update.message.document.file_id}.xlsx"

        # print(file)

        # # Создаем папку для загрузок, если она не существует
        # if not os.path.exists('downloads'):
        #     os.makedirs('downloads')

        # await file.download_to_drive(file_path)

        file = await context.bot.get_file(update.message.document)

        print(f'File: {file}')
        file_path = f"downloads/{update.message.document.file_id}.xlsx"
        await file.download_to_drive(file_path)

        # Открываем файл с помощью pandas
        df = pd.read_excel(file_path)

        # Выводим содержимое файла
        response = df.to_string(index=False)
        await update.message.reply_text(f"Содержимое файла:\n{response}")

        # Сохраняем данные в базу данных
        conn = init_db()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO items (title, url, xpath) VALUES (?, ?, ?)
            ''', (row['title'], row['url'], row['xpath']))
        conn.commit()
        conn.close()

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")
        print(str(e))


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == '__main__':
    main()