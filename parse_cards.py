from bs4 import BeautifulSoup
from urllib.parse import urljoin
import aiohttp
import logging
import re
import asyncio
from typing import List, Dict, Optional, Any
import json

# Базовый URL сайта с недвижимостью
URL = "https://www.xn----htbkhfjn2e0c.xn--p1ai/"

def setup_logging():
    """Настройка логирования для парсера"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def fix_url(url: str) -> str:
    """
    Исправляет URL, делая его абсолютным
    
    Args:
        url: Относительный или абсолютный URL
        
    Returns:
        Абсолютный URL
    """
    if not url:
        return URL
    
    if url.startswith('/'):
        return urljoin(URL, url)
    
    if url.startswith('http'):
        return url
    
    return urljoin(URL, url)

async def debug_card_structure(category_url: str) -> int:
    """
    Анализирует структуру карточек на сайте
    
    Args:
        category_url: URL категории для анализа
        
    Returns:
        Количество найденных карточек
    """
    try:
        url = fix_url(category_url)
        logger.info(f"Анализ структуры карточек: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    property_cards = soup.find_all('div', class_='catalog-page-cart__item')
                    
                    print(f"\n{'='*60}")
                    print(f"НАЙДЕНО КАРТОЧЕК: {len(property_cards)}")
                    print(f"{'='*60}")
                    
                    if property_cards:
                        first_card = property_cards[0]
                        
                        print("\n📊 АНАЛИЗ СТРУКТУРЫ ПЕРВОЙ КАРТОЧКИ:")
                        print("-" * 50)
                        
                        # 1. Выводим ВСЕ классы в карточке
                        print("\n📌 Все элементы с классами:")
                        elements_with_classes = []
                        for elem in first_card.find_all(class_=True):
                            class_name = ' '.join(elem.get('class', []))
                            text = elem.get_text(strip=True)
                            if text and len(text) < 100:
                                elements_with_classes.append((class_name, text))
                        
                        # Сортируем по длине текста
                        elements_with_classes.sort(key=lambda x: len(x[1]))
                        for class_name, text in elements_with_classes[:10]:  # Первые 10
                            print(f"  🏷️ Класс: {class_name:40} | 📝 Текст: {text}")
                        
                        # 2. Ищем элементы с локацией
                        print("\n📍 Поиск элементов с локацией:")
                        location_keywords = ['район', 'улица', 'ул.', 'пос.', 'г.', 'сочи', 
                                           'геленджик', 'новороссийск', 'адрес', 'location']
                        
                        location_elements = []
                        for elem in first_card.find_all():
                            text = elem.get_text(strip=True).lower()
                            if any(keyword in text for keyword in location_keywords):
                                class_name = ' '.join(elem.get('class', []))
                                location_elements.append((class_name, elem.get_text(strip=True)))
                        
                        if location_elements:
                            for class_name, text in location_elements:
                                print(f"  🗺️ Найден: '{text}' | Класс: {class_name}")
                        else:
                            print("  ❌ Элементы с локацией не найдены")
                        
                        # 3. Сохраняем HTML для ручного анализа
                        with open('debug_card.html', 'w', encoding='utf-8') as f:
                            f.write(str(first_card.prettify()))
                        print(f"\n💾 HTML сохранен в debug_card.html")
                        
                        # 4. Выводим структуру карточки
                        print("\n🏗️ Структура карточки:")
                        print(f"  Тег: {first_card.name}")
                        print(f"  ID: {first_card.get('id', 'нет')}")
                        print(f"  Классы: {first_card.get('class', [])}")
                        
                    return len(property_cards)
                else:
                    logger.error(f"Ошибка HTTP {response.status} при анализе структуры")
                    return 0
                    
    except asyncio.TimeoutError:
        logger.error("Таймаут при анализе структуры")
        return 0
    except Exception as e:
        logger.error(f"Ошибка при анализе структуры: {e}")
        return 0

def check_city_in_text(text: str) -> Optional[str]:
    """
    Проверяет наличие города в тексте
    
    Args:
        text: Текст для анализа
        
    Returns:
        Название города или None
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Паттерны для каждого города
    city_patterns = {
        "Сочи": [
            r'\bсочи\b',
            r'\bsochi\b',
            r'адлер',
            r'хостин',
            r'лазарев',
            r'кудепст',
            r'дагомыс'
        ],
        "Геленджик": [
            r'\bгеленджик\b',
            r'\bgelendzhik\b',
            r'кабардин',
            r'дивия',
            r'архипо'
        ],
        "Новороссийск": [
            r'\bновороссийск\b',
            r'\bnovorossiysk\b',
            r'\bцы\b',
            r'мысхак',
            r'южная оз'
        ]
    }
    
    for city, patterns in city_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.I):
                return city
    
    return None

def detect_city_in_property(property_card: BeautifulSoup) -> Optional[str]:
    """
    Определяет город из структуры карточки
    
    Args:
        property_card: BeautifulSoup объект карточки
        
    Returns:
        Название города или None
    """
    try:
        # 1. Сначала ищем в специальных элементах локации
        location_selectors = [
            'loc', 'location', 'address', 'адрес', 'район', 
            'street', 'улица', 'город', 'city'
        ]
        
        for selector in location_selectors:
            # Ищем по классу
            location_elem = property_card.find(class_=re.compile(selector, re.I))
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                city = check_city_in_text(location_text)
                if city:
                    logger.debug(f"Город найден в локации: {city}")
                    return city
        
        # 2. Ищем в описании
        description_selectors = ['descr', 'description', 'описание', 'text', 'info']
        for selector in description_selectors:
            description_elem = property_card.find(class_=re.compile(selector, re.I))
            if description_elem:
                description_text = description_elem.get_text(strip=True)
                city = check_city_in_text(description_text)
                if city:
                    logger.debug(f"Город найден в описании: {city}")
                    return city
        
        # 3. Ищем в заголовке
        title_selectors = ['title', 'name', 'название', 'header']
        for selector in title_selectors:
            title_elem = property_card.find(class_=re.compile(selector, re.I))
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                city = check_city_in_text(title_text)
                if city:
                    logger.debug(f"Город найден в заголовке: {city}")
                    return city
        
        # 4. Если не нашли в специальных элементах, ищем во всем тексте карточки
        all_text = property_card.get_text().lower()
        city = check_city_in_text(all_text)
        if city:
            logger.debug(f"Город найден во всем тексте: {city}")
            return city
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при определении города: {e}")
        return None

def find_city_flexible(card: BeautifulSoup) -> Optional[str]:
    """
    Гибкий поиск города во всех текстовых элементах
    
    Args:
        card: BeautifulSoup объект карточки
        
    Returns:
        Название города или None
    """
    city_synonyms = {
        'сочи': ['сочи', 'sochi', 'адлер', 'хости', 'лазарев', 'кудепста'],
        'геленджик': ['геленджик', 'gelendzhik', 'кабардин', 'дивия', 'архипо'],
        'новороссийск': ['новороссийск', 'novorossiysk', 'цы', 'мысхак', 'южная озерка']
    }
    
    try:
        # Ищем во всех текстовых элементах
        for elem in card.find_all(text=True):
            text = elem.strip().lower()
            if text and len(text) > 2:  # Игнорируем очень короткие тексты
                for city, synonyms in city_synonyms.items():
                    for syn in synonyms:
                        if syn in text:
                            logger.debug(f"Город '{city}' найден по синониму '{syn}'")
                            return city.capitalize()
    
    except Exception as e:
        logger.error(f"Ошибка при гибком поиске города: {e}")
    
    return None

def extract_price_from_card(card: BeautifulSoup) -> str:
    """
    Извлекает цену из карточки
    
    Args:
        card: BeautifulSoup объект карточки
        
    Returns:
        Цена в виде строки
    """
    price_selectors = [
        'catalog-page-cart__prices',
        'catalog-page-cart__prices-alt',
        'price', 'стоимость', 'руб', '₽', 'р.',
        re.compile(r'price|стоимость|руб', re.I)
    ]
    
    for selector in price_selectors:
        try:
            price_elem = card.find(class_=selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if price_text and any(c.isdigit() for c in price_text):
                    # Очищаем цену от лишних символов
                    cleaned_price = re.sub(r'\s+', ' ', price_text).strip()
                    logger.debug(f"Цена найдена: {cleaned_price}")
                    return cleaned_price
        except:
            continue
    
    # Если не нашли, пробуем найти любой текст с цифрами и символами валюты
    for elem in card.find_all():
        text = elem.get_text(strip=True)
        if any(c.isdigit() for c in text) and any(c in text for c in ['₽', 'руб', 'р.', '$', '€']):
            logger.debug(f"Цена найдена альтернативным способом: {text}")
            return text
    
    return "Цена не указана"

def extract_property_data(card: BeautifulSoup, url: str) -> Dict[str, Any]:
    """
    Извлекает данные о недвижимости из карточки
    
    Args:
        card: BeautifulSoup объект карточки
        url: URL страницы
        
    Returns:
        Словарь с данными о недвижимости
    """
    property_data = {}
    
    try:
        # Название
        title_elem = card.find('a', class_='catalog-page-cart__title')
        if not title_elem:
            title_elem = card.find(class_=re.compile(r'title|name|название', re.I))
        
        property_data['title'] = title_elem.get_text(strip=True) if title_elem else "Название не указано"
        
        # Определяем город
        detected_city = detect_city_in_property(card)
        if not detected_city:
            detected_city = find_city_flexible(card)
        
        property_data['city'] = detected_city or "Не определен"
        
        # Цена
        property_data['price'] = extract_price_from_card(card)
        
        # Фото
        img_elem = card.find('img')
        if img_elem:
            img_src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-original')
            property_data['image'] = fix_url(img_src) if img_src else None
        else:
            property_data['image'] = None
        
        # Ссылка
        if title_elem and title_elem.get('href'):
            property_data['link'] = fix_url(title_elem['href'])
        else:
            any_link = card.find('a', href=True)
            property_data['link'] = fix_url(any_link['href']) if any_link else url
        
        # Локация (детальная)
        location_text = ""
        loc_elem = card.find(class_=re.compile(r'loc|location|address|район|улиц', re.I))
        if loc_elem:
            location_text = loc_elem.get_text(strip=True)
        
        property_data['location'] = location_text or property_data['city']
        
        # Сохраняем ВЕСЬ текст карточки для отладки
        property_data['full_text'] = card.get_text(strip=True)
        
        # ID карточки (если есть)
        property_data['card_id'] = card.get('id', '')
        
        # Классы карточки
        property_data['card_classes'] = card.get('class', [])
        
        logger.debug(f"Извлечены данные: {property_data['title'][:30]}... | Город: {property_data['city']}")
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных из карточки: {e}")
        property_data['error'] = str(e)
    
    return property_data

async def fetch_all_properties(category_url: str, selected_city: Optional[str] = None, 
                             max_cards: int = 20) -> List[Dict[str, Any]]:
    """
    Парсит карточки недвижимости с сайта
    
    Args:
        category_url: URL категории
        selected_city: Город для фильтрации (если None - все города)
        max_cards: Максимальное количество карточек для парсинга
        
    Returns:
        Список словарей с данными о недвижимости
    """
    try:
        url = fix_url(category_url)
        logger.info(f"Начинаю парсинг: {url} | Город: {selected_city or 'все'} | Лимит: {max_cards}")
        
        async with aiohttp.ClientSession() as session:
            # Устанавливаем заголовки, чтобы выглядеть как браузер
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем карточки недвижимости
                    property_cards = soup.find_all('div', class_='catalog-page-cart__item')
                    logger.info(f"На странице найдено {len(property_cards)} карточек")
                    
                    if not property_cards:
                        # Пробуем альтернативные селекторы
                        property_cards = soup.find_all(class_=re.compile(r'cart|item|card|product', re.I))
                        logger.info(f"Альтернативным поиском найдено {len(property_cards)} карточек")
                    
                    all_properties = []
                    cards_processed = 0
                    
                    for card in property_cards:
                        if cards_processed >= max_cards:
                            break
                        
                        property_data = extract_property_data(card, url)
                        
                        # Фильтрация по городу
                        if selected_city:
                            city = property_data.get('city', '')
                            if city != selected_city:
                                continue
                        
                        # Добавляем только если есть название
                        if property_data.get('title') != "Название не указано":
                            all_properties.append(property_data)
                            cards_processed += 1
                    
                    logger.info(f"После фильтрации осталось {len(all_properties)} объектов")
                    
                    # Логируем статистику по городам
                    if all_properties:
                        cities_found = {}
                        for prop in all_properties:
                            city = prop.get('city', 'Не определен')
                            cities_found[city] = cities_found.get(city, 0) + 1
                        
                        logger.info(f"Распределение по городам: {cities_found}")
                    
                    return all_properties
                    
                else:
                    logger.error(f"Ошибка HTTP {response.status} при парсинге {url}")
                    return []
                    
    except asyncio.TimeoutError:
        logger.error(f"Таймаут при парсинге {category_url}")
        return []
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка сети при парсинге: {e}")
        return []
    except Exception as e:
        logger.error(f"Критическая ошибка при парсинге: {e}", exc_info=True)
        return []

async def fetch_and_filter_by_city(category_url: str, selected_city: str, 
                                 max_cards: int = 20) -> List[Dict[str, Any]]:
    """
    Парсит все карточки и фильтрует их на стороне бота
    
    Args:
        category_url: URL категории
        selected_city: Город для фильтрации
        max_cards: Максимальное количество карточек
        
    Returns:
        Отфильтрованный список недвижимости
    """
    logger.info(f"Фильтрация по городу '{selected_city}'")
    
    # 1. Парсим все карточки без фильтрации
    all_properties = await fetch_all_properties(category_url, None, max_cards * 2)
    
    # 2. Фильтруем по городу
    filtered = []
    city_synonyms = {
        'Сочи': ['сочи', 'sochi', 'адлер'],
        'Геленджик': ['геленджик', 'gelendzhik'],
        'Новороссийск': ['новороссийск', 'novorossiysk']
    }
    
    for prop in all_properties:
        city = prop.get('city', '')
        
        # Если город не определен, пытаемся определить из текста
        if city == "Не определен" and selected_city:
            full_text = prop.get('full_text', '').lower()
            
            synonyms = city_synonyms.get(selected_city, [selected_city.lower()])
            for synonym in synonyms:
                if synonym in full_text:
                    prop['city'] = selected_city
                    break
        
        # Фильтруем по точному совпадению
        if prop.get('city') == selected_city:
            filtered.append(prop)
        
        # Ограничиваем количество результатов
        if len(filtered) >= max_cards:
            break
    
    logger.info(f"После фильтрации найдено {len(filtered)} объектов в {selected_city}")
    return filtered

async def fetch_properties(category_url: str, selected_city: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Основная функция для получения свойств недвижимости
    
    Args:
        category_url: URL категории
        selected_city: Город для фильтрации
        
    Returns:
        Список недвижимости
    """
    if selected_city:
        return await fetch_and_filter_by_city(category_url, selected_city, max_cards=8)
    else:
        return await fetch_all_properties(category_url, None, max_cards=20)

async def test_parsing():
    """Тестовая функция для проверки парсинга"""
    test_url = "https://www.xn----htbkhfjn2e0c.xn--p1ai/katalog-nedvizhimosti/kvartiry/ctudii/"
    
    print("\n🔍 ТЕСТ ПАРСИНГА")
    print("=" * 50)
    
    # Анализ структуры
    cards_count = await debug_card_structure(test_url)
    print(f"\n📊 Всего карточек на странице: {cards_count}")
    
    # Тест парсинга без фильтра
    print("\n📋 Парсинг всех карточек:")
    all_props = await fetch_all_properties(test_url, None, 5)
    print(f"Найдено: {len(all_props)}")
    
    for i, prop in enumerate(all_props[:3], 1):
        print(f"{i}. {prop.get('title', 'Нет названия')[:50]}... | Город: {prop.get('city')}")
    
    # Тест парсинга с фильтром
    print("\n📍 Парсинг с фильтром 'Сочи':")
    sochi_props = await fetch_and_filter_by_city(test_url, "Сочи", 3)
    print(f"Найдено в Сочи: {len(sochi_props)}")
    
    for i, prop in enumerate(sochi_props, 1):
        print(f"{i}. {prop.get('title', 'Нет названия')[:50]}...")

# Экспорт функций
__all__ = [
    'fix_url',
    'debug_card_structure',
    'fetch_all_properties',
    'fetch_and_filter_by_city',
    'fetch_properties',
    'test_parsing'
]

# Запуск теста при прямом выполнении файла
if __name__ == "__main__":
    asyncio.run(test_parsing())