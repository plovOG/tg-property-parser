from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import logging
from typing import Dict, List, Any, Optional

from keyboards import (
    make_subcategory_keyboard, quarters, houses, newbuildings, 
    land_plots, commercial, make_main_keyboard, make_property_keyboard, 
    back_kb, keyboard_of_cities, cities, make_city_selector_keyboard,
    get_main_bot_keyboard, get_about_keyboard, get_contact_keyboard,
    get_help_keyboard
)
from textformat import format_property_message, format_error_message, format_success_message
from parse_cards import fix_url, fetch_properties
from config import save_user_city, get_user_city

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для категорий
category_router = Router()

# Состояния FSM
class CategoryStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_category = State()
    waiting_for_subcategory = State()

# Вспомогательные функции
async def get_user_city_from_state(state: FSMContext) -> Optional[str]:
    """Получает город пользователя из состояния"""
    data = await state.get_data()
    return data.get('city')

async def save_city_to_state_and_db(user_id: int, city: str, state: FSMContext):
    """Сохраняет город в состояние и базу данных"""
    await state.update_data({'city': city})
    await save_user_city(user_id, city)
    logger.info(f"Город '{city}' сохранен для пользователя {user_id}")

# Обработчики команд
@category_router.message(Command("start"))
async def cmd_start_after_captcha(message: Message, state: FSMContext):
    """
    Главное меню после прохождения капчи
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} (ID: {user_id}) в главном меню")
    
    try:
        # Проверяем, прошел ли пользователь капчу
        data = await state.get_data()
        if not data.get('passed', False):
            await message.answer(
                "🔐 Сначала пройдите проверку безопасности.\n"
                "Используйте команду /start для начала работы."
            )
            return
        
        # Получаем сохраненный город из базы данных
        saved_city = await get_user_city(user_id)
        if saved_city:
            await state.update_data({'city': saved_city})
            city_message = f"📍 Ваш город: *{saved_city}*\n\n"
        else:
            city_message = "📍 Сначала выберите город для поиска недвижимости\n\n"
        
        await message.answer(
            f"{city_message}🏘️ *Добро пожаловать в бот недвижимости!*\n\n"
            "Выберите действие:",
            reply_markup=get_main_bot_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в главном меню: {e}", exc_info=True)
        await message.answer(
            format_error_message("Не удалось загрузить главное меню. Попробуйте позже.")
        )

@category_router.message(Command("city"))
async def cmd_city(message: Message, state: FSMContext):
    """
    Команда для выбора/смены города
    """
    await message.answer(
        "📍 *Выберите город для поиска недвижимости:*",
        reply_markup=keyboard_of_cities(),
        parse_mode="Markdown"
    )

@category_router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Справка по использованию бота
    """
    help_text = (
        "🆘 *Помощь по использованию бота:*\n\n"
        
        "🏘️ *Поиск недвижимости:*\n"
        "1. Выберите город\n"
        "2. Выберите тип недвижимости\n"
        "3. Выберите подкатегорию\n"
        "4. Просматривайте предложения\n\n"
        
        "🏦 *Ипотечный калькулятор:*\n"
        "• Рассчитайте ежемесячный платеж\n"
        "• Узнайте, сколько можете взять по доходу\n"
        "• Сравните разные варианты\n"
        "• Рассчитайте досрочное погашение\n\n"
        
        "📋 *Основные команды:*\n"
        "• /start - Главное меню\n"
        "• /city - Выбрать город\n"
        "• /help - Эта справка\n"
        "• /debug - Отладочная информация\n\n"
        
        "📞 *Поддержка:*\n"
        "Если у вас возникли проблемы, используйте раздел 'О нас'"
    )
    
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_help_keyboard())

@category_router.message(Command("debug"))
async def cmd_debug(message: Message, state: FSMContext):
    """
    Отладочная информация
    """
    user_id = message.from_user.id
    data = await state.get_data()
    
    # Проверяем доступ к отладке (например, только для администраторов)
    # В реальном боте здесь должна быть проверка прав
    
    debug_info = (
        f"🐛 *Отладочная информация:*\n\n"
        f"• User ID: `{user_id}`\n"
        f"• Капча пройдена: {'✅' if data.get('passed') else '❌'}\n"
        f"• Город: {data.get('city', 'Не выбран')}\n"
        f"• Состояние: {await state.get_state()}\n"
        f"• Данные: `{data}`\n\n"
        
        f"🔧 *Тестирование парсера:*\n"
        f"Используйте кнопки ниже для проверки работы парсера"
    )
    
    # Создаем отладочную клавиатуру
    debug_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Тест парсера (студии)", callback_data="debug_parse_studios")],
        [InlineKeyboardButton(text="📍 Тест фильтра по городу", callback_data="debug_city_filter")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="debug_stats")],
        [InlineKeyboardButton(text="🔄 Сброс состояния", callback_data="debug_reset")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")]
    ])
    
    await message.answer(debug_info, parse_mode="Markdown", reply_markup=debug_kb)

# Обработчики callback-запросов для главного меню
@category_router.callback_query(F.data == "search_real_estate")
async def search_real_estate_handler(call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Поиск недвижимости"
    """
    user_id = call.from_user.id
    
    try:
        # Получаем город пользователя
        current_city = await get_user_city_from_state(state)
        
        if current_city:
            await call.message.edit_text(
                f"📍 *Текущий город: {current_city}*\n\n"
                "🏘️ *Выберите тип недвижимости:*",
                reply_markup=make_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await call.message.edit_text(
                "📍 *Сначала выберите город для поиска недвижимости:*",
                reply_markup=keyboard_of_cities(),
                parse_mode="Markdown"
            )
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при переходе к поиску недвижимости: {e}")
        await call.message.answer(format_error_message(str(e)))
        await call.answer("❌ Произошла ошибка")

@category_router.callback_query(F.data == "mortgage_calculator")
async def mortgage_calculator_handler(call: CallbackQuery):
    """
    Обработчик кнопки "Ипотечный калькулятор"
    """
    from mortgage_bot import get_mortgage_main_keyboard
    
    await call.message.edit_text(
        "🏦 *Ипотечный калькулятор*\n\n"
        "Выберите тип расчета:",
        reply_markup=get_mortgage_main_keyboard(),
        parse_mode="Markdown"
    )
    await call.answer()

@category_router.callback_query(F.data == "about_us")
async def about_us_handler(call: CallbackQuery):
    """
    Обработчик кнопки "О нас"
    """
    await call.message.answer(
        "🏘️ *Агентство недвижимости «Ключи»*\n\n"
        
        "✅ *Наши преимущества:*\n"
        "• 10+ лет на рынке недвижимости\n"
        "• 5000+ довольных клиентов\n"
        "• Полное сопровождение сделок\n"
        "• Юридическая проверка объектов\n"
        "• Помощь в получении ипотеки\n\n"
        
        "📞 *Контактная информация:*\n"
        "• Телефоны:\n"
        "  `8 800 222-20-89`\n"
        "  `8 928 202-80-60`\n\n"
        
        "• Email:\n"
        "Геленджик: kluchi-gel@mail.ru\n"
        "Новороссийск: kluchi-novoross@mail.ru\n"
        "Сочи: kluchi-sochi@mail.ru\n"
        "• Сайт: https://www.xn----htbkhfjn2e0c.xn--p1ai/\n\n"
        
        "⏰ *Часы работы офиса:*\n"
        "• Пн-Пт: 9:00-19:00\n"
        "• Сб: 10:00-17:00\n"
        "• Вс: выходной\n\n"
        
        "📍 *Адреса наших офисов*\n"
        "г. Геленджик, Крымская улица, 19, корп. 3\n"
        "г. Новороссийск, Пионерская улица, 43\n"
        "г. Сочи, Пластунская улица, 92\n\n"

        "💼 *Наши услуги:*\n"
        "• Продажа/покупка недвижимости\n"
        "• Аренда жилья и коммерции\n"
        "• Ипотечное консультирование\n"
        "• Юридическое сопровождение\n"
        "• Оценка недвижимости",
        reply_markup=get_about_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@category_router.callback_query(F.data == "contact_us")
async def contact_us_handler(call: CallbackQuery):
    """
    Обработчик кнопки "Связаться с нами"
    """
    await call.message.answer(
        "📞 *Свяжитесь с нами удобным способом:*\n\n"
        
        "💬 *Быстрые контакты:*\n"
        "• WhatsApp: +7 928 202-80-60\n"
        "• Telegram: @kluchi_support\n"
        "• Viber: +7 928 202-80-60\n\n"
        
        "📋 *Заказать обратный звонок:*\n"
        "Мы перезвоним вам в удобное время\n\n"
        
        "👨‍💼 *Консультация специалиста:*\n"
        "Получите бесплатную консультацию\nпо вопросам недвижимости\n\n"
        
        "📍 *Посетите наши офисы:*\n"
        "г. Геленджик, Крымская улица, 19, корп. 3\n"
        "г. Новороссийск, Пионерская улица, 43\n"
        "г. Сочи, Пластунская улица, 92\n\n"
        "Работаем: Пн-Пт 9:00-19:00, Сб 10:00-17:00",
        reply_markup=get_contact_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@category_router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(call: CallbackQuery, state: FSMContext):
    """
    Возврат в главное меню бота
    """
    user_id = call.from_user.id
    
    try:
        # Получаем город пользователя
        saved_city = await get_user_city(user_id)
        
        if saved_city:
            await state.update_data({'city': saved_city})
            city_message = f"📍 Ваш город: *{saved_city}*\n\n"
        else:
            city_message = ""
        
        await call.message.edit_text(
            f"{city_message}🏘️ *Главное меню*\n\nВыберите действие:",
            reply_markup=get_main_bot_keyboard(),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        await call.message.answer("❌ Произошла ошибка")
        await call.answer()

# Обработчики выбора города
@category_router.callback_query(F.data.startswith("city_"))
async def city_handler(call: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора города
    """
    user_id = call.from_user.id
    city_code = call.data.replace("city_", "")
    
    try:
        # Находим название города по коду
        city_name = None
        for name, code in cities.items():
            if code == city_code:
                city_name = name
                break
        
        if not city_name:
            await call.answer("❌ Город не найден", show_alert=True)
            return
        
        # Сохраняем город
        await save_city_to_state_and_db(user_id, city_name, state)
        
        logger.info(f"Пользователь {user_id} выбрал город: {city_name}")
        
        await call.message.edit_text(
            f"✅ *Город выбран: {city_name}*\n\n"
            "🏘️ Теперь выберите тип недвижимости:",
            reply_markup=make_main_keyboard(),
            parse_mode="Markdown"
        )
        await call.answer(f"📍 Выбран город: {city_name}")
        
    except Exception as e:
        logger.error(f"Ошибка при выборе города: {e}")
        await call.answer("❌ Ошибка при выборе города", show_alert=True)

@category_router.callback_query(F.data == "select_city")
async def select_city_handler(call: CallbackQuery):
    """
    Обработчик для выбора города из меню
    """
    await call.message.edit_text(
        "📍 *Выберите город для поиска недвижимости:*",
        reply_markup=keyboard_of_cities(),
        parse_mode="Markdown"
    )
    await call.answer()

@category_router.callback_query(F.data == "change_city")
async def change_city_handler(call: CallbackQuery):
    """
    Обработчик для смены города
    """
    await call.message.edit_text(
        "📍 *Выберите новый город:*",
        reply_markup=keyboard_of_cities(),
        parse_mode="Markdown"
    )
    await call.answer()

@category_router.callback_query(F.data == "change_city_main")
async def change_city_main_handler(call: CallbackQuery):
    """
    Обработчик для смены города из главного меню
    """
    await call.message.edit_text(
        "📍 *Выберите город для поиска недвижимости:*",
        reply_markup=keyboard_of_cities(),
        parse_mode="Markdown"
    )
    await call.answer()

# Обработчики категорий недвижимости
@category_router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(call: CallbackQuery, state: FSMContext):
    """
    Возврат к основным категориям
    """
    try:
        current_city = await get_user_city_from_state(state)
        
        if current_city:
            await call.message.edit_text(
                f"📍 *Текущий город: {current_city}*\n\n"
                "🏘️ *Выберите тип недвижимости:*",
                reply_markup=make_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await call.message.edit_text(
                "📍 *Сначала выберите город для поиска недвижимости:*",
                reply_markup=keyboard_of_cities(),
                parse_mode="Markdown"
            )
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при возврате к категориям: {e}")
        await call.answer("❌ Произошла ошибка")

@category_router.callback_query(F.data.startswith("cat_"))
async def category_handler(call: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора основной категории
    """
    category_type = call.data.replace("cat_", "")
    user_id = call.from_user.id
    
    try:
        # Проверяем, выбран ли город
        current_city = await get_user_city_from_state(state)
        
        if not current_city:
            await call.answer("📍 Сначала выберите город!", show_alert=True)
            await call.message.edit_text(
                "📍 *Сначала выберите город для поиска недвижимости:*",
                reply_markup=keyboard_of_cities(),
                parse_mode="Markdown"
            )
            return
        
        # Определяем, какую клавиатуру показать
        if category_type == "kvartiry":
            kb = make_subcategory_keyboard(quarters)
            category_text = "🏠 Квартиры"
            
        elif category_type == "doma":
            kb = make_subcategory_keyboard(houses)
            category_text = "🏡 Дома"
            
        elif category_type == "novostroyki":
            kb = make_subcategory_keyboard(newbuildings)
            category_text = "🏗️ Новостройки"
            
        elif category_type == "zemelnie_uchastki":
            kb = make_subcategory_keyboard(land_plots)
            category_text = "🏞️ Земельные участки"
            
        elif category_type == "commercy":
            kb = make_subcategory_keyboard(commercial)
            category_text = "🏢 Коммерческая недвижимость"
            
        else:
            await call.answer("❌ Категория не найдена", show_alert=True)
            return
        
        logger.info(f"Пользователь {user_id} выбрал категорию: {category_text} в городе {current_city}")
        
        await call.message.edit_text(
            f"📍 *Город: {current_city}*\n\n"
            f"*{category_text}:*\nВыберите подкатегорию:",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе категории: {e}")
        await call.answer("❌ Произошла ошибка", show_alert=True)

@category_router.callback_query(F.data.startswith("sub_"))
async def subcategory_handler(call: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора подкатегории с фильтрацией по городу
    """
    subcategory_name = call.data.replace("sub_", "")
    user_id = call.from_user.id
    
    try:
        # Получаем выбранный город
        selected_city = await get_user_city_from_state(state)
        
        if not selected_city:
            await call.answer("📍 Сначала выберите город!", show_alert=True)
            await call.message.edit_text(
                "📍 *Сначала выберите город для поиска недвижимости:*",
                reply_markup=keyboard_of_cities(),
                parse_mode="Markdown"
            )
            return
        
        # Определяем URL в зависимости от подкатегории
        url = None
        
        if subcategory_name in quarters:
            url = quarters[subcategory_name]
            property_type = "квартиры"
            
        elif subcategory_name in houses:
            url = houses[subcategory_name]
            property_type = "дома"
            
        elif subcategory_name in newbuildings:
            url = newbuildings[subcategory_name]
            property_type = "новостройки"
            
        elif subcategory_name in land_plots:
            url = land_plots[subcategory_name]
            property_type = "земельные участки"
            
        elif subcategory_name in commercial:
            url = commercial[subcategory_name]
            property_type = "коммерческая недвижимость"
        
        if not url:
            await call.answer("❌ Категория не найдена", show_alert=True)
            return
        
        logger.info(f"Пользователь {user_id} ищет {property_type}: {subcategory_name} в {selected_city}")
        
        # Показываем сообщение о начале поиска
        await call.message.edit_text(
            f"📍 *Фильтр: {selected_city}*\n"
            f"🔍 *Ищу {subcategory_name}...*\n\n"
            f"⏳ *Это может занять несколько секунд*\n"
            f"Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        # Парсим свойства с фильтрацией по городу
        properties = await fetch_properties(url, selected_city)
        
        if not properties:
            logger.warning(f"Не найдено объектов '{subcategory_name}' в городе {selected_city}")
            
            await call.message.answer(
                f"📍 *Город: {selected_city}*\n"
                f"❌ *Не найдено объектов '{subcategory_name}' в выбранном городе.*\n\n"
                f"*Попробуйте:*\n"
                f"• Выбрать другой город\n"
                f"• Выбрать другую категорию\n"
                f"• Или посмотреть все объекты: {fix_url(url)}",
                reply_markup=back_kb,
                parse_mode="Markdown"
            )
            await call.answer()
            return
        
        # Отправляем карточки недвижимости
        sent_count = 0
        max_cards = min(len(properties), 8)  # Максимум 8 карточек
        
        logger.info(f"Найдено {len(properties)} объектов, отправляю {max_cards}")
        
        for prop in properties[:max_cards]:
            try:
                message_text = format_property_message(prop, subcategory_name)
                property_keyboard = make_property_keyboard(prop['link'])
                
                logger.debug(f"Отправка карточки: {prop.get('title', 'Без названия')[:50]}...")
                
                if prop.get('image'):
                    await call.message.answer_photo(
                        photo=prop['image'],
                        caption=message_text,
                        reply_markup=property_keyboard,
                        parse_mode='MarkdownV2'
                    )
                else:
                    await call.message.answer(
                        message_text,
                        reply_markup=property_keyboard,
                        parse_mode='MarkdownV2'
                    )
                
                sent_count += 1
                await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
                
            except Exception as e:
                logger.error(f"Ошибка при отправке карточки: {e}")
        
        # Итоговое сообщение
        if sent_count > 0:
            await call.message.answer(
                f"✅ *Найдено {sent_count} объектов в {selected_city}*\n\n"
                "Выберите следующее действие:",
                reply_markup=back_kb,
                parse_mode="Markdown"
            )
        else:
            await call.message.answer(
                f"❌ *Не удалось загрузить объекты*\n\n"
                f"Попробуйте позже или выберите другую категорию.",
                reply_markup=back_kb,
                parse_mode="Markdown"
            )
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике подкатегории: {e}", exc_info=True)
        await call.message.answer(
            format_error_message("Произошла ошибка при поиске недвижимости. Попробуйте позже.")
        )
        await call.answer("❌ Произошла ошибка")

# Обработчики для раздела "О нас"
@category_router.callback_query(F.data == "call_us")
async def call_us_handler(call: CallbackQuery):
    """
    Обработчик кнопки "Позвонить нам"
    """
    await call.message.answer(
        "📞 *Телефоны для связи:*\n\n"
        "• Общий: `8 800 222-20-89`\n"
        "• Мобильный: `8 928 202-80-60`\n\n"
        "💬 *Мессенджеры:*\n"
        "• WhatsApp: +7 928 202-80-60\n"
        "• Telegram: @AgentstvoKluchi\n\n"
        "⏰ *Часы работы call-центра:*\n"
        "• Пн-Пт: 8:00-20:00\n"
        "• Сб-Вс: 9:00-18:00",
        parse_mode="HTML"
    )
    await call.answer()

@category_router.callback_query(F.data == "our_office_map")
async def our_office_map_handler(call: CallbackQuery):
    """
    Обработчик кнопки "Наш офис на карте"
    """
    await call.message.answer(
        "📍 *Наши офисы на карте:*\n\n"
        "Адреса:\n"
        "г. Геленджик, Крымская улица, 19, корп. 3\n"
        "г. Новороссийск, Пионерская улица, 43\n"
        "г. Сочи, Пластунская улица, 92\n\n"
        "🕒 *Часы работы офиса:*\n"
        "• Пн-Пт: 9:00-19:00\n"
        "• Сб: 10:00-17:00\n"
        "• Вс: выходной\n\n"
        "📸 *Фото офиса:*\n"
        "Посмотрите фото нашего офиса на сайте",
        parse_mode="Markdown"
    )
    await call.answer()

@category_router.callback_query(F.data == "write_email")
async def write_email_handler(call: CallbackQuery):
    """
    Обработчик кнопки "Написать email"
    """
    await call.message.answer(
        "📧 *Электронная почта:*\n\n"
        "• Геленджик: kluchi-gel@mail.ru\n"
        "• Новороссийск: kluchi-novoross@mail.ru\n"
        "• Сочи: kluchi-sochi@mail.ru\n"
        "📋 *Рекомендуем указать в письме:*\n"
        "1. Ваше имя и контакты\n"
        "2. Тип недвижимости\n"
        "3. Бюджет\n"
        "4. Желаемый район\n\n"
        "⏱️ *Время ответа:*\n"
        "Обычно отвечаем в течение 2 часов\nв рабочие дни",
        parse_mode="Markdown"
    )
    await call.answer()

# Отладочные обработчики
@category_router.callback_query(F.data == "debug_parse_studios")
async def debug_parse_studios_handler(call: CallbackQuery, state: FSMContext):
    """
    Тестирование парсера (студии)
    """
    await call.answer("🔄 Тестирую парсер...", show_alert=False)
    
    test_url = "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/ctudii/"
    
    try:
        # Парсим без фильтра
        all_props = await fetch_properties(test_url, None)
        
        # Парсим с фильтром по городам
        sochi_props = await fetch_properties(test_url, "Сочи")
        gel_props = await fetch_properties(test_url, "Геленджик")
        nov_props = await fetch_properties(test_url, "Новороссийск")
        
        current_city = await get_user_city_from_state(state)
        
        debug_result = (
            f"🐛 *Результаты теста парсера:*\n\n"
            f"• Всего карточек на странице: *{len(all_props)}*\n"
            f"• С фильтром 'Сочи': *{len(sochi_props)}*\n"
            f"• С фильтром 'Геленджик': *{len(gel_props)}*\n"
            f"• С фильтром 'Новороссийск': *{len(nov_props)}*\n\n"
            f"• Ваш текущий город: *{current_city or 'Не выбран'}*\n\n"
            f"📊 *Примеры найденных городов:*\n"
        )
        
        # Показываем города из первых 5 карточек
        for i, prop in enumerate(all_props[:5], 1):
            debug_result += f"{i}. {prop.get('city', 'Не определен')}: {prop.get('title', '')[:30]}...\n"
        
        await call.message.answer(debug_result, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании парсера: {e}")
        await call.message.answer(f"❌ Ошибка: {str(e)}")

@category_router.callback_query(F.data == "debug_city_filter")
async def debug_city_filter_handler(call: CallbackQuery):
    """
    Тестирование фильтра по городу
    """
    await call.answer("🔍 Тестирую фильтр городов...")
    
    from parse_cards import debug_card_structure
    
    test_url = "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/ctudii/"
    
    try:
        cards_count = await debug_card_structure(test_url)
        
        await call.message.answer(
            f"🔍 *Анализ структуры карточек:*\n\n"
            f"• Найдено карточек: *{cards_count}*\n"
            f"• HTML сохранен в *debug_card.html*\n\n"
            f"📋 *Следующие шаги:*\n"
            f"1. Проверьте файл debug_card.html\n"
            f"2. Найдите элементы с городами\n"
            f"3. Обновите функцию detect_city_in_property",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе структуры: {e}")
        await call.message.answer(f"❌ Ошибка: {str(e)}")

@category_router.callback_query(F.data == "debug_stats")
async def debug_stats_handler(call: CallbackQuery, state: FSMContext):
    """
    Статистика пользователя
    """
    data = await state.get_data()
    
    stats = (
        f"📊 *Статистика пользователя:*\n\n"
        f"• ID: `{call.from_user.id}`\n"
        f"• Username: @{call.from_user.username or 'нет'}\n"
        f"• Имя: {call.from_user.first_name}\n"
        f"• Фамилия: {call.from_user.last_name or 'нет'}\n\n"
        
        f"⚙️ *Настройки:*\n"
        f"• Город: {data.get('city', 'Не выбран')}\n"
        f"• Капча пройдена: {'✅' if data.get('passed') else '❌'}\n"
        f"• Попытки капчи: {data.get('ATTEMPTS', 0)}\n\n"
        
        f"📅 *Дата регистрации:*\n"
        f"{(call.from_user.id >> 22) + 1420070400000}"
    )
    
    await call.message.answer(stats, parse_mode="Markdown")
    await call.answer()

@category_router.callback_query(F.data == "debug_reset")
async def debug_reset_handler(call: CallbackQuery, state: FSMContext):
    """
    Сброс состояния пользователя
    """
    # Только для администраторов (проверка в реальном боте)
    
    await state.clear()
    
    await call.message.answer(
        "🔄 *Состояние сброшено!*\n\n"
        "Все данные пользователя очищены.\n"
        "При следующем /start будет показана капча.",
        parse_mode="Markdown"
    )
    await call.answer("✅ Состояние сброшено")

# Экспорт роутера

__all__ = ['category_router', 'CategoryStates']
