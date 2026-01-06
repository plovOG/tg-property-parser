import os
from dotenv import load_dotenv
from datetime import datetime
import aiosqlite

# Загружаем переменные окружения
load_dotenv()

# Конфигурационные переменные
TOKEN = os.getenv('TOKEN')  # Токен бота от @BotFather
DB_FILE = 'users.db'  # Файл базы данных
TELEGRAM_CHANNEL_URL = "https://t.me/Kluchi_gel_sochi"  # Ссылка на канал
    
async def init_db():
    """
    Инициализация базы данных.
    Создает таблицу пользователей, если она не существует.
    """
    async with aiosqlite.connect(DB_FILE) as db:
        # Создаем таблицу пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                passed INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                last_captcha INTEGER,
                captcha_time TIMESTAMP,
                city TEXT
            )
        ''')
        
        # Создаем таблицу для ипотечных расчетов (кеширование)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mortgage_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                calculation_type TEXT,
                parameters TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()
        print(f"База данных создана: {DB_FILE}")

async def user_passed(user_id: int) -> bool:
    """
    Проверяет, прошел ли пользователь капчу
    """
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT passed FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row and row[0] == 1)

async def save_captcha(user_id: int, correct: int):
    """
    Сохраняет данные капчи для пользователя
    """
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT INTO users (user_id, last_captcha, captcha_time, passed)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                last_captcha = excluded.last_captcha,
                captcha_time = excluded.captcha_time,
                passed = 0
        ''', (user_id, correct, datetime.now()))
        await db.commit()

async def check_answer(user_id: int, answer: int) -> bool:
    """
    Проверяет ответ на капчу и отмечает пользователя как прошедшего проверку
    """
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT last_captcha FROM users WHERE user_id = ? AND passed = 0", (user_id,)) as cur:
            row = await cur.fetchone()
            if row and row[0] == answer:
                await db.execute("UPDATE users SET passed = 1 WHERE user_id = ?", (user_id,))
                await db.commit()
                return True

    return False

async def save_user_city(user_id: int, city: str):
    """
    Сохраняет выбранный город пользователя
    """
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT INTO users (user_id, city)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                city = excluded.city
        ''', (user_id, city))
        await db.commit()

async def get_user_city(user_id: int) -> str:
    """
    Получает сохраненный город пользователя
    """
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT city FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def save_mortgage_calculation(user_id: int, calc_type: str, params: dict, result: dict):
    """
    Сохраняет результат расчета ипотеки для истории
    """
    import json
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT INTO mortgage_calculations (user_id, calculation_type, parameters, result)
            VALUES (?, ?, ?, ?)
        ''', (user_id, calc_type, json.dumps(params), json.dumps(result)))
        await db.commit()

async def get_mortgage_history(user_id: int, limit: int = 10):
    """
    Получает историю расчетов пользователя
    """
    import json
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute('''
            SELECT calculation_type, parameters, result, created_at 
            FROM mortgage_calculations 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit)) as cur:
            rows = await cur.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'type': row[0],
                    'parameters': json.loads(row[1]),
                    'result': json.loads(row[2]),
                    'date': row[3]
                })
            return history