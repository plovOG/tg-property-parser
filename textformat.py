from typing import Dict, Any

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы для MarkdownV2
    
    Args:
        text: Исходный текст
        
    Returns:
        Экранированный текст
    """
    if not text:
        return ""
    
    # Специальные символы MarkdownV2, которые нужно экранировать
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Экранируем каждый специальный символ
    escaped_text = ''
    for char in text:
        if char in escape_chars:
            escaped_text += '\\' + char
        else:
            escaped_text += char
    
    return escaped_text

def format_currency(amount: float) -> str:
    """
    Форматирует денежную сумму в красивый вид
    
    Args:
        amount: Сумма денег
        
    Returns:
        Отформатированная строка
    """
    if amount is None:
        return "не указано"
    
    # Округляем до 2 знаков после запятой
    amount = round(amount, 2)
    
    # Форматируем с разделителями тысяч
    formatted = f"{amount:,.2f}"
    
    # Заменяем точку на запятую для рублевого формата
    formatted = formatted.replace(",", " ").replace(".", ",")
    
    return f"{formatted} ₽"

def format_property_message(property_data: Dict[str, Any], category_name: str = "") -> str:
    """
    Форматирует сообщение для карточки недвижимости
    
    Args:
        property_data: Данные о недвижимости
        category_name: Название категории
        
    Returns:
        Отформатированное сообщение в MarkdownV2
    """
    # Извлекаем данные
    title = property_data.get('title', 'Без названия')
    price = property_data.get('price', 'Цена не указана')
    city = property_data.get('city', 'Не указан')
    location = property_data.get('location', '')
    
    # Экранируем специальные символы
    escaped_title = escape_markdown(title)
    escaped_price = escape_markdown(price)
    escaped_city = escape_markdown(city)
    escaped_location = escape_markdown(location)
    
    # Формируем заголовок с городом
    message = f"📍 *{escaped_city}*"
    
    # Добавляем локацию, если она отличается от города
    if escaped_location and escaped_location.lower() != escaped_city.lower():
        message += f" \\(*{escaped_location}*\\)"
    
    # Добавляем категорию, если указана
    if category_name:
        message += f"\n🏷️ *Категория:* {escape_markdown(category_name)}"
    
    # Добавляем название объекта
    message += f"\n\n🏠 *{escaped_title}*"
    
    # Добавляем цену
    message += f"\n\n💰 *{escaped_price}*"
    
    # Добавляем ссылку, если есть
    link = property_data.get('link')
    if link:
        # В MarkdownV2 ссылки требуют двойного экранирования скобок
        escaped_link = link.replace('(', '\\(').replace(')', '\\)')
        message += f"\n\n🔗 [Подробнее на сайте]({escaped_link})"
    
    return message

def format_property_message_html(property_data: Dict[str, Any], category_name: str = "") -> str:
    """
    Форматирует сообщение для карточки недвижимости с HTML
    
    Args:
        property_data: Данные о недвижимости
        category_name: Название категории
        
    Returns:
        Отформатированное сообщение в HTML
    """
    title = property_data.get('title', 'Без названия')
    price = property_data.get('price', 'Цена не указана')
    city = property_data.get('city', 'Не указан')
    location = property_data.get('location', '')
    
    # Формируем сообщение
    message = f"<b>📍 {city}</b>"
    
    if location and location.lower() != city.lower():
        message += f" (<i>{location}</i>)"
    
    if category_name:
        message += f"\n🏷️ <b>Категория:</b> {category_name}"
    
    message += f"\n\n🏠 <b>{title}</b>"
    message += f"\n\n💰 <b>{price}</b>"
    
    link = property_data.get('link')
    if link:
        message += f"\n\n🔗 <a href='{link}'>Подробнее на сайте</a>"
    
    return message

def format_mortgage_result(result: Dict[str, Any]) -> str:
    """
    Форматирует результат расчета ипотеки
    
    Args:
        result: Результат расчета
        
    Returns:
        Отформатированное сообщение
    """
    message = "📊 *Результаты расчета ипотеки:*\n\n"
    
    # Основные параметры
    if 'loan_amount' in result:
        message += f"• Сумма кредита: *{format_currency(result['loan_amount'])}*\n"
    
    if 'total_cost' in result:
        message += f"• Стоимость недвижимости: *{format_currency(result['total_cost'])}*\n"
    
    if 'downpayment_amount' in result:
        message += f"• Первоначальный взнос: *{format_currency(result['downpayment_amount'])}*"
        if 'downpayment_percent' in result:
            message += f" ({result['downpayment_percent']}%)\n"
        else:
            message += "\n"
    
    if 'annual_rate' in result:
        message += f"• Процентная ставка: *{result['annual_rate']}%* годовых\n"
    
    if 'years' in result:
        message += f"• Срок кредита: *{result['years']}* лет\n"
    
    # Результаты расчета
    if 'monthly_payment' in result:
        message += f"\n📅 *Ежемесячный платеж:*\n*{format_currency(result['monthly_payment'])}*\n"
    
    if 'total_paid' in result:
        message += f"\n💰 *Общая сумма выплат:*\n*{format_currency(result['total_paid'])}*\n"
    
    if 'overpayment' in result:
        message += f"\n💸 *Переплата по кредиту:*\n*{format_currency(result['overpayment'])}*"
        if 'overpayment_percent' in result:
            message += f" ({result['overpayment_percent']}%)\n"
    
    # График платежей (первые 6 месяцев)
    if 'schedule_first_6' in result and result['schedule_first_6']:
        message += "\n\n📈 *Первые 6 месяцев платежей:*\n"
        
        for month_data in result['schedule_first_6']:
            month = month_data['month']
            payment = format_currency(month_data['payment'])
            principal = format_currency(month_data['principal'])
            interest = format_currency(month_data['interest'])
            remaining = format_currency(month_data['remaining'])
            
            message += f"Месяц {month}: {payment} (осн.долг: {principal}, проценты: {interest})\n"
    
    # Дополнительная информация
    if 'effective_rate' in result:
        message += f"\n📊 *Эффективная ставка:* {result['effective_rate']}%\n"
    
    if 'available_payment' in result:
        message += f"\n💼 *Доступный платеж:* {format_currency(result['available_payment'])}/мес\n"
    
    if 'max_loan' in result:
        message += f"\n🏦 *Максимальная сумма кредита:* {format_currency(result['max_loan'])}\n"
    
    return message

def format_short_property_info(property_data: Dict[str, Any]) -> str:
    """
    Короткий формат для карточки недвижимости
    
    Args:
        property_data: Данные о недвижимости
        
    Returns:
        Краткое описание
    """
    title = property_data.get('title', '')[:50]
    price = property_data.get('price', '')
    city = property_data.get('city', '')
    
    return f"{city} | {title} | {price}"

def format_city_selection(city_name: str) -> str:
    """
    Форматирует сообщение о выборе города
    
    Args:
        city_name: Название города
        
    Returns:
        Отформатированное сообщение
    """
    return f"📍 *Выбран город: {city_name}*\n\nТеперь вы можете искать недвижимость в этом городе."

def format_error_message(error: str) -> str:
    """
    Форматирует сообщение об ошибке
    
    Args:
        error: Текст ошибки
        
    Returns:
        Отформатированное сообщение об ошибке
    """
    return f"❌ *Ошибка:* {error}\n\nПожалуйста, попробуйте еще раз или обратитесь в поддержку."

def format_success_message(message: str) -> str:
    """
    Форматирует сообщение об успехе
    
    Args:
        message: Текст сообщения
        
    Returns:
        Отформатированное сообщение
    """
    return f"✅ {message}"

def format_number_with_spaces(number: float) -> str:
    """
    Форматирует число с пробелами для разделения тысяч
    
    Args:
        number: Число для форматирования
        
    Returns:
        Отформатированная строка
    """
    return f"{number:,.0f}".replace(",", " ")

# Экспорт функций
__all__ = [
    'escape_markdown',
    'format_currency',
    'format_property_message',
    'format_property_message_html',
    'format_mortgage_result',
    'format_short_property_info',
    'format_city_selection',
    'format_error_message',
    'format_success_message',
    'format_number_with_spaces'
]