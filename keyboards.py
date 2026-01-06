from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TELEGRAM_CHANNEL_URL
import random

# ========== ДАННЫЕ ДЛЯ КАТЕГОРИЙ НЕДВИЖИМОСТИ ==========

# Основные категории недвижимости
categories = {
    "🏠 Квартиры": "kvartiry",
    "🏡 Дома": "doma", 
    "🏗️ Новостройки": "novostroyki",
    "🏞️ Земельные участки": "zemelnie_uchastki",
    "🏢 Коммерческая недвижимость": "commercy"
}

# Подкатегории для квартир
quarters = {
    "Студии": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/ctudii/",
    "Комнаты": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/komnaty/",
    "1-комнатные": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/odnokomnatnye/",
    "2-комнатные": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/dvukhkomnatnye/",
    "3-комнатные": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/3-komnatnye/",
    "4-комнатные": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/4-komnatnye/",
    "5+ комнат": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/5-komnat/"
}

# Подкатегории для домов
houses = {
    "Дома бизнес-класс": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/doma/doma-biznes-klass/",
    "Дуплекс": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/doma/dupleks/",
    "Коттеджи": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/doma/kottedzhi/",
    "Таунхаус": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/doma/taunkhaus/",
    "Часть дома": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/doma/chast-doma/",
    "Дома эконом-класса": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/doma/doma-ekonom-klassa/"
}

# Подкатегории для новостроек
newbuildings = {
    "Бизнес-класса": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/novostroyki/biznes-klassa/",
    "Новостройки эконом-класса": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/novostroyki/novostroyki-ekonom-klassa/"
}

# Земельные участки (без подкатегорий)
land_plots = {
    "Земельные участки": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/zemelnye-uchastki/"
}

# Коммерческая недвижимость (без подкатегорий)
commercial = {
    "Коммерческая недвижимость": "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kommercheskaya-nedvizhimost/"
}

# Города для поиска
cities = {
    "Сочи": "Sochi",
    "Геленджик": "Gelendzhik",
    "Новороссийск": "Novorosiisk"
}

# ========== КЛАВИАТУРЫ ДЛЯ ПОИСКА НЕДВИЖИМОСТИ ==========

def keyboard_of_cities():
    """
    Создает клавиатуру для выбора города
    """
    buttons = []
    for name, callback_data in cities.items():
        # Каждая кнопка - отдельный ряд
        buttons.append([InlineKeyboardButton(
            text=f"📍 {name}",
            callback_data=f"city_{callback_data}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def make_main_keyboard():
    """
    Создает главную клавиатуру для выбора категории недвижимости
    """
    buttons = []
    # Добавляем кнопки для каждой категории
    for name, callback_data in categories.items():
        buttons.append([InlineKeyboardButton(
            text=name, 
            callback_data=f"cat_{callback_data}"
        )])
    
    # Кнопка для выбора/смены города
    buttons.append([InlineKeyboardButton(
        text="📍 Выбрать/сменить город",
        callback_data="select_city"
    )])
    
    # Кнопка с ссылкой на Telegram-канал
    buttons.append([InlineKeyboardButton(
        text="📢 Наш Telegram канал",
        url=TELEGRAM_CHANNEL_URL
    )])
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(
        text="⬅️ Главное меню",
        callback_data="back_to_main_menu"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def make_subcategory_keyboard(subcategories_dict, back_button=True):
    """
    Создает клавиатуру подкатегорий
    
    Args:
        subcategories_dict: словарь с подкатегориями
        back_button: показывать ли кнопку "Назад"
    """
    buttons = []
    # Создаем кнопки для каждой подкатегории
    for name in subcategories_dict.keys():
        buttons.append([InlineKeyboardButton(
            text=name,
            callback_data=f"sub_{name}"
        )])
    
    # Добавляем кнопку "Назад", если нужно
    if back_button:
        buttons.append([InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back_to_main_menu"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def make_property_keyboard(property_link):
    """
    Создает клавиатуру для карточки недвижимости
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        # Кнопка для перехода на сайт с подробной информацией
        [InlineKeyboardButton(
            text="🔗 Подробнее на сайте", 
            url=property_link
        )],
        # Кнопка для смены города
        [InlineKeyboardButton(
            text="📍 Сменить город", 
            callback_data="change_city"
        )],
        # Кнопка для возврата к категориям
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")]
    ])

def make_city_selector_keyboard():
    """
    Клавиатура для быстрого выбора/смены города
    """
    buttons = []
    # Кнопки для каждого города
    for name, callback_data in cities.items():
        buttons.append([InlineKeyboardButton(
            text=f"📍 {name}",
            callback_data=f"city_{callback_data}"
        )])
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(
        text="⬅️ Главное меню",
        callback_data="back_to_main_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Простая клавиатура "Назад"
back_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main_menu")]
])

# ========== КЛАВИАТУРЫ ДЛЯ КАПЧИ ==========

def make_captcha_kb(user_id: int, correct: int):
    """
    Создает клавиатуру с вариантами ответов для капчи
    
    Args:
        user_id: ID пользователя (встраивается в callback_data)
        correct: правильный ответ
    """
    # Создаем варианты ответов
    options = [
        correct,  # Правильный ответ
        correct + random.randint(1, 10),  # Неправильный (больше)
        max(0, correct - random.randint(1, 10)),  # Неправильный (меньше)
        correct + random.randint(5, 15)  # Неправильный (значительно больше)
    ]
    
    # Перемешиваем варианты
    random.shuffle(options)
    
    # Создаем клавиатуру
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    
    # Распределяем кнопки по 2 в ряд
    for opt in options:
        # В callback_data передаем user_id и выбранный ответ
        row.append(InlineKeyboardButton(
            text=str(opt), 
            callback_data=f"cap:{user_id}:{opt}"
        ))
        
        # Если в ряду уже 2 кнопки, добавляем ряд в клавиатуру
        if len(row) == 2:
            kb.inline_keyboard.append(row)
            row = []
    
    # Если осталась неполная строка, добавляем её
    if row:
        kb.inline_keyboard.append(row)
    
    return kb

# ========== КЛАВИАТУРЫ ДЛЯ ИПОТЕЧНОГО КАЛЬКУЛЯТОРА ==========

def get_mortgage_main_keyboard():
    """
    Главная клавиатура ипотечного калькулятора
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Рассчитать платеж", callback_data="calc_payment")],
        [InlineKeyboardButton(text="🏠 С первоначальным взносом", callback_data="calc_downpayment")],
        [InlineKeyboardButton(text="💰 Сколько могу взять", callback_data="calc_affordable")],
        [InlineKeyboardButton(text="⚖️ Сравнить варианты", callback_data="compare_scenarios")],
        [InlineKeyboardButton(text="📈 Досрочное погашение", callback_data="early_repayment")],
        [InlineKeyboardButton(text="📋 История расчетов", callback_data="mortgage_history")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main_menu")]
    ])

def get_mortgage_back_keyboard():
    """
    Клавиатура возврата в ипотечном калькуляторе
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

def get_payment_type_keyboard():
    """
    Выбор типа платежа (аннуитетный/дифференцированный)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Аннуитетный (равные платежи)", callback_data="payment_type_annuity")],
        [InlineKeyboardButton(text="📉 Дифференцированный (уменьшающиеся)", callback_data="payment_type_diff")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

def get_yes_no_keyboard(with_back=True):
    """
    Универсальная клавиатура Да/Нет
    
    Args:
        with_back: добавлять ли кнопку "Назад"
    """
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no")
        ]
    ]
    
    if with_back:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_compare_options_keyboard():
    """
    Клавиатура для сравнения вариантов ипотеки
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вариант", callback_data="add_scenario")],
        [InlineKeyboardButton(text="📊 Сравнить сейчас", callback_data="compare_now")],
        [InlineKeyboardButton(text="📋 Показать варианты", callback_data="show_scenarios")],
        [InlineKeyboardButton(text="🗑️ Очистить список", callback_data="clear_scenarios")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

def get_early_repayment_keyboard():
    """
    Клавиатура для выбора типа досрочного погашения
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Единовременное погашение", callback_data="early_lump_sum")],
        [InlineKeyboardButton(text="📅 Уменьшение срока", callback_data="early_reduce_term")],
        [InlineKeyboardButton(text="💵 Уменьшение платежа", callback_data="early_reduce_payment")],
        [InlineKeyboardButton(text="🔄 Частичное досрочное", callback_data="early_partial")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

def get_mortgage_history_keyboard():
    """
    Клавиатура для управления историей расчетов
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Последние 5 расчетов", callback_data="history_last5")],
        [InlineKeyboardButton(text="📊 Все расчеты", callback_data="history_all")],
        [InlineKeyboardButton(text="🗑️ Очистить историю", callback_data="history_clear")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])
    
# ========== ГЛАВНАЯ КЛАВИАТУРА БОТА ==========

def get_main_bot_keyboard():
    """
    Главная клавиатура всего бота (показывается после капчи)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        # Основные функции бота
        [InlineKeyboardButton(text="🏘️ Поиск недвижимости", callback_data="search_real_estate")],
        [InlineKeyboardButton(text="🏦 Ипотечный калькулятор", callback_data="mortgage_calculator")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about_us")],
        [InlineKeyboardButton(text="📍 Сменить город", callback_data="change_city_main")],
        
        # Ссылки
        [InlineKeyboardButton(text="📢 Наш Telegram канал", url=TELEGRAM_CHANNEL_URL)],
        [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contact_us")]
    ])

def get_about_keyboard():
    """
    Клавиатура для раздела 'О нас'
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Позвонить нам", callback_data="call_us")],
        [InlineKeyboardButton(text="📍 Наш офис на карте", callback_data="our_office_map")],
        [InlineKeyboardButton(text="📧 Написать email", callback_data="write_email")],
        [InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/AgentstvoKluchi")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main_menu")]
    ])

def get_contact_keyboard():
    """
    Клавиатура для связи с нами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Позвонить", callback_data="call_us")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main_menu")]
    ])

def get_numeric_keyboard():
    """
    Цифровая клавиатура для ввода чисел
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="num_1"),
            InlineKeyboardButton(text="2", callback_data="num_2"),
            InlineKeyboardButton(text="3", callback_data="num_3")
        ],
        [
            InlineKeyboardButton(text="4", callback_data="num_4"),
            InlineKeyboardButton(text="5", callback_data="num_5"),
            InlineKeyboardButton(text="6", callback_data="num_6")
        ],
        [
            InlineKeyboardButton(text="7", callback_data="num_7"),
            InlineKeyboardButton(text="8", callback_data="num_8"),
            InlineKeyboardButton(text="9", callback_data="num_9")
        ],
        [
            InlineKeyboardButton(text="0", callback_data="num_0"),
            InlineKeyboardButton(text="⬅️ Стереть", callback_data="num_clear"),
            InlineKeyboardButton(text="✅ Готово", callback_data="num_done")
        ],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="num_cancel")]
    ])

def get_confirmation_keyboard():
    """
    Клавиатура подтверждения действия
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_no")
        ],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="confirm_edit")]
    ])

def get_help_keyboard():
    """
    Клавиатура помощи/справки
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Как искать недвижимость", callback_data="help_search")],
        [InlineKeyboardButton(text="💰 Как считать ипотеку", callback_data="help_mortgage")],
        [InlineKeyboardButton(text="🏠 Советы по покупке", callback_data="help_tips")],
        [InlineKeyboardButton(text="📋 Частые вопросы", callback_data="help_faq")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main_menu")]
    ])

# ========== СПЕЦИАЛЬНЫЕ КЛАВИАТУРЫ ==========

def get_rate_keyboard():
    """
    Клавиатура для выбора процентной ставки
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📉 Базовая (15-18%)", callback_data="rate_base")],
        [InlineKeyboardButton(text="🏠 Семейная (6%)", callback_data="rate_family")],
        [InlineKeyboardButton(text="💻 IT-ипотека (5%)", callback_data="rate_it")],
        [InlineKeyboardButton(text="🌏 Дальневосточная (2%)", callback_data="rate_far_east")],
        [InlineKeyboardButton(text="🎖️ Военная ипотека (9%)", callback_data="rate_military")],
        [InlineKeyboardButton(text="🏢 Господдержка новостройки (8%)", callback_data="rate_state_support")],
        [InlineKeyboardButton(text="✏️ Ввести свою", callback_data="rate_custom")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

def get_years_keyboard():
    """
    Клавиатура для выбора срока кредита
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 лет", callback_data="years_5")],
        [InlineKeyboardButton(text="10 лет", callback_data="years_10")],
        [InlineKeyboardButton(text="15 лет", callback_data="years_15")],
        [InlineKeyboardButton(text="20 лет", callback_data="years_20")],
        [InlineKeyboardButton(text="25 лет", callback_data="years_25")],
        [InlineKeyboardButton(text="30 лет", callback_data="years_30")],
        [InlineKeyboardButton(text="✏️ Ввести свой срок", callback_data="years_custom")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

def get_downpayment_keyboard():
    """
    Клавиатура для выбора первоначального взноса
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10%", callback_data="down_10")],
        [InlineKeyboardButton(text="15%", callback_data="down_15")],
        [InlineKeyboardButton(text="20%", callback_data="down_20")],
        [InlineKeyboardButton(text="25%", callback_data="down_25")],
        [InlineKeyboardButton(text="30%", callback_data="down_30")],
        [InlineKeyboardButton(text="50%", callback_data="down_50")],
        [InlineKeyboardButton(text="✏️ Ввести свою сумму", callback_data="down_custom")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
    ])

# Экспорт всех клавиатур
__all__ = [
    # Данные
    'categories', 'quarters', 'houses', 'newbuildings', 
    'land_plots', 'commercial', 'cities',
    
    # Клавиатуры недвижимости
    'keyboard_of_cities', 'make_main_keyboard', 'make_subcategory_keyboard',
    'make_property_keyboard', 'make_city_selector_keyboard', 'back_kb',
    
    # Клавиатуры капчи
    'make_captcha_kb',
    
    # Клавиатуры ипотеки
    'get_mortgage_main_keyboard', 'get_mortgage_back_keyboard',
    'get_payment_type_keyboard', 'get_yes_no_keyboard',
    'get_compare_options_keyboard', 'get_early_repayment_keyboard',
    'get_mortgage_history_keyboard', 'get_rate_keyboard',
    'get_years_keyboard', 'get_downpayment_keyboard',
    
    # Основные клавиатуры
    'get_main_bot_keyboard', 'get_about_keyboard',
    'get_contact_keyboard', 'get_numeric_keyboard',
    'get_confirmation_keyboard', 'get_help_keyboard'
]