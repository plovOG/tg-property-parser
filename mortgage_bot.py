from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from typing import Dict, Any, Optional
import re

from mortgage_calculator import MortgageCalculator
from keyboards import (
    get_mortgage_main_keyboard, get_mortgage_back_keyboard,
    get_payment_type_keyboard, get_compare_options_keyboard, 
    get_early_repayment_keyboard, get_mortgage_history_keyboard,
    get_rate_keyboard, get_years_keyboard, get_downpayment_keyboard,
)
from textformat import format_mortgage_result, format_currency, format_error_message
from config import save_mortgage_calculation, get_mortgage_history

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для ипотечного калькулятора
mortgage_router = Router()

# Состояния FSM для ипотечного калькулятора
class MortgageStates(StatesGroup):
    # Основные состояния
    waiting_for_amount = State()
    waiting_for_rate = State()
    waiting_for_years = State()
    waiting_for_payment_type = State()
    
    # Для расчета с первоначальным взносом
    waiting_for_total_cost = State()
    waiting_for_downpayment_percent = State()
    
    # Для расчета по доходу
    waiting_for_income = State()
    waiting_for_other_loans = State()
    
    # Для сравнения вариантов
    waiting_for_scenario_name = State()
    waiting_for_scenario_amount = State()
    waiting_for_scenario_rate = State()
    waiting_for_scenario_years = State()
    
    # Для досрочного погашения
    waiting_for_early_month = State()
    waiting_for_early_amount = State()
    waiting_for_early_type = State()
    
    # Для истории расчетов
    viewing_history = State()

# Вспомогательные функции
def parse_amount(text: str) -> Optional[float]:
    """Парсит сумму из текста"""
    try:
        # Удаляем пробелы, запятые, символы валюты
        cleaned = re.sub(r'[^\d.]', '', text.replace(',', '.'))
        if not cleaned:
            return None
        return float(cleaned)
    except:
        return None

def format_mortgage_parameters(params: Dict[str, Any]) -> str:
    """Форматирует параметры ипотеки для отображения"""
    result = "📋 *Параметры расчета:*\n\n"
    
    if 'loan_amount' in params:
        result += f"• Сумма кредита: {format_currency(params['loan_amount'])}\n"
    
    if 'total_cost' in params:
        result += f"• Стоимость недвижимости: {format_currency(params['total_cost'])}\n"
    
    if 'downpayment_percent' in params:
        result += f"• Первоначальный взнос: {params['downpayment_percent']}%\n"
    
    if 'annual_rate' in params:
        result += f"• Процентная ставка: {params['annual_rate']}% годовых\n"
    
    if 'years' in params:
        result += f"• Срок кредита: {params['years']} лет\n"
    
    if 'monthly_income' in params:
        result += f"• Ежемесячный доход: {format_currency(params['monthly_income'])}\n"
    
    if 'other_loans' in params:
        result += f"• Другие кредиты: {format_currency(params['other_loans'])}/мес\n"
    
    return result

async def save_calculation_to_history(user_id: int, calc_type: str, 
                                     params: Dict[str, Any], result: Dict[str, Any]):
    """Сохраняет расчет в историю"""
    try:
        await save_mortgage_calculation(user_id, calc_type, params, result)
        logger.info(f"Расчет сохранен в историю для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении расчета в историю: {e}")

# Основные обработчики
@mortgage_router.callback_query(F.data == "mortgage_calculator")
async def cmd_mortgage(call: CallbackQuery):
    """
    Главное меню ипотечного калькулятора
    """
    await call.message.edit_text(
        "🏦 *Ипотечный калькулятор*\n\n"
        "Выберите тип расчета:\n\n"
        "📊 *Основные расчеты:*\n"
        "• Рассчитать ежемесячный платеж\n"
        "• Расчет с первоначальным взносом\n"
        "• Сколько можно взять по доходу\n\n"
        "⚖️ *Дополнительные функции:*\n"
        "• Сравнить несколько вариантов\n"
        "• Досрочное погашение\n"
        "• История ваших расчетов",
        reply_markup=get_mortgage_main_keyboard(),
        parse_mode="Markdown"
    )
    await call.answer()

@mortgage_router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_from_mortgage(call: CallbackQuery, state: FSMContext):
    """
    Возврат в главное меню бота
    """
    user_id = call.from_user.id
    
    try:
        # Очищаем состояние ипотечного калькулятора
        await state.clear()
        
        # Получаем основной роутер для возврата в главное меню
        from choose_category import get_main_bot_keyboard
        
        # Пытаемся получить сохраненный город
        from config import get_user_city
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

@mortgage_router.callback_query(F.data == "back_to_mortgage_menu")
async def back_to_mortgage_menu(call: CallbackQuery):
    """
    Возврат в меню ипотечного калькулятора
    """
    await call.message.edit_text(
        "🏦 *Ипотечный калькулятор*\n\nВыберите тип расчета:",
        reply_markup=get_mortgage_main_keyboard(),
        parse_mode="Markdown"
    )
    await call.answer()

# Расчет обычного платежа
@mortgage_router.callback_query(F.data == "calc_payment")
async def start_calculation(call: CallbackQuery, state: FSMContext):
    """
    Начало расчета обычного платежа
    """
    await call.message.answer(
        "📊 *Расчет ежемесячного платежа*\n\n"
        "Введите сумму кредита (в рублях):\n\n"
        "*Пример:* 5 000 000",
        parse_mode="Markdown",
        reply_markup=get_mortgage_back_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_amount)
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    """
    Обработка ввода суммы кредита
    """
    amount = parse_amount(message.text)
    
    if amount is None or amount <= 0:
        await message.answer(
            "❌ *Неверная сумма!*\n\n"
            "Пожалуйста, введите корректную сумму кредита в рублях.\n"
            "*Пример:* 5 000 000 или 5000000",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    if amount > 1000000000:  # 1 млрд
        await message.answer(
            "⚠️ *Слишком большая сумма!*\n\n"
            "Максимальная сумма для расчета: 1 000 000 000 ₽\n"
            "Введите меньшую сумму:",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    # Сохраняем сумму и просим выбрать тип платежа
    await state.update_data(loan_amount=amount)
    
    await message.answer(
        f"✅ Сумма кредита: *{format_currency(amount)}*\n\n"
        "📅 *Выберите тип платежа:*\n\n"
        "• *Аннуитетный* — одинаковые платежи каждый месяц\n"
        "• *Дифференцированный* — платежи уменьшаются со временем\n\n"
        "Большинство банков используют аннуитетные платежи.",
        parse_mode="Markdown",
        reply_markup=get_payment_type_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_payment_type)

@mortgage_router.callback_query(F.data == "payment_type_annuity")
async def process_payment_type_annuity(call: CallbackQuery, state: FSMContext):
    """
    Выбран аннуитетный тип платежа
    """
    await state.update_data(payment_type='annuity')
    
    await call.message.answer(
        "📊 *Аннуитетные платежи выбраны*\n\n"
        "Введите годовую процентную ставку (%):\n\n"
        "*Примеры:*\n"
        "• 7.5 — обычная ставка\n"
        "• 6.0 — семейная ипотека\n"
        "• 5.0 — IT-ипотека\n"
        "• 15.0 — базовая ставка",
        parse_mode="Markdown",
        reply_markup=get_rate_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_rate)
    await call.answer("✅ Аннуитетные платежи")

@mortgage_router.callback_query(F.data == "payment_type_diff")
async def process_payment_type_diff(call: CallbackQuery, state: FSMContext):
    """
    Выбран дифференцированный тип платежа
    """
    await state.update_data(payment_type='differentiated')
    
    await call.message.answer(
        "📉 *Дифференцированные платежи выбраны*\n\n"
        "Введите годовую процентную ставку (%):",
        parse_mode="Markdown",
        reply_markup=get_rate_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_rate)
    await call.answer("✅ Дифференцированные платежи")

@mortgage_router.message(MortgageStates.waiting_for_rate)
async def process_rate(message: Message, state: FSMContext):
    """
    Обработка ввода процентной ставки
    """
    try:
        rate = float(message.text.replace(',', '.'))
        
        if rate <= 0 or rate > 50:
            await message.answer(
                "❌ *Неверная ставка!*\n\n"
                "Пожалуйста, введите корректную процентную ставку (от 0.1 до 50%).\n"
                "*Пример:* 7.5",
                parse_mode="Markdown",
                reply_markup=get_rate_keyboard()
            )
            return
        
        await state.update_data(annual_rate=rate)
        
        await message.answer(
            f"✅ Процентная ставка: *{rate}%* годовых\n\n"
            "📅 *Выберите срок кредита (в годах):*",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )
        await state.set_state(MortgageStates.waiting_for_years)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите число с точкой или запятой.\n"
            "*Пример:* 7.5 или 7,5",
            parse_mode="Markdown",
            reply_markup=get_rate_keyboard()
        )

# Обработчики быстрого выбора ставки
@mortgage_router.callback_query(F.data.startswith("rate_"))
async def process_quick_rate(call: CallbackQuery, state: FSMContext):
    """
    Быстрый выбор процентной ставки
    """
    rate_map = {
        'rate_base': 15.0,
        'rate_family': 6.0,
        'rate_it': 5.0,
        'rate_far_east': 2.0,
        'rate_military': 9.0,
        'rate_state_support': 8.0

    }
    
    rate_value = rate_map.get(call.data)
    
    if rate_value:
        await state.update_data(annual_rate=rate_value)
        
        rate_names = {
            15.0: "Базовая ставка",
            6.0: "Семейная ипотека",
            5.0: "IT-ипотека",
            2.0: "Дальневосточная ипотека",
            9.0: "Военная ипотека",
            8.0: "Ипотека для новостроек"
        }
        
        await call.message.answer(
            f"✅ *{rate_names[rate_value]}*: *{rate_value}%* годовых\n\n"
            "📅 *Выберите срок кредита (в годах):*",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )
        await state.set_state(MortgageStates.waiting_for_years)
    else:
        # Пользователь хочет ввести свою ставку
        await call.message.answer(
            "✏️ *Введите свою процентную ставку (%):*\n\n"
            "*Пример:* 7.5",
            parse_mode="Markdown"
        )
        await state.set_state(MortgageStates.waiting_for_rate)
    
    await call.answer()

# Обработчики быстрого выбора срока
@mortgage_router.callback_query(F.data.startswith("years_"))
async def process_quick_years(call: CallbackQuery, state: FSMContext):
    """
    Быстрый выбора срока кредита
    """
    if call.data == "years_custom":
        await call.message.answer(
            "✏️ *Введите свой срок кредита (в годах):*\n\n"
            "*Пример:* 15",
            parse_mode="Markdown"
        )
        await state.set_state(MortgageStates.waiting_for_years)
    else:
        years = int(call.data.replace("years_", ""))
        await state.update_data(years=years)
        await perform_calculation(call, state)
    
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_years)
async def process_years(message: Message, state: FSMContext):
    """
    Обработка ввода срока кредита
    """
    try:
        years = int(message.text)
        
        if years <= 0 or years > 50:
            await message.answer(
                "❌ *Неверный срок!*\n\n"
                "Пожалуйста, введите срок кредита от 1 до 50 лет.\n"
                "*Пример:* 20",
                parse_mode="Markdown",
                reply_markup=get_years_keyboard()
            )
            return
        
        await state.update_data(years=years)
        await perform_calculation_from_message(message, state)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите целое число лет.\n"
            "*Пример:* 15",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )

async def perform_calculation_from_message(message: Message, state: FSMContext):
    """
    Выполнение расчета из обработчика сообщений
    """
    data = await state.get_data()
    
    # Создаем fake callback для использования общей функции
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await perform_calculation(fake_callback, state)

async def perform_calculation(call: CallbackQuery, state: FSMContext):
    """
    Выполнение расчета ипотеки
    """
    user_id = call.from_user.id
    data = await state.get_data()
    
    try:
        # Извлекаем параметры
        loan_amount = data.get('loan_amount')
        annual_rate = data.get('annual_rate')
        years = data.get('years')
        payment_type = data.get('payment_type', 'annuity')
        
        if not all([loan_amount, annual_rate, years]):
            await call.message.answer(
                "❌ *Недостаточно данных для расчета!*\n\n"
                "Пожалуйста, начните расчет заново.",
                parse_mode="Markdown",
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Выполняем расчет
        if payment_type == 'annuity':
            result = MortgageCalculator.calculate_annuity(loan_amount, annual_rate, years)
        else:
            result = MortgageCalculator.calculate_differentiated(loan_amount, annual_rate, years)
        
        if not result.get('success', False):
            await call.message.answer(
                format_error_message(result.get('error', 'Неизвестная ошибка')),
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Форматируем результат
        result_text = format_mortgage_result(result)
        
        # Добавляем параметры расчета
        params_text = format_mortgage_parameters(data)
        
        # Сохраняем в историю
        await save_calculation_to_history(
            user_id=user_id,
            calc_type='basic_mortgage',
            params=data,
            result=result
        )
        
        # Отправляем результат
        await call.message.answer(
            f"{params_text}\n{result_text}",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        
        # Предлагаем дополнительные действия
        await call.message.answer(
            "🔄 *Что дальше?*\n\n"
            "• Рассчитать с первоначальным взносом\n"
            "• Сравнить с другим вариантом\n"
            "• Рассчитать досрочное погашение\n"
            "• Вернуться в меню",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏠 С первонач. взносом", callback_data="calc_downpayment"),
                    InlineKeyboardButton(text="⚖️ Сравнить", callback_data="compare_scenarios")
                ],
                [
                    InlineKeyboardButton(text="📈 Досрочное погашение", callback_data="early_repayment"),
                    InlineKeyboardButton(text="📋 История", callback_data="mortgage_history")
                ],
                [
                    InlineKeyboardButton(text="🔄 Новый расчет", callback_data="calc_payment"),
                    InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_mortgage_menu")
                ]
            ])
        )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при расчете ипотеки: {e}", exc_info=True)
        await call.message.answer(
            format_error_message("Произошла ошибка при расчете. Попробуйте другие параметры."),
            reply_markup=get_mortgage_back_keyboard()
        )

# Расчет с первоначальным взносом
@mortgage_router.callback_query(F.data == "calc_downpayment")
async def start_downpayment_calculation(call: CallbackQuery, state: FSMContext):
    """
    Начало расчета с первоначальным взносом
    """
    await call.message.answer(
        "🏠 *Расчет с первоначальным взносом*\n\n"
        "Введите общую стоимость недвижимости (в рублях):\n\n"
        "*Пример:* 8 000 000",
        parse_mode="Markdown",
        reply_markup=get_mortgage_back_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_total_cost)
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_total_cost)
async def process_total_cost(message: Message, state: FSMContext):
    """
    Обработка ввода стоимости недвижимости
    """
    total_cost = parse_amount(message.text)
    
    if total_cost is None or total_cost <= 0:
        await message.answer(
            "❌ *Неверная стоимость!*\n\n"
            "Пожалуйста, введите корректную стоимость недвижимости в рублях.\n"
            "*Пример:* 8 000 000",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    await state.update_data(total_cost=total_cost)
    
    await message.answer(
        f"✅ Стоимость недвижимости: *{format_currency(total_cost)}*\n\n"
        "💵 *Выберите процент первоначального взноса:*\n\n"
        "Обычно банки требуют от 15% до 20%.\n"
        "Чем больше взнос, тем меньше переплата.",
        parse_mode="Markdown",
        reply_markup=get_downpayment_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_downpayment_percent)

@mortgage_router.callback_query(F.data.startswith("down_"))
async def process_downpayment_percent(call: CallbackQuery, state: FSMContext):
    """
    Обработка выбора процента первоначального взноса
    """
    if call.data == "down_custom":
        await call.message.answer(
            "✏️ *Введите свой процент первоначального взноса:*\n\n"
            "*Пример:* 25",
            parse_mode="Markdown"
        )
        await state.set_state(MortgageStates.waiting_for_downpayment_percent)
    else:
        percent = float(call.data.replace("down_", ""))
        await perform_downpayment_calculation(call, state, percent)
    
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_downpayment_percent)
async def process_custom_downpayment(message: Message, state: FSMContext):
    """
    Обработка ввода своего процента первоначального взноса
    """
    try:
        percent = float(message.text.replace(',', '.'))
        
        if percent < 0 or percent >= 100:
            await message.answer(
                "❌ *Неверный процент!*\n\n"
                "Пожалуйста, введите процент от 0 до 99.\n"
                "*Пример:* 20",
                parse_mode="Markdown",
                reply_markup=get_downpayment_keyboard()
            )
            return
        
        await perform_downpayment_calculation_from_message(message, state, percent)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите число с точкой или запятой.\n"
            "*Пример:* 20 или 20.5",
            parse_mode="Markdown",
            reply_markup=get_downpayment_keyboard()
        )

async def perform_downpayment_calculation_from_message(message: Message, state: FSMContext, percent: float):
    """
    Выполнение расчета с первоначальным взносом из сообщения
    """
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await perform_downpayment_calculation(fake_callback, state, percent)

async def perform_downpayment_calculation(call: CallbackQuery, state: FSMContext, downpayment_percent: float):
    """
    Выполнение расчета с первоначальным взносом
    """
    user_id = call.from_user.id
    data = await state.get_data()
    
    try:
        total_cost = data.get('total_cost')
        
        if not total_cost:
            await call.message.answer(
                "❌ *Не указана стоимость недвижимости!*",
                parse_mode="Markdown",
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Запрашиваем процентную ставку
        await state.update_data(downpayment_percent=downpayment_percent)
        
        await call.message.answer(
            f"✅ Первоначальный взнос: *{downpayment_percent}%*\n\n"
            f"📊 *Сумма взноса:* {format_currency(total_cost * downpayment_percent / 100)}\n"
            f"💰 *Сумма кредита:* {format_currency(total_cost * (1 - downpayment_percent / 100))}\n\n"
            "Введите годовую процентную ставку (%):",
            parse_mode="Markdown",
            reply_markup=get_rate_keyboard()
        )
        await state.set_state(MortgageStates.waiting_for_rate)
        
    except Exception as e:
        logger.error(f"Ошибка при расчете с первоначальным взносом: {e}")
        await call.message.answer(
            format_error_message("Произошла ошибка при расчете."),
            reply_markup=get_mortgage_back_keyboard()
        )

# Расчет максимальной суммы по доходу
@mortgage_router.callback_query(F.data == "calc_affordable")
async def start_affordable_calculation(call: CallbackQuery, state: FSMContext):
    """
    Начало расчета максимальной суммы по доходу
    """
    await call.message.answer(
        "💰 *Сколько можно взять по доходу*\n\n"
        "Введите ваш ежемесячный доход после налогов (в рублях):\n\n"
        "*Пример:* 150 000",
        parse_mode="Markdown",
        reply_markup=get_mortgage_back_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_income)
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_income)
async def process_income(message: Message, state: FSMContext):
    """
    Обработка ввода дохода
    """
    income = parse_amount(message.text)
    
    if income is None or income <= 0:
        await message.answer(
            "❌ *Неверный доход!*\n\n"
            "Пожалуйста, введите корректную сумму дохода в рублях.\n"
            "*Пример:* 150 000",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    await state.update_data(monthly_income=income)
    
    await message.answer(
        f"✅ Ежемесячный доход: *{format_currency(income)}*\n\n"
        "💳 *Есть ли у вас другие ежемесячные кредитные платежи?*\n\n"
        "Если да, введите общую сумму в рублях.\n"
        "Если нет, введите 0.\n\n"
        "*Пример:* 25 000",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Нет других кредитов", callback_data="other_loans_0")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_mortgage_menu")]
        ])
    )
    await state.set_state(MortgageStates.waiting_for_other_loans)

@mortgage_router.callback_query(F.data == "other_loans_0")
async def process_no_other_loans(call: CallbackQuery, state: FSMContext):
    """
    Обработка отсутствия других кредитов
    """
    await state.update_data(other_loans=0)
    await continue_affordable_calculation(call, state)
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_other_loans)
async def process_other_loans(message: Message, state: FSMContext):
    """
    Обработка ввода других кредитов
    """
    other_loans = parse_amount(message.text)
    
    if other_loans is None or other_loans < 0:
        await message.answer(
            "❌ *Неверная сумма!*\n\n"
            "Пожалуйста, введите корректную сумму или 0.\n"
            "*Пример:* 0 или 25 000",
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(other_loans=other_loans)
    await continue_affordable_calculation_from_message(message, state)

async def continue_affordable_calculation_from_message(message: Message, state: FSMContext):
    """
    Продолжение расчета из сообщения
    """
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await continue_affordable_calculation(fake_callback, state)

async def continue_affordable_calculation(call: CallbackQuery, state: FSMContext):
    """
    Продолжение расчета максимальной суммы
    """
    data = await state.get_data()
    
    await call.message.answer(
        "📊 *Теперь выберите процентную ставку и срок:*\n\n"
        "Банки обычно одобряют кредит, если платеж не превышает 40% от дохода.",
        parse_mode="Markdown",
        reply_markup=get_rate_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_rate)

# После ввода ставки и срока для расчета по доходу
@mortgage_router.message(MortgageStates.waiting_for_years)
async def process_years_for_affordable(message: Message, state: FSMContext):
    """
    Обработка срока для расчета по доходу
    """
    try:
        years = int(message.text)
        
        if years <= 0 or years > 50:
            await message.answer(
                "❌ *Неверный срок!*\n\n"
                "Пожалуйста, введите срок от 1 до 50 лет.\n"
                "*Пример:* 20",
                parse_mode="Markdown",
                reply_markup=get_years_keyboard()
            )
            return
        
        await state.update_data(years=years)
        await perform_affordable_calculation_from_message(message, state)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите целое число лет.\n"
            "*Пример:* 15",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )

async def perform_affordable_calculation_from_message(message: Message, state: FSMContext):
    """
    Выполнение расчета по доходу из сообщения
    """
    user_id = message.from_user.id
    data = await state.get_data()
    
    try:
        monthly_income = data.get('monthly_income')
        other_loans = data.get('other_loans', 0)
        annual_rate = data.get('annual_rate')
        years = data.get('years')
        
        if not all([monthly_income, annual_rate, years]):
            await message.answer(
                "❌ *Недостаточно данных для расчета!*",
                parse_mode="Markdown",
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Выполняем расчет
        result = MortgageCalculator.max_affordable_loan(
            monthly_income=monthly_income,
            annual_rate=annual_rate,
            years=years,
            other_loans=other_loans
        )
        
        if not result.get('success', False):
            await message.answer(
                format_error_message(result.get('error', 'Неизвестная ошибка')),
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Форматируем результат
        result_text = (
            f"💰 *Расчет по вашему доходу:*\n\n"
            f"• Ежемесячный доход: *{format_currency(monthly_income)}*\n"
            f"• Другие кредиты: *{format_currency(other_loans)}/мес*\n"
            f"• Ставка: *{annual_rate}%* годовых\n"
            f"• Срок: *{years}* лет\n\n"
            
            f"📊 *Результаты:*\n"
            f"• Доступный платеж: *{format_currency(result['available_payment'])}/мес*\n"
            f"• Максимальный кредит: *{format_currency(result['max_loan'])}*\n"
            f"• Доля платежа от дохода: *{result['payment_to_income_ratio']}%*\n\n"
            
            f"🏠 *Пример при 20% взносе:*\n"
            f"• Стоимость жилья: *{format_currency(result['example_property_cost'])}*\n"
            f"• Первоначальный взнос: *{format_currency(result['example_downpayment'])}*\n"
            f"• Сумма кредита: *{format_currency(result['max_loan'])}*\n\n"
            
            f"💡 *Рекомендации:*\n"
            "• Банки обычно одобряют кредит, если платеж не превышает 40% от дохода\n"
            "• Учитывайте дополнительные расходы: ремонт, мебель, коммунальные платежи\n"
            "• Рекомендуемый срок: 15-25 лет"
        )
        
        # Сохраняем в историю
        await save_calculation_to_history(
            user_id=user_id,
            calc_type='affordable_loan',
            params=data,
            result=result
        )
        
        # Отправляем результат
        await message.answer(
            result_text,
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при расчете по доходу: {e}", exc_info=True)
        await message.answer(
            format_error_message("Произошла ошибка при расчете."),
            reply_markup=get_mortgage_back_keyboard()
        )

# Сравнение вариантов
@mortgage_router.callback_query(F.data == "compare_scenarios")
async def start_comparison(call: CallbackQuery, state: FSMContext):
    """
    Начало сравнения вариантов
    """
    # Инициализируем список сценариев
    await state.update_data(scenarios=[])
    
    await call.message.answer(
        "⚖️ *Сравнение вариантов ипотеки*\n\n"
        "Вы можете добавить несколько вариантов и сравнить их:\n\n"
        "• Разные суммы кредита\n"
        "• Разные процентные ставки\n"
        "• Разные сроки\n"
        "• С первоначальным взносом и без\n\n"
        "Добавьте первый вариант:",
        parse_mode="Markdown",
        reply_markup=get_compare_options_keyboard()
    )
    await call.answer()

@mortgage_router.callback_query(F.data == "add_scenario")
async def add_scenario(call: CallbackQuery, state: FSMContext):
    """
    Добавление нового сценария для сравнения
    """
    await call.message.answer(
        "➕ *Добавление варианта*\n\n"
        "Введите название для этого варианта:\n\n"
        "*Примеры:*\n"
        "• Базовая ипотека\n"
        "• Семейная ипотека\n"
        "• С 20% взносом\n"
        "• На 15 лет",
        parse_mode="Markdown",
        reply_markup=get_mortgage_back_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_scenario_name)
    await call.answer()

@mortgage_router.message(MortgageStates.waiting_for_scenario_name)
async def process_scenario_name(message: Message, state: FSMContext):
    """
    Обработка названия сценария
    """
    scenario_name = message.text.strip()
    
    if not scenario_name or len(scenario_name) > 50:
        await message.answer(
            "❌ *Неверное название!*\n\n"
            "Пожалуйста, введите название до 50 символов.",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    await state.update_data(current_scenario_name=scenario_name)
    
    await message.answer(
        f"✅ Название: *{scenario_name}*\n\n"
        "Введите сумму кредита (в рублях):\n\n"
        "*Пример:* 5 000 000",
        parse_mode="Markdown",
        reply_markup=get_mortgage_back_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_scenario_amount)

# Продолжение обработчиков сравнения вариантов

@mortgage_router.message(MortgageStates.waiting_for_scenario_amount)
async def process_scenario_amount(message: Message, state: FSMContext):
    """
    Обработка суммы кредита для сценария
    """
    amount = parse_amount(message.text)
    
    if amount is None or amount <= 0:
        await message.answer(
            "❌ *Неверная сумма!*\n\n"
            "Пожалуйста, введите корректную сумму кредита.\n"
            "*Пример:* 5 000 000",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    await state.update_data(current_scenario_amount=amount)
    
    await message.answer(
        f"✅ Сумма кредита: *{format_currency(amount)}*\n\n"
        "Введите годовую процентную ставку (%):\n\n"
        "*Пример:* 7.5",
        parse_mode="Markdown",
        reply_markup=get_rate_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_scenario_rate)

@mortgage_router.message(MortgageStates.waiting_for_scenario_rate)
async def process_scenario_rate(message: Message, state: FSMContext):
    """
    Обработка процентной ставки для сценария
    """
    try:
        rate = float(message.text.replace(',', '.'))
        
        if rate <= 0 or rate > 50:
            await message.answer(
                "❌ *Неверная ставка!*\n\n"
                "Пожалуйста, введите ставку от 0.1 до 50%.\n"
                "*Пример:* 7.5",
                parse_mode="Markdown",
                reply_markup=get_rate_keyboard()
            )
            return
        
        await state.update_data(current_scenario_rate=rate)
        
        await message.answer(
            f"✅ Процентная ставка: *{rate}%* годовых\n\n"
            "Введите срок кредита (в годах):\n\n"
            "*Пример:* 20",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )
        await state.set_state(MortgageStates.waiting_for_scenario_years)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите число с точкой или запятой.\n"
            "*Пример:* 7.5",
            parse_mode="Markdown",
            reply_markup=get_rate_keyboard()
        )

@mortgage_router.message(MortgageStates.waiting_for_scenario_years)
async def process_scenario_years(message: Message, state: FSMContext):
    """
    Обработка срока кредита для сценария
    """
    try:
        years = int(message.text)
        
        if years <= 0 or years > 50:
            await message.answer(
                "❌ *Неверный срок!*\n\n"
                "Пожалуйста, введите срок от 1 до 50 лет.\n"
                "*Пример:* 20",
                parse_mode="Markdown",
                reply_markup=get_years_keyboard()
            )
            return
        
        # Получаем все данные сценария
        data = await state.get_data()
        scenario_name = data.get('current_scenario_name')
        amount = data.get('current_scenario_amount')
        rate = data.get('current_scenario_rate')
        
        # Создаем сценарий
        scenario = {
            'name': scenario_name,
            'loan_amount': amount,
            'annual_rate': rate,
            'years': years,
            'type': 'annuity'  # Пока только аннуитетные
        }
        
        # Добавляем в список сценариев
        scenarios = data.get('scenarios', [])
        scenarios.append(scenario)
        await state.update_data(scenarios=scenarios)
        
        # Очищаем временные данные
        await state.update_data({
            'current_scenario_name': None,
            'current_scenario_amount': None,
            'current_scenario_rate': None
        })
        
        # Показываем текущий список сценариев
        scenarios_text = "📋 *Текущие варианты для сравнения:*\n\n"
        for i, s in enumerate(scenarios, 1):
            scenarios_text += (
                f"{i}. *{s['name']}*\n"
                f"   Сумма: {format_currency(s['loan_amount'])}\n"
                f"   Ставка: {s['annual_rate']}%\n"
                f"   Срок: {s['years']} лет\n\n"
            )
        
        await message.answer(
            f"✅ *Вариант добавлен!*\n\n"
            f"{scenarios_text}"
            f"Вы можете добавить ещё варианты или сравнить текущие.",
            parse_mode="Markdown",
            reply_markup=get_compare_options_keyboard()
        )
        
        # Возвращаемся в состояние ожидания выбора действия
        await state.set_state(None)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите целое число лет.\n"
            "*Пример:* 15",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )

@mortgage_router.callback_query(F.data == "compare_now")
async def compare_scenarios_now(call: CallbackQuery, state: FSMContext):
    """
    Выполнение сравнения вариантов
    """
    data = await state.get_data()
    scenarios = data.get('scenarios', [])
    
    if not scenarios:
        await call.message.answer(
            "❌ *Нет вариантов для сравнения!*\n\n"
            "Добавьте хотя бы один вариант для сравнения.",
            parse_mode="Markdown",
            reply_markup=get_compare_options_keyboard()
        )
        await call.answer()
        return
    
    if len(scenarios) < 2:
        await call.message.answer(
            "❌ *Недостаточно вариантов!*\n\n"
            "Для сравнения нужно как минимум 2 варианта.\n"
            "Добавьте ещё один вариант.",
            parse_mode="Markdown",
            reply_markup=get_compare_options_keyboard()
        )
        await call.answer()
        return
    
    try:
        # Выполняем сравнение
        result = MortgageCalculator.compare_scenarios(scenarios)
        
        if not result.get('success', False):
            await call.message.answer(
                format_error_message(result.get('error', 'Ошибка сравнения')),
                reply_markup=get_mortgage_back_keyboard()
            )
            await call.answer()
            return
        
        # Форматируем результаты сравнения
        comparison_text = "⚖️ *Сравнение вариантов ипотеки:*\n\n"
        
        # Для каждого сценария
        for scenario_result in result['scenarios']:
            comparison_text += (
                f"📊 *{scenario_result['scenario_name']}*\n"
                f"• Платеж: {format_currency(scenario_result['monthly_payment'])}/мес\n"
                f"• Всего выплат: {format_currency(scenario_result['total_paid'])}\n"
                f"• Переплата: {format_currency(scenario_result['overpayment'])} "
                f"({scenario_result['overpayment_percent']}%)\n\n"
            )
        
        # Лучшие варианты
        best_by_payment = result['best_by_payment']
        best_by_total = result['best_by_total']
        best_by_overpayment = result['best_by_overpayment']
        
        comparison_text += (
            "🏆 *Лучшие варианты:*\n\n"
            f"• *Самый низкий платеж:* {best_by_payment['scenario_name']}\n"
            f"  {format_currency(best_by_payment['monthly_payment'])}/мес\n\n"
            
            f"• *Минимальная переплата:* {best_by_overpayment['scenario_name']}\n"
            f"  {format_currency(best_by_overpayment['overpayment'])} "
            f"({best_by_overpayment['overpayment_percent']}%)\n\n"
            
            f"• *Минимальная общая сумма:* {best_by_total['scenario_name']}\n"
            f"  {format_currency(best_by_total['total_paid'])}\n\n"
            
            "💡 *Рекомендации:*\n"
            "• Выбирайте вариант с минимальным платежом, если бюджет ограничен\n"
            "• Выбирайте вариант с минимальной переплатой, если хотите сэкономить\n"
            "• Учитывайте также возможность досрочного погашения"
        )
        
        # Сохраняем в историю
        user_id = call.from_user.id
        await save_calculation_to_history(
            user_id=user_id,
            calc_type='comparison',
            params={'scenarios': scenarios},
            result=result
        )
        
        # Отправляем результаты
        await call.message.answer(
            comparison_text,
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        
        # Очищаем список сценариев
        await state.update_data(scenarios=[])
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при сравнении вариантов: {e}", exc_info=True)
        await call.message.answer(
            format_error_message("Произошла ошибка при сравнении вариантов."),
            reply_markup=get_mortgage_back_keyboard()
        )
        await call.answer()

@mortgage_router.callback_query(F.data == "show_scenarios")
async def show_scenarios(call: CallbackQuery, state: FSMContext):
    """
    Показ текущих сценариев
    """
    data = await state.get_data()
    scenarios = data.get('scenarios', [])
    
    if not scenarios:
        await call.message.answer(
            "📋 *Список вариантов пуст*\n\n"
            "Добавьте варианты для сравнения.",
            parse_mode="Markdown",
            reply_markup=get_compare_options_keyboard()
        )
    else:
        scenarios_text = "📋 *Текущие варианты для сравнения:*\n\n"
        for i, s in enumerate(scenarios, 1):
            scenarios_text += (
                f"{i}. *{s['name']}*\n"
                f"   Сумма: {format_currency(s['loan_amount'])}\n"
                f"   Ставка: {s['annual_rate']}%\n"
                f"   Срок: {s['years']} лет\n\n"
            )
        
        await call.message.answer(
            scenarios_text,
            parse_mode="Markdown",
            reply_markup=get_compare_options_keyboard()
        )
    
    await call.answer()

@mortgage_router.callback_query(F.data == "clear_scenarios")
async def clear_scenarios(call: CallbackQuery, state: FSMContext):
    """
    Очистка списка сценариев
    """
    await state.update_data(scenarios=[])
    
    await call.message.answer(
        "🗑️ *Список вариантов очищен!*\n\n"
        "Вы можете начать добавление вариантов заново.",
        parse_mode="Markdown",
        reply_markup=get_compare_options_keyboard()
    )
    await call.answer()

# Досрочное погашение
@mortgage_router.callback_query(F.data == "early_repayment")
async def start_early_repayment(call: CallbackQuery, state: FSMContext):
    """
    Начало расчета досрочного погашения
    """
    await call.message.answer(
        "📈 *Расчет досрочного погашения*\n\n"
        "Введите сумму кредита (в рублях):\n\n"
        "*Пример:* 5 000 000",
        parse_mode="Markdown",
        reply_markup=get_mortgage_back_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_amount)
    await call.answer()

# После ввода суммы, ставки и срока для досрочного погашения
@mortgage_router.message(MortgageStates.waiting_for_years)
async def process_years_for_early_repayment(message: Message, state: FSMContext):
    """
    Обработка срока для досрочного погашения
    """
    try:
        years = int(message.text)
        
        if years <= 0 or years > 50:
            await message.answer(
                "❌ *Неверный срок!*\n\n"
                "Пожалуйста, введите срок от 1 до 50 лет.\n"
                "*Пример:* 20",
                parse_mode="Markdown",
                reply_markup=get_years_keyboard()
            )
            return
        
        await state.update_data(years=years)
        
        # Теперь запрашиваем месяц досрочного погашения
        data = await state.get_data()
        loan_amount = data.get('loan_amount')
        annual_rate = data.get('annual_rate')
        
        # Сначала показываем обычный расчет
        regular_result = MortgageCalculator.calculate_annuity(loan_amount, annual_rate, years)
        
        if regular_result.get('success', False):
            regular_text = (
                f"📊 *Исходный кредит:*\n\n"
                f"• Сумма: {format_currency(loan_amount)}\n"
                f"• Ставка: {annual_rate}% годовых\n"
                f"• Срок: {years} лет\n"
                f"• Платеж: {format_currency(regular_result['monthly_payment'])}/мес\n"
                f"• Всего выплат: {format_currency(regular_result['total_paid'])}\n"
                f"• Переплата: {format_currency(regular_result['overpayment'])}\n\n"
            )
            
            await message.answer(
                f"{regular_text}"
                "📅 *Введите месяц, в который планируете внести досрочный платеж:*\n\n"
                "*Пример:* 12 (через год)",
                parse_mode="Markdown",
                reply_markup=get_mortgage_back_keyboard()
            )
            await state.set_state(MortgageStates.waiting_for_early_month)
        else:
            await message.answer(
                format_error_message(regular_result.get('error', 'Ошибка расчета')),
                reply_markup=get_mortgage_back_keyboard()
            )
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите целое число лет.\n"
            "*Пример:* 15",
            parse_mode="Markdown",
            reply_markup=get_years_keyboard()
        )

@mortgage_router.message(MortgageStates.waiting_for_early_month)
async def process_early_month(message: Message, state: FSMContext):
    """
    Обработка месяца досрочного погашения
    """
    try:
        early_month = int(message.text)
        data = await state.get_data()
        years = data.get('years')
        total_months = years * 12
        
        if early_month <= 0 or early_month > total_months:
            await message.answer(
                f"❌ *Неверный месяц!*\n\n"
                f"Кредит на {years} лет ({total_months} месяцев).\n"
                f"Введите месяц от 1 до {total_months}.\n\n"
                f"*Пример:* 12 (через год)",
                parse_mode="Markdown",
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        await state.update_data(early_month=early_month)
        
        await message.answer(
            f"✅ Месяц досрочного погашения: *{early_month}*\n\n"
            "💰 *Введите сумму досрочного погашения (в рублях):*\n\n"
            "*Пример:* 500 000",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        await state.set_state(MortgageStates.waiting_for_early_amount)
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат!*\n\n"
            "Пожалуйста, введите целое число месяцев.\n"
            "*Пример:* 12",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )

@mortgage_router.message(MortgageStates.waiting_for_early_amount)
async def process_early_amount(message: Message, state: FSMContext):
    """
    Обработка суммы досрочного погашения
    """
    early_amount = parse_amount(message.text)
    
    if early_amount is None or early_amount <= 0:
        await message.answer(
            "❌ *Неверная сумма!*\n\n"
            "Пожалуйста, введите корректную сумму досрочного погашения.\n"
            "*Пример:* 500 000",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    data = await state.get_data()
    loan_amount = data.get('loan_amount')
    
    if early_amount > loan_amount:
        await message.answer(
            f"⚠️ *Сумма досрочного погашения превышает кредит!*\n\n"
            f"Кредит: {format_currency(loan_amount)}\n"
            f"Досрочка: {format_currency(early_amount)}\n\n"
            f"Введите сумму до {format_currency(loan_amount)}:",
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        return
    
    await state.update_data(early_amount=early_amount)
    
    # Спрашиваем тип досрочного погашения
    await message.answer(
        f"💰 *Сумма досрочного погашения: {format_currency(early_amount)}*\n\n"
        "📊 *Выберите тип досрочного погашения:*\n\n"
        "• *Уменьшение платежа* — срок останется прежним, платеж уменьшится\n"
        "• *Уменьшение срока* — платеж останется прежним, срок уменьшится\n\n"
        "Что вы предпочитаете?",
        parse_mode="Markdown",
        reply_markup=get_early_repayment_keyboard()
    )
    await state.set_state(MortgageStates.waiting_for_early_type)

@mortgage_router.callback_query(F.data.startswith("early_"))
async def process_early_type(call: CallbackQuery, state: FSMContext):
    """
    Обработка выбора типа досрочного погашения
    """
    early_type_map = {
        'early_reduce_payment': 'reduce_payment',
        'early_reduce_term': 'reduce_term',
        'early_lump_sum': 'reduce_payment',  # Единовременное = уменьшение платежа
        'early_partial': 'reduce_payment'    # Частичное = уменьшение платежа
    }
    
    repayment_type = early_type_map.get(call.data)
    
    if not repayment_type:
        await call.answer("❌ Неизвестный тип досрочного погашения")
        return
    
    await perform_early_repayment_calculation(call, state, repayment_type)
    await call.answer()

async def perform_early_repayment_calculation(call: CallbackQuery, state: FSMContext, repayment_type: str):
    """
    Выполнение расчета досрочного погашения
    """
    user_id = call.from_user.id
    data = await state.get_data()
    
    try:
        # Извлекаем параметры
        loan_amount = data.get('loan_amount')
        annual_rate = data.get('annual_rate')
        years = data.get('years')
        early_month = data.get('early_month')
        early_amount = data.get('early_amount')
        
        if not all([loan_amount, annual_rate, years, early_month, early_amount]):
            await call.message.answer(
                "❌ *Недостаточно данных для расчета!*",
                parse_mode="Markdown",
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Выполняем расчет
        result = MortgageCalculator.early_repayment_calculation(
            loan_amount=loan_amount,
            annual_rate=annual_rate,
            years=years,
            early_month=early_month,
            early_amount=early_amount,
            repayment_type=repayment_type
        )
        
        if not result.get('success', False):
            await call.message.answer(
                format_error_message(result.get('error', 'Ошибка расчета')),
                reply_markup=get_mortgage_back_keyboard()
            )
            return
        
        # Форматируем результат
        if repayment_type == 'reduce_payment':
            type_text = "уменьшение платежа"
            savings_text = f"• Экономия: *{format_currency(result['total_savings'])}*\n"
        else:
            type_text = "уменьшение срока"
            savings_text = (
                f"• Сэкономлено месяцев: *{result['months_saved']}*\n"
                f"• Экономия: *{format_currency(result['total_savings'])}*\n"
            )
        
        result_text = (
            f"📈 *Результаты досрочного погашения*\n"
            f"Тип: *{type_text}*\n\n"
            
            f"📋 *Исходные параметры:*\n"
            f"• Кредит: {format_currency(loan_amount)}\n"
            f"• Ставка: {annual_rate}% годовых\n"
            f"• Срок: {years} лет ({years * 12} месяцев)\n"
            f"• Исходный платеж: {format_currency(result['original_payment'])}/мес\n\n"
            
            f"💰 *Досрочное погашение:*\n"
            f"• Месяц: {early_month}\n"
            f"• Сумма: {format_currency(early_amount)}\n\n"
            
            f"📊 *Результаты:*\n"
            f"• Новый платеж: *{format_currency(result['new_payment'])}/мес*\n"
            f"• Остаток долга: *{format_currency(result['remaining_debt'])}*\n"
            f"{savings_text}"
            f"• Всего выплат с досрочкой: *{format_currency(result['total_paid_with_early'])}*\n\n"
            
            f"💡 *Эффект досрочного погашения:*\n"
            f"Досрочное погашение в {early_month} месяце на сумму "
            f"{format_currency(early_amount)} позволяет "
        )
        
        if repayment_type == 'reduce_payment':
            payment_reduction = result['original_payment'] - result['new_payment']
            result_text += (
                f"уменьшить ежемесячный платеж на "
                f"{format_currency(payment_reduction)}."
            )
        else:
            result_text += (
                f"сократить срок кредита на {result['months_saved']} месяцев."
            )
        
        # Сохраняем в историю
        await save_calculation_to_history(
            user_id=user_id,
            calc_type=f'early_repayment_{repayment_type}',
            params=data,
            result=result
        )
        
        # Отправляем результат
        await call.message.answer(
            result_text,
            parse_mode="Markdown",
            reply_markup=get_mortgage_back_keyboard()
        )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при расчете досрочного погашения: {e}", exc_info=True)
        await call.message.answer(
            format_error_message("Произошла ошибка при расчете досрочного погашения."),
            reply_markup=get_mortgage_back_keyboard()
        )

# История расчетов
@mortgage_router.callback_query(F.data == "mortgage_history")
async def show_mortgage_history(call: CallbackQuery, state: FSMContext):
    """
    Показ истории расчетов
    """
    user_id = call.from_user.id
    
    try:
        # Получаем историю
        history = await get_mortgage_history(user_id, limit=5)
        
        if not history:
            await call.message.answer(
                "📋 *История расчетов пуста*\n\n"
                "Вы ещё не делали расчетов ипотеки.\n"
                "Начните с любого типа расчета.",
                parse_mode="Markdown",
                reply_markup=get_mortgage_history_keyboard()
            )
            await call.answer()
            return
        
        # Форматируем историю
        history_text = "📋 *Последние 5 расчетов:*\n\n"
        
        for i, calc in enumerate(history, 1):
            calc_type_map = {
                'basic_mortgage': '📊 Базовая ипотека',
                'with_downpayment': '🏠 С первоначальным взносом',
                'affordable_loan': '💰 Расчет по доходу',
                'comparison': '⚖️ Сравнение вариантов',
                'early_repayment_reduce_payment': '📈 Досрочное (уменьшение платежа)',
                'early_repayment_reduce_term': '📈 Досрочное (уменьшение срока)'
            }
            
            calc_type = calc_type_map.get(calc['type'], calc['type'])
            date = calc['date'][:16].replace('T', ' ')  # Форматируем дату
            
            history_text += (
                f"{i}. *{calc_type}*\n"
                f"   📅 {date}\n"
            )
            
            # Добавляем основные параметры
            params = calc['parameters']
            if 'loan_amount' in params:
                history_text += f"   💰 {format_currency(params['loan_amount'])}\n"
            if 'annual_rate' in params:
                history_text += f"   📈 {params['annual_rate']}%\n"
            if 'years' in params:
                history_text += f"   📅 {params['years']} лет\n"
            
            history_text += "\n"
        
        await call.message.answer(
            history_text,
            parse_mode="Markdown",
            reply_markup=get_mortgage_history_keyboard()
        )
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        await call.message.answer(
            format_error_message("Не удалось загрузить историю расчетов."),
            reply_markup=get_mortgage_back_keyboard()
        )
        await call.answer()

@mortgage_router.callback_query(F.data == "history_last5")
async def show_history_last5(call: CallbackQuery):
    """
    Показ последних 5 расчетов
    """
    await show_mortgage_history(call, None)
    await call.answer()

@mortgage_router.callback_query(F.data == "history_all")
async def show_history_all(call: CallbackQuery):
    """
    Показ всей истории
    """
    user_id = call.from_user.id
    
    try:
        history = await get_mortgage_history(user_id, limit=20)
        
        if not history:
            await call.message.answer(
                "📋 *История расчетов пуста*",
                parse_mode="Markdown",
                reply_markup=get_mortgage_history_keyboard()
            )
            await call.answer()
            return
        
        history_text = "📋 *Вся история расчетов:*\n\n"
        
        for i, calc in enumerate(history, 1):
            calc_type_map = {
                'basic_mortgage': '📊',
                'with_downpayment': '🏠',
                'affordable_loan': '💰',
                'comparison': '⚖️',
                'early_repayment': '📈'
            }
            
            calc_icon = calc_type_map.get(calc['type'], '📝')
            date = calc['date'][:10]
            
            history_text += f"{i}. {calc_icon} {date}: "
            
            params = calc['parameters']
            if 'loan_amount' in params:
                history_text += f"{format_currency(params['loan_amount'])} "
            if 'annual_rate' in params:
                history_text += f"({params['annual_rate']}%) "
            if 'years' in params:
                history_text += f"- {params['years']} лет"
            
            history_text += "\n"
        
        await call.message.answer(
            history_text,
            parse_mode="Markdown",
            reply_markup=get_mortgage_history_keyboard()
        )
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при получении всей истории: {e}")
        await call.answer("❌ Ошибка загрузки истории")

@mortgage_router.callback_query(F.data == "history_clear")
async def clear_history(call: CallbackQuery):
    """
    Очистка истории
    """
    # В реальном боте здесь должен быть код очистки истории из базы данных
    # Пока просто показываем сообщение
    
    await call.message.answer(
        "🗑️ *Очистка истории*\n\n"
        "Функция очистки истории находится в разработке.\n"
        "Сейчас история хранится 30 дней, затем автоматически очищается.",
        parse_mode="Markdown",
        reply_markup=get_mortgage_history_keyboard()
    )
    await call.answer()

# Обработчики помощи
@mortgage_router.callback_query(F.data == "help_mortgage")
async def help_mortgage(call: CallbackQuery):
    """
    Помощь по ипотечному калькулятору
    """
    help_text = (
        "🆘 *Помощь по ипотечному калькулятору*\n\n"
        
        "📊 *Основные функции:*\n"
        "1. *Расчет платежа* — узнайте ежемесячный платеж\n"
        "2. *С первоначальным взносом* — расчет с учётом ваших средств\n"
        "3. *По доходу* — сколько можете взять\n"
        "4. *Сравнение* — сравните несколько вариантов\n"
        "5. *Досрочное погашение* — расчёт экономии\n\n"
        
        "📈 *Как пользоваться:*\n"
        "• Вводите суммы без пробелов или с пробелами\n"
        "• Используйте точку или запятую для десятичных дробей\n"
        "• Для ставок можно использовать быстрый выбор\n"
        "• Все расчеты сохраняются в историю\n\n"
        
        "💡 *Советы:*\n"
        "• Ипотека на 15-20 лет оптимальна по переплате\n"
        "• Ставка 6-8% считается хорошей\n"
        "• Платеж не должен превышать 40% от дохода\n"
        "• Досрочное погашение сильно сокращает переплату\n\n"
        
        "❓ *Частые вопросы:*\n"
        "• Расчеты приблизительные, точные цифры даст банк\n"
        "• Не учитываются страховки и дополнительные комиссии\n"
        "• Для сложных расчетов обращайтесь к консультанту"
    )
    
    await call.message.answer(help_text, parse_mode="Markdown")
    await call.answer()

# Обработка числовых кнопок
@mortgage_router.callback_query(F.data.startswith("num_"))
async def process_numeric_button(call: CallbackQuery, state: FSMContext):
    """
    Обработка нажатий на числовые кнопки
    """
    button_data = call.data
    
    if button_data == "num_clear":
        # Очистка ввода
        await call.answer("Очищено")
    elif button_data == "num_done":
        # Готово
        await call.answer("Готово")
    elif button_data == "num_cancel":
        # Отмена
        await call.answer("Отмена")
        await back_to_mortgage_menu(call)
    else:
        # Цифра
        digit = button_data.replace("num_", "")
        await call.answer(f"Цифра {digit}")

# Экспорт роутера
__all__ = ['mortgage_router', 'MortgageStates']