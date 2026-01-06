import math
from typing import Dict, List, Any
from datetime import datetime

class MortgageCalculator:
    """
    Калькулятор ипотеки с полным набором функций по формулам calcus.ru
    
    Основные возможности:
    1. Расчет аннуитетных и дифференцированных платежей
    2. Расчет с первоначальным взносом
    3. Определение максимальной суммы по доходу
    4. Сравнение нескольких вариантов
    5. Расчет досрочного погашения
    6. Учет страховки и других расходов
    """
    
    @staticmethod
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
        if amount >= 1000000:
            formatted = f"{amount:,.2f}"
        else:
            formatted = f"{amount:,.0f}"
        
        # Заменяем точку на запятую для рублевого формата
        formatted = formatted.replace(",", " ").replace(".", ",")
        
        return f"{formatted} ₽"
    
    @staticmethod
    def calculate_annuity_coefficient(monthly_rate: float, months: int) -> float:
        """
        Рассчитывает коэффициент аннуитета
        
        Args:
            monthly_rate: Месячная процентная ставка (в долях)
            months: Количество месяцев
            
        Returns:
            Коэффициент аннуитета
        """
        if monthly_rate == 0:
            return 1 / months
        
        numerator = monthly_rate * math.pow(1 + monthly_rate, months)
        denominator = math.pow(1 + monthly_rate, months) - 1
        
        return numerator / denominator
    
    @staticmethod
    def calculate_annuity_payment(loan_amount: float, monthly_rate: float, months: int) -> float:
        """
        Рассчитывает аннуитетный платеж
        
        Args:
            loan_amount: Сумма кредита
            monthly_rate: Месячная процентная ставка (в долях)
            months: Количество месяцев
            
        Returns:
            Ежемесячный платеж
        """
        coefficient = MortgageCalculator.calculate_annuity_coefficient(monthly_rate, months)
        return loan_amount * coefficient
    
    @staticmethod
    def calculate_differentiated_payment(loan_amount: float, monthly_rate: float, 
                                       months: int, current_month: int) -> Dict[str, float]:
        """
        Рассчитывает дифференцированный платеж для конкретного месяца
        
        Args:
            loan_amount: Сумма кредита
            monthly_rate: Месячная процентная ставка (в долях)
            months: Общее количество месяцев
            current_month: Текущий месяц (начиная с 1)
            
        Returns:
            Словарь с данными платежа
        """
        # Основной долг каждый месяц одинаковый
        principal_payment = loan_amount / months
        
        # Остаток долга на начало месяца
        remaining_debt = loan_amount - principal_payment * (current_month - 1)
        
        # Проценты за месяц
        interest_payment = remaining_debt * monthly_rate
        
        # Общий платеж
        total_payment = principal_payment + interest_payment
        
        # Новый остаток долга
        new_remaining = remaining_debt - principal_payment
        
        return {
            'principal': principal_payment,
            'interest': interest_payment,
            'total': total_payment,
            'remaining': new_remaining
        }
    
    @staticmethod
    def calculate_annuity(loan_amount: float, annual_rate: float, years: int, 
                         include_schedule: bool = True) -> Dict[str, Any]:
        """
        Основной расчет аннуитетной ипотеки
        
        Args:
            loan_amount: Сумма кредита
            annual_rate: Годовая процентная ставка (%)
            years: Срок кредита в годах
            include_schedule: Включать ли график платежей
            
        Returns:
            Словарь с результатами расчета
        """
        try:
            # Проверка входных данных
            if loan_amount <= 0:
                raise ValueError("Сумма кредита должна быть положительной")
            if annual_rate < 0:
                raise ValueError("Процентная ставка не может быть отрицательной")
            if years <= 0 or years > 50:
                raise ValueError("Срок кредита должен быть от 1 до 50 лет")
            
            # Конвертируем параметры
            months = years * 12
            monthly_rate = annual_rate / 12 / 100  # Переводим в доли
            
            # Рассчитываем ежемесячный платеж
            monthly_payment = MortgageCalculator.calculate_annuity_payment(
                loan_amount, monthly_rate, months
            )
            
            # Общая сумма выплат
            total_paid = monthly_payment * months
            
            # Переплата
            overpayment = total_paid - loan_amount
            overpayment_percent = (overpayment / loan_amount * 100) if loan_amount > 0 else 0
            
            # Коэффициент аннуитета
            coefficient = MortgageCalculator.calculate_annuity_coefficient(monthly_rate, months)
            
            # График платежей (первые 6 месяцев)
            schedule = []
            if include_schedule:
                remaining = loan_amount
                
                for month in range(1, min(7, months + 1)):
                    interest = remaining * monthly_rate
                    principal = monthly_payment - interest
                    remaining -= principal
                    
                    schedule.append({
                        'month': month,
                        'payment': monthly_payment,
                        'principal': principal,
                        'interest': interest,
                        'remaining': max(remaining, 0)
                    })
            
            # Формируем результат
            result = {
                'success': True,
                'loan_amount': loan_amount,
                'annual_rate': annual_rate,
                'years': years,
                'months': months,
                'monthly_payment': round(monthly_payment, 2),
                'total_paid': round(total_paid, 2),
                'overpayment': round(overpayment, 2),
                'overpayment_percent': round(overpayment_percent, 2),
                'coefficient': round(coefficient, 6),
                'payment_type': 'annuity'
            }
            
            if include_schedule:
                result['schedule_first_6'] = schedule
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'loan_amount': loan_amount,
                'annual_rate': annual_rate,
                'years': years
            }
    
    @staticmethod
    def calculate_differentiated(loan_amount: float, annual_rate: float, years: int,
                               include_schedule: bool = True) -> Dict[str, Any]:
        """
        Расчет дифференцированной ипотеки
        
        Args:
            loan_amount: Сумма кредита
            annual_rate: Годовая процентная ставка (%)
            years: Срок кредита в годах
            include_schedule: Включать ли график платежей
            
        Returns:
            Словарь с результатами расчета
        """
        try:
            # Проверка входных данных
            if loan_amount <= 0:
                raise ValueError("Сумма кредита должна быть положительной")
            if annual_rate < 0:
                raise ValueError("Процентная ставка не может быть отрицательной")
            if years <= 0 or years > 50:
                raise ValueError("Срок кредита должен быть от 1 до 50 лет")
            
            # Конвертируем параметры
            months = years * 12
            monthly_rate = annual_rate / 12 / 100
            
            # Рассчитываем общие показатели
            total_interest = 0
            payments = []
            
            remaining = loan_amount
            principal_payment = loan_amount / months
            
            # Рассчитываем каждый месяц
            for month in range(1, months + 1):
                month_data = MortgageCalculator.calculate_differentiated_payment(
                    loan_amount, monthly_rate, months, month
                )
                
                total_interest += month_data['interest']
                remaining = month_data['remaining']
                
                if include_schedule and month <= 6:
                    payments.append({
                        'month': month,
                        'payment': month_data['total'],
                        'principal': month_data['principal'],
                        'interest': month_data['interest'],
                        'remaining': remaining
                    })
            
            # Первый и последний платеж
            first_payment = MortgageCalculator.calculate_differentiated_payment(
                loan_amount, monthly_rate, months, 1
            )['total']
            
            last_payment = MortgageCalculator.calculate_differentiated_payment(
                loan_amount, monthly_rate, months, months
            )['total']
            
            # Общая сумма выплат
            total_paid = loan_amount + total_interest
            overpayment = total_interest
            overpayment_percent = (overpayment / loan_amount * 100) if loan_amount > 0 else 0
            
            # Формируем результат
            result = {
                'success': True,
                'loan_amount': loan_amount,
                'annual_rate': annual_rate,
                'years': years,
                'months': months,
                'first_payment': round(first_payment, 2),
                'last_payment': round(last_payment, 2),
                'average_payment': round(total_paid / months, 2),
                'total_paid': round(total_paid, 2),
                'overpayment': round(overpayment, 2),
                'overpayment_percent': round(overpayment_percent, 2),
                'payment_type': 'differentiated'
            }
            
            if include_schedule:
                result['schedule_first_6'] = payments
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'loan_amount': loan_amount,
                'annual_rate': annual_rate,
                'years': years
            }
    
    @staticmethod
    def calculate_with_downpayment(total_cost: float, downpayment_percent: float,
                                 annual_rate: float, years: int) -> Dict[str, Any]:
        """
        Расчет ипотеки с первоначальным взносом
        
        Args:
            total_cost: Общая стоимость недвижимости
            downpayment_percent: Процент первоначального взноса
            annual_rate: Годовая процентная ставка (%)
            years: Срок кредита в годах
            
        Returns:
            Словарь с результатами расчета
        """
        try:
            # Проверка входных данных
            if total_cost <= 0:
                raise ValueError("Стоимость недвижимости должна быть положительной")
            if downpayment_percent < 0 or downpayment_percent >= 100:
                raise ValueError("Процент первоначального взноса должен быть от 0 до 99%")
            if annual_rate < 0:
                raise ValueError("Процентная ставка не может быть отрицательной")
            if years <= 0 or years > 50:
                raise ValueError("Срок кредита должен быть от 1 до 50 лет")
            
            # Рассчитываем суммы
            downpayment_amount = total_cost * downpayment_percent / 100
            loan_amount = total_cost - downpayment_amount
            
            # Расчет ипотеки
            mortgage_result = MortgageCalculator.calculate_annuity(
                loan_amount, annual_rate, years
            )
            
            # Объединяем результаты
            if mortgage_result['success']:
                result = {
                    **mortgage_result,
                    'total_cost': total_cost,
                    'downpayment_percent': downpayment_percent,
                    'downpayment_amount': round(downpayment_amount, 2),
                    'own_funds_percent': downpayment_percent,
                    'own_funds_amount': round(downpayment_amount, 2),
                    'loan_to_value': round((loan_amount / total_cost * 100), 2)  # LTV ratio
                }
                return result
            else:
                return mortgage_result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_cost': total_cost,
                'downpayment_percent': downpayment_percent,
                'annual_rate': annual_rate,
                'years': years
            }
    
    @staticmethod
    def max_affordable_loan(monthly_income: float, annual_rate: float, years: int,
                           other_loans: float = 0, dependents: int = 0) -> Dict[str, Any]:
        """
        Расчет максимальной суммы кредита по доходу
        
        Args:
            monthly_income: Ежемесячный доход после налогов
            annual_rate: Годовая процентная ставка (%)
            years: Срок кредита в годах
            other_loans: Другие ежемесячные кредитные платежи
            dependents: Количество иждивенцев
            
        Returns:
            Словарь с результатами расчета
        """
        try:
            # Проверка входных данных
            if monthly_income <= 0:
                raise ValueError("Доход должен быть положительным")
            if annual_rate < 0:
                raise ValueError("Процентная ставка не может быть отрицательной")
            if years <= 0 or years > 50:
                raise ValueError("Срок кредита должен быть от 1 до 50 лет")
            
            # Рассчитываем прожиточный минимум (примерно)
            living_wage_per_person = 15000  # рублей
            total_living_wage = living_wage_per_person * (1 + dependents)
            
            # Доступный платеж (40% от чистого дохода минус другие кредиты)
            available_income = monthly_income - other_loans - total_living_wage
            if available_income <= 0:
                return {
                    'success': True,
                    'max_loan': 0,
                    'available_payment': 0,
                    'message': 'Доход недостаточен для кредита'
                }
            
            max_payment = available_income * 0.4  # Банки обычно дают до 40% от дохода
            
            # Конвертируем параметры
            months = years * 12
            monthly_rate = annual_rate / 12 / 100
            
            # Рассчитываем максимальную сумму кредита
            if monthly_rate == 0:
                max_loan = max_payment * months
            else:
                coefficient = MortgageCalculator.calculate_annuity_coefficient(monthly_rate, months)
                max_loan = max_payment / coefficient
            
            # Пример стоимости недвижимости при 20% первоначальном взносе
            example_downpayment_percent = 20
            example_property_cost = max_loan / (1 - example_downpayment_percent / 100)
            example_downpayment = example_property_cost * example_downpayment_percent / 100
            
            return {
                'success': True,
                'monthly_income': monthly_income,
                'annual_rate': annual_rate,
                'years': years,
                'available_payment': round(max_payment, 2),
                'max_loan': round(max_loan, 2),
                'example_property_cost': round(example_property_cost, 2),
                'example_downpayment': round(example_downpayment, 2),
                'example_downpayment_percent': example_downpayment_percent,
                'payment_to_income_ratio': round((max_payment / monthly_income * 100), 2)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'monthly_income': monthly_income,
                'annual_rate': annual_rate,
                'years': years
            }
    
    @staticmethod
    def compare_scenarios(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Сравнение нескольких вариантов ипотеки
        
        Args:
            scenarios: Список сценариев для сравнения
            
        Returns:
            Словарь с результатами сравнения
        """
        try:
            if not scenarios:
                raise ValueError("Необходимо указать хотя бы один сценарий")
            
            results = []
            
            for i, scenario in enumerate(scenarios, 1):
                # Извлекаем параметры
                calc_type = scenario.get('type', 'annuity')
                
                if calc_type == 'with_downpayment':
                    result = MortgageCalculator.calculate_with_downpayment(
                        total_cost=scenario.get('total_cost', 0),
                        downpayment_percent=scenario.get('downpayment_percent', 20),
                        annual_rate=scenario.get('annual_rate', 7),
                        years=scenario.get('years', 20)
                    )
                elif calc_type == 'annuity':
                    result = MortgageCalculator.calculate_annuity(
                        loan_amount=scenario.get('loan_amount', 0),
                        annual_rate=scenario.get('annual_rate', 7),
                        years=scenario.get('years', 20)
                    )
                elif calc_type == 'differentiated':
                    result = MortgageCalculator.calculate_differentiated(
                        loan_amount=scenario.get('loan_amount', 0),
                        annual_rate=scenario.get('annual_rate', 7),
                        years=scenario.get('years', 20)
                    )
                else:
                    continue
                
                if result['success']:
                    results.append({
                        'scenario_number': i,
                        'scenario_name': scenario.get('name', f'Вариант {i}'),
                        **result
                    })
            
            if not results:
                return {
                    'success': False,
                    'error': 'Не удалось рассчитать ни один сценарий'
                }
            
            # Находим лучший вариант по разным критериям
            best_by_payment = min(results, key=lambda x: x['monthly_payment'])
            best_by_overpayment = min(results, key=lambda x: x['overpayment'])
            best_by_total = min(results, key=lambda x: x['total_paid'])
            
            return {
                'success': True,
                'scenarios_count': len(results),
                'scenarios': results,
                'best_by_payment': best_by_payment,
                'best_by_overpayment': best_by_overpayment,
                'best_by_total': best_by_total,
                'comparison_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'scenarios_count': len(scenarios)
            }
    
    @staticmethod
    def early_repayment_calculation(loan_amount: float, annual_rate: float, years: int,
                                  early_month: int, early_amount: float,
                                  repayment_type: str = 'reduce_payment') -> Dict[str, Any]:
        """
        Расчет досрочного погашения
        
        Args:
            loan_amount: Сумма кредита
            annual_rate: Годовая процентная ставка (%)
            years: Срок кредита в годах
            early_month: В какой месяц вносится досрочный платеж
            early_amount: Сумма досрочного погашения
            repayment_type: Тип досрочного погашения:
                           'reduce_payment' - уменьшение платежа
                           'reduce_term' - уменьшение срока
                           
        Returns:
            Словарь с результатами расчета
        """
        try:
            # Проверка входных данных
            if loan_amount <= 0:
                raise ValueError("Сумма кредита должна быть положительной")
            if annual_rate < 0:
                raise ValueError("Процентная ставка не может быть отрицательной")
            if years <= 0 or years > 50:
                raise ValueError("Срок кредита должен быть от 1 до 50 лет")
            if early_month <= 0:
                raise ValueError("Месяц досрочного погашения должен быть положительным")
            if early_amount <= 0:
                raise ValueError("Сумма досрочного погашения должна быть положительной")
            
            # Рассчитываем исходный график
            original = MortgageCalculator.calculate_annuity(loan_amount, annual_rate, years)
            
            if not original['success']:
                return original
            
            # Параметры кредита
            months = years * 12
            monthly_rate = annual_rate / 12 / 100
            original_payment = original['monthly_payment']
            
            # Имитируем выплаты до досрочного погашения
            remaining = loan_amount
            total_paid_before = 0
            total_interest_before = 0
            
            for month in range(1, early_month + 1):
                interest = remaining * monthly_rate
                principal = original_payment - interest
                remaining -= principal
                total_paid_before += original_payment
                total_interest_before += interest
                
                # Вносим досрочный платеж
                if month == early_month:
                    if early_amount >= remaining:
                        # Полное досрочное погашение
                        total_paid_before += remaining
                        remaining = 0
                    else:
                        # Частичное досрочное погашение
                        total_paid_before += early_amount
                        remaining -= early_amount
            
            if remaining <= 0:
                # Кредит полностью погашен
                return {
                    'success': True,
                    'original_payment': original_payment,
                    'new_payment': 0,
                    'remaining_debt': 0,
                    'total_savings': round(original['total_paid'] - total_paid_before, 2),
                    'months_saved': months - early_month,
                    'total_paid_with_early': round(total_paid_before, 2),
                    'early_repayment_type': 'full',
                    'message': 'Кредит полностью погашен досрочно'
                }
            
            # Пересчитываем оставшиеся платежи
            remaining_months = months - early_month
            
            if repayment_type == 'reduce_payment':
                # Уменьшение платежа при том же сроке
                new_payment = MortgageCalculator.calculate_annuity_payment(
                    remaining, monthly_rate, remaining_months
                )
                new_months = remaining_months
                
            elif repayment_type == 'reduce_term':
                # Уменьшение срока при том же платеже
                # Находим новый срок методом подбора
                new_months = 0
                test_remaining = remaining
                
                while test_remaining > 0 and new_months < remaining_months * 2:
                    new_months += 1
                    interest = test_remaining * monthly_rate
                    if original_payment <= interest:
                        break
                    principal = original_payment - interest
                    test_remaining -= principal
                
                new_payment = original_payment
                
            else:
                raise ValueError("Неизвестный тип досрочного погашения")
            
            # Рассчитываем общую сумму выплат с досрочным погашением
            total_paid_after = total_paid_before + (new_payment * new_months)
            savings = original['total_paid'] - total_paid_after
            
            return {
                'success': True,
                'original_payment': original_payment,
                'new_payment': round(new_payment, 2),
                'remaining_debt': round(remaining, 2),
                'total_savings': round(savings, 2),
                'months_saved': remaining_months - new_months if repayment_type == 'reduce_term' else 0,
                'payment_reduced': round(original_payment - new_payment, 2) if repayment_type == 'reduce_payment' else 0,
                'total_paid_with_early': round(total_paid_after, 2),
                'early_repayment_type': repayment_type,
                'new_months': new_months
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'loan_amount': loan_amount,
                'annual_rate': annual_rate,
                'years': years,
                'early_month': early_month,
                'early_amount': early_amount,
                'repayment_type': repayment_type
            }
    
    @staticmethod
    def calculate_effective_rate(loan_amount: float, annual_rate: float, years: int,
                               insurance_percent: float = 0.3, other_fees: float = 0) -> Dict[str, Any]:
        """
        Расчет эффективной процентной ставки с учетом всех расходов
        
        Args:
            loan_amount: Сумма кредита
            annual_rate: Номинальная годовая ставка (%)
            years: Срок кредита в годах
            insurance_percent: Процент страховки от остатка долга
            other_fees: Другие единовременные расходы
            
        Returns:
            Словарь с эффективной ставкой
        """
        try:
            # Рассчитываем базовый платеж
            base_result = MortgageCalculator.calculate_annuity(loan_amount, annual_rate, years)
            
            if not base_result['success']:
                return base_result
            
            # Добавляем страховку к ставке
            effective_rate = annual_rate + insurance_percent
            
            # Рассчитываем общую сумму выплат с учетом всех расходов
            months = years * 12
            monthly_insurance_rate = insurance_percent / 12 / 100
            
            # Сумма страховых выплат (упрощенный расчет)
            total_insurance = 0
            remaining = loan_amount
            
            for _ in range(months):
                insurance_payment = remaining * monthly_insurance_rate
                total_insurance += insurance_payment
                
                # Уменьшаем остаток (примерно)
                monthly_payment = base_result['monthly_payment']
                interest = remaining * (annual_rate / 12 / 100)
                principal = monthly_payment - interest
                remaining -= principal
            
            # Общая стоимость кредита
            total_cost = base_result['total_paid'] + total_insurance + other_fees
            
            # Находим эффективную ставку методом приближения
            # (упрощенный расчет - в реальности используется сложная формула ЦБ)
            effective_rate_per_month = effective_rate / 12 / 100
            
            payment_with_fees = MortgageCalculator.calculate_annuity_payment(
                loan_amount + other_fees, effective_rate_per_month, months
            )
            
            total_with_fees = payment_with_fees * months
            
            return {
                'success': True,
                'nominal_rate': annual_rate,
                'effective_rate': round(effective_rate, 2),
                'insurance_adds': insurance_percent,
                'base_payment': round(base_result['monthly_payment'], 2),
                'payment_with_insurance': round(payment_with_fees, 2),
                'total_insurance': round(total_insurance, 2),
                'other_fees': other_fees,
                'total_cost_with_fees': round(total_with_fees, 2),
                'difference': round(total_with_fees - base_result['total_paid'], 2)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Экспорт класса
__all__ = ['MortgageCalculator']

# Пример использования
if __name__ == "__main__":
    print("🔍 ТЕСТ КАЛЬКУЛЯТОРА ИПОТЕКИ")
    print("=" * 50)
    
    # Тест 1: Базовая ипотека
    print("\n📊 Тест 1: Базовая ипотека")
    result1 = MortgageCalculator.calculate_annuity(
        loan_amount=5000000,
        annual_rate=7.5,
        years=20
    )
    
    if result1['success']:
        print(f"Ежемесячный платеж: {MortgageCalculator.format_currency(result1['monthly_payment'])}")
        print(f"Общая переплата: {MortgageCalculator.format_currency(result1['overpayment'])}")
        print(f"Процент переплаты: {result1['overpayment_percent']}%")
    
    # Тест 2: С первоначальным взносом
    print("\n🏠 Тест 2: С первоначальным взносом")
    result2 = MortgageCalculator.calculate_with_downpayment(
        total_cost=8000000,
        downpayment_percent=20,
        annual_rate=7.5,
        years=20
    )
    
    if result2['success']:
        print(f"Первоначальный взнос: {MortgageCalculator.format_currency(result2['downpayment_amount'])}")
        print(f"Сумма кредита: {MortgageCalculator.format_currency(result2['loan_amount'])}")
        print(f"Ежемесячный платеж: {MortgageCalculator.format_currency(result2['monthly_payment'])}")
    
    # Тест 3: Расчет по доходу
    print("\n💰 Тест 3: Сколько можно взять по доходу")
    result3 = MortgageCalculator.max_affordable_loan(
        monthly_income=150000,
        annual_rate=7.5,
        years=20
    )
    
    if result3['success']:
        print(f"Максимальный кредит: {MortgageCalculator.format_currency(result3['max_loan'])}")
        print(f"Примерная стоимость жилья: {MortgageCalculator.format_currency(result3['example_property_cost'])}")