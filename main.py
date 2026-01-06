from aiogram import Bot, Dispatcher
import asyncio
import logging
from dotenv import load_dotenv
from config import TOKEN, init_db, DB_FILE
from captcha import start_router
from choose_category import category_router
from mortgage_bot import mortgage_router
import os

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключаем все роутеры
dp.include_router(start_router)      # Капча и начало работы
dp.include_router(category_router)   # Поиск недвижимости
dp.include_router(mortgage_router)   # Ипотечный калькулятор

async def main():
    """Главная функция запуска бота"""
    # Инициализируем базу данных, если её нет
    if not os.path.exists(DB_FILE):
        await init_db()
        logging.info("База данных инициализирована")
    
    logging.info("Бот запускается...")
    
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())