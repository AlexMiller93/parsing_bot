import logging
import os
import sqlite3
import pandas as pd

from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update
    )

from telegram.ext import (
    ContextTypes, 
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler,
    CallbackQueryHandler,
    filters
    )

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    keyboard = [
        [InlineKeyboardButton("Загрузить файл Excel", callback_data='upload_file')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Нажмите кнопку ниже, чтобы загрузить файл Excel со столбцами title, url и xpath.", 
        reply_markup=reply_markup)

# Обработчик нажатия на кнопку
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  
    await query.edit_message_text(text="Пожалуйста, прикрепите файл Excel.")

# Обработчик получения файла
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await context.bot.get_file(update.message.document)

        # print(f'File: {file}')
        file_path = f"downloads/{update.message.document.file_id}.xlsx"
        await file.download_to_drive(file_path)

        # Открываем файл с помощью pandas
        df = pd.read_excel(file_path)

        # Проверка наличия необходимых столбцов
        required_columns = ['title', 'url', 'xpath']  
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            await update.message.reply_text(f"Ошибка: отсутствуют необходимые столбцы: {', '.join(missing_columns)}.")
            return

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


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback, pattern='upload_file'))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == '__main__':
    main()