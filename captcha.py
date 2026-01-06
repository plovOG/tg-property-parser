from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey

from keyboards import get_main_bot_keyboard, make_captcha_kb
from config import save_captcha, check_answer, save_user_city, get_user_city
import random
from datetime import datetime, timedelta
import logging
import asyncio

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для капчи
start_router = Router()

# Состояния FSM
class CaptchaStates(StatesGroup):
    waiting_for_captcha = State()
    waiting_for_city = State()

# Ключи для хранения данных в состоянии
BAN_UNTIL = "ban_until"
CAPTCHA_ANS = "captcha_ans"
ATTEMPTS = "attempts"
PASSED = "passed"
USER_CITY = "city"

def generate_captcha() -> tuple[int, int, int, str]:
    """
    Генерирует простую математическую капчу
    
    Returns:
        tuple: (число1, число2, правильный ответ, текст вопроса)
    """
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    operation = random.choice(['+', '-'])
    
    if operation == '+':
        correct = a + b
        question = f"{a} + {b} = ?"
    else:
        # Убеждаемся, что результат не отрицательный
        a, b = max(a, b), min(a, b)
        correct = a - b
        question = f"{a} - {b} = ?"
    
    return a, b, correct, question

async def check_ban(state: FSMContext) -> tuple[bool, str | None]:
    """
    Проверяет, забанен ли пользователь
    
    Args:
        state: Контекст состояния FSM
        
    Returns:
        tuple: (забанен ли, время до разбана или None)
    """
    try:
        data = await state.get_data()
        ban_str = data.get(BAN_UNTIL)
        
        if not ban_str:
            return False, None
        
        ban_until = datetime.fromisoformat(ban_str)
        now = datetime.now()
        
        if now < ban_until:
            time_left = ban_until - now
            total_seconds = int(time_left.total_seconds())
            
            if total_seconds >= 60:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                time_text = f"{minutes} мин {seconds} сек"
            else:
                time_text = f"{total_seconds} сек"
            
            return True, time_text
        
        # Время бана истекло, очищаем
        await state.update_data({BAN_UNTIL: None})
        return False, None
        
    except Exception as e:
        logger.error(f"Ошибка при проверке бана: {e}")
        return False, None

async def send_new_captcha(message_obj: Message | CallbackQuery, state: FSMContext, user_id: int):
    """
    Отправляет новую капчу пользователю
    
    Args:
        message_obj: Объект сообщения или callback
        state: Контекст состояния FSM
        user_id: ID пользователя
    """
    try:
        _, _, correct, question = generate_captcha()
        
        # Сохраняем текущие данные и обновляем правильный ответ
        current_data = await state.get_data()
        current_data[CAPTCHA_ANS] = correct
        await state.set_data(current_data)
        
        # Создаем клавиатуру с вариантами
        kb = make_captcha_kb(user_id, correct)
        
        # Формируем текст сообщения
        attempts = current_data.get(ATTEMPTS, 0)
        
        if attempts == 1:
            text = f"❌ Неверно! Осталась 1 попытка.\n\n{question}"
        else:
            text = f"{question}"
        
        # Отправляем сообщение
        if isinstance(message_obj, Message):
            await message_obj.answer(text, reply_markup=kb)
        else:
            await message_obj.message.edit_text(text, reply_markup=kb)
            
        # Логируем
        logger.info(f"Отправлена новая капча пользователю {user_id}, правильный ответ: {correct}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке новой капчи: {e}")

async def ban_user(state: FSMContext, minutes: int = 2):
    """
    Банит пользователя на указанное время
    
    Args:
        state: Контекст состояния FSM
        minutes: Количество минут для бана
    """
    try:
        ban_until = datetime.now() + timedelta(minutes=minutes)
        await state.update_data({
            BAN_UNTIL: ban_until.isoformat(),
            ATTEMPTS: 0  # Сбрасываем попытки
        })
        
        logger.info(f"Пользователь забанен до {ban_until}")
        
    except Exception as e:
        logger.error(f"Ошибка при бане пользователя: {e}")

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start
    
    Показывает капчу или главное меню, если капча уже пройдена
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} (ID: {user_id}) запустил бота")
    
    try:
        # Получаем текущие данные пользователя
        data = await state.get_data()
        
        # 1. Проверяем, прошел ли пользователь капчу навсегда
        if data.get(PASSED):
            logger.info(f"Пользователь {user_id} уже прошел капчу")
            
            # Пытаемся получить сохраненный город из базы данных
            saved_city = await get_user_city(user_id)
            if saved_city:
                await state.update_data({USER_CITY: saved_city})
                city_message = f"📍 Ваш город: {saved_city}\n\n"
            else:
                city_message = ""
            
            await message.answer(
                f"{city_message}✅ Добро пожаловать обратно, {message.from_user.first_name}!\n"
                "🏘️ Выберите действие:",
                reply_markup=get_main_bot_keyboard()
            )
            return
        
        # 2. Проверяем, не забанен ли пользователь
        banned, time_left = await check_ban(state)
        if banned:
            logger.warning(f"Пользователь {user_id} забанен, время до разбана: {time_left}")
            
            await message.answer(
                f"⛔ Вы заблокированы за ошибки в капче.\n"
                f"⏰ Осталось: {time_left}\n\n"
                f"Пожалуйста, подождите и попробуйте снова позже.\n"
                f"Перезапуск /start не поможет — нужно дождаться окончания блокировки.",
                reply_markup=None
            )
            return
        
        # 3. Генерируем новую капчу для пользователя
        _, _, correct, question = generate_captcha()
        
        # Инициализируем состояние пользователя
        await state.set_data({
            CAPTCHA_ANS: correct,
            ATTEMPTS: 0,
            PASSED: False,
            BAN_UNTIL: None,
            USER_CITY: None
        })
        
        # Сохраняем капчу в базу данных
        await save_captcha(user_id, correct)
        
        # Создаем клавиатуру с вариантами ответов
        kb = make_captcha_kb(user_id, correct)
        
        # Отправляем приветствие и капчу
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "🔐 Для доступа к функциям бота пройдите простую проверку:\n\n"
            f"*{question}*\n\n"
            "Выберите правильный ответ:",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        
        logger.info(f"Отправлена капча пользователю {user_id}, правильный ответ: {correct}")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}", exc_info=True)
        
        await message.answer(
            "❌ Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.",
            reply_markup=None
        )

@start_router.callback_query(F.data.startswith("cap:"))
async def process_captcha(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку капчи
    
    Проверяет ответ пользователя и либо пропускает дальше,
    либо показывает новую капчу, либо банит
    """
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    logger.info(f"Пользователь {username} (ID: {user_id}) ответил на капчу")
    
    try:
        # Парсим callback_data: "cap:user_id:answer"
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Ошибка в данных капчи", show_alert=True)
            return
        
        _, uid_str, ans_str = parts
        uid = int(uid_str)
        user_answer = int(ans_str)
        
        # Проверяем, что ответ принадлежит правильному пользователю
        if uid != user_id:
            await callback.answer("❌ Это не ваша капча!", show_alert=True)
            return
        
        # Проверяем, не забанен ли пользователь
        banned, time_left = await check_ban(state)
        if banned:
            await callback.message.edit_text(
                f"⛔ Вы заблокированы.\n⏰ Осталось: {time_left}\n\n"
                f"Пожалуйста, подождите и попробуйте снова позже.",
                reply_markup=None
            )
            await callback.answer("Вы заблокированы", show_alert=True)
            return
        
        # Получаем текущие данные пользователя
        data = await state.get_data()
        
        # Проверяем, не прошел ли уже пользователь капчу
        if data.get(PASSED):
            await callback.message.edit_text("✅ Проверка уже пройдена!", reply_markup=None)
            
            # Показываем главное меню
            await callback.message.answer(
                "🏘️ Добро пожаловать в бот недвижимости!\n"
                "📍 Для поиска недвижимости сначала выберите город",
                reply_markup=get_main_bot_keyboard()
            )
            await callback.answer("Вы уже прошли проверку!")
            return
        
        # Получаем правильный ответ
        correct_answer = data.get(CAPTCHA_ANS)
        attempts = data.get(ATTEMPTS, 0)
        
        # Проверяем ответ пользователя
        if user_answer == correct_answer:
            # ПРАВИЛЬНЫЙ ОТВЕТ
            logger.info(f"Пользователь {user_id} правильно ответил на капчу")
            
            # Отмечаем пользователя как прошедшего проверку
            await state.update_data({
                PASSED: True,
                ATTEMPTS: 0  # Сбрасываем счетчик попыток
            })
            
            # Обновляем сообщение с капчей
            await callback.message.edit_text(
                "✅ *Проверка пройдена успешно!*\n\n"
                "Добро пожаловать в бот недвижимости! 🏘️",
                reply_markup=None,
                parse_mode="Markdown"
            )
            
            # Показываем главное меню
            await callback.message.answer(
                "🏘️ *Добро пожаловать в бот недвижимости!*\n\n"
                "📍 Для поиска недвижимости сначала выберите город\n"
                "💰 Используйте ипотечный калькулятор для расчетов\n"
                "📞 Обращайтесь, если нужна помощь!",
                reply_markup=get_main_bot_keyboard(),
                parse_mode="Markdown"
            )
            
            await callback.answer("✅ Верно! Добро пожаловать!", show_alert=False)
            
        else:
            # НЕПРАВИЛЬНЫЙ ОТВЕТ
            logger.warning(f"Пользователь {user_id} ошибся в капче. Попытка {attempts + 1}")
            
            # Увеличиваем счетчик попыток
            attempts += 1
            await state.update_data({ATTEMPTS: attempts})
            
            if attempts >= 3:
                # 3 ошибки подряд - бан на 5 минут
                await ban_user(state, minutes=5)
                
                await callback.message.edit_text(
                    "⛔ *Три ошибки подряд!*\n\n"
                    "Вы заблокированы на 5 минут за подозрительную активность.\n\n"
                    "⏰ *Причина:* многократные неверные ответы\n"
                    "🔄 *Решение:* подождите и попробуйте снова позже",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                
                await callback.answer("🚫 Заблокирован на 5 минут", show_alert=True)
                
            elif attempts >= 2:
                # 2 ошибки - бан на 2 минуты
                await ban_user(state, minutes=2)
                
                await callback.message.edit_text(
                    "⚠️ *Две ошибки подряд!*\n\n"
                    "Вы заблокированы на 2 минуты.\n\n"
                    "🔄 Перезапуск /start не поможет — просто подождите.",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                
                await callback.answer("⏰ Заблокирован на 2 минуты", show_alert=True)
                
            else:
                # 1 ошибка - даем еще попытку
                await send_new_captcha(callback, state, user_id)
                await callback.answer("❌ Неверно! Попробуйте еще раз", show_alert=False)
    
    except ValueError:
        logger.error(f"Ошибка парсинга callback_data: {callback.data}")
        await callback.answer("❌ Ошибка в данных", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике капчи: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@start_router.message(Command("reset_captcha"))
async def cmd_reset_captcha(message: Message, state: FSMContext):
    """
    Сброс капчи (только для тестирования)
    """
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором или разработчиком
    # В реальном боте здесь должна быть проверка прав
    if user_id not in [123456789]:  # Замените на ID администраторов
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    # Сбрасываем состояние капчи
    await state.clear()
    
    await message.answer(
        "🔄 Состояние капчи сброшено.\n"
        "Теперь при следующем /start будет показана новая капча."
    )

@start_router.message(Command("status"))
async def cmd_status(message: Message, state: FSMContext):
    """
    Показывает статус пользователя (для отладки)
    """
    user_id = message.from_user.id
    data = await state.get_data()
    
    status_info = (
        f"📊 *Статус пользователя {user_id}:*\n\n"
        f"• Капча пройдена: {'✅ Да' if data.get(PASSED) else '❌ Нет'}\n"
        f"• Попытки: {data.get(ATTEMPTS, 0)}\n"
        f"• Город: {data.get(USER_CITY, 'Не выбран')}\n"
    )
    
    banned, time_left = await check_ban(state)
    if banned:
        status_info += f"• Статус: ⛔ Заблокирован (осталось: {time_left})\n"
    else:
        status_info += "• Статус: ✅ Активен\n"
    
    await message.answer(status_info, parse_mode="Markdown")

# Экспорт роутера
__all__ = ['start_router', 'CaptchaStates']