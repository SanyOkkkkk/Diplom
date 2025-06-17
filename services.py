# services.py
import json
from typing import Dict, List, Any, Optional
from models import CompanyModel, SearchService
import math

RESULTS_PER_PAGE = 50


class CompanyService:
    """Сервис для работы с компаниями"""

    @staticmethod
    def get_company_with_reports_from_api(inn: str) -> tuple:
        """Получить компанию и её отчеты из API"""
        # Получаем данные из API
        api_data = CompanyModel.get_by_inn_from_api(inn)

        if not api_data:
            return None, []

        # Преобразуем данные API в формат, понятный шаблонам
        company_info = api_data.get('company_info', {})
        finance_info = api_data.get('finance_info', {})

        # Создаем объект компании из данных API
        company = {
            'inn': inn,
            'name': company_info.get('company', {}).get('company_names', {}).get('short_name', 'Неизвестно'),
            'full_name': company_info.get('company', {}).get('company_names', {}).get('full_name', ''),
            'ogrn': company_info.get('ogrn', ''),
            'kpp': company_info.get('company', {}).get('kpp', ''),
            'opf': company_info.get('company', {}).get('opf', ''),
            'address': company_info.get('company', {}).get('address', {}).get('line_address', ''),
            'registration_date': company_info.get('company', {}).get('registration_date', ''),
            'charter_capital': company_info.get('company', {}).get('charter_capital', ''),
            'status': company_info.get('company', {}).get('status', {}),
            'owners': company_info.get('company', {}).get('owners', {}),
            'managers': company_info.get('company', {}).get('managers', []),
            'tax_mode_info': company_info.get('company', {}).get('tax_mode_info', {}),
            'location': company_info.get('company', {}).get('address', {}).get('line_address', ''),
            'okved': '',  # Будет заполнено из okveds если есть
            'okved_o': ''
        }

        # Получаем ОКВЭД из данных
        okveds = company_info.get('company', {}).get('okveds', [])
        if okveds:
            company['okved'] = okveds[0] if len(okveds) > 0 else ''
            company['okved_o'] = ', '.join(okveds[1:]) if len(okveds) > 1 else ''

        # Преобразуем финансовые данные в формат отчетов
        reports = CompanyService._convert_api_finance_to_reports(finance_info)

        return company, reports

    @staticmethod
    def _convert_api_finance_to_reports(finance_info: Dict) -> List[Dict]:
        """Преобразует финансовые данные из API в формат отчетов"""
        if not finance_info:
            return []

        reports = []

        # Получаем данные баланса
        balances = finance_info.get('balances', {})
        fin_results = finance_info.get('fin_results', {})

        # Получаем годы
        balance_years = balances.get('years', [])
        fin_years = fin_results.get('years', [])

        # Объединяем годы
        all_years = sorted(set(balance_years + fin_years))

        for year in all_years:
            year_str = str(year)

            report = {
                'year': year,
                # Данные из баланса
                'intangible_assets_eoy': CompanyService._get_balance_value(balances, '1110', year_str),
                'curr_assets_eoy': CompanyService._get_balance_value(balances, '1200', year_str),
                'balance_assets_eoy': CompanyService._get_balance_value(balances, '1600', year_str),
                'equity_eoy': CompanyService._get_balance_value(balances, '1300', year_str),
                'lt_liabilities_eoy': CompanyService._get_balance_value(balances, '1400', year_str),
                'st_liabilities_eoy': CompanyService._get_balance_value(balances, '1500', year_str),
                'balance_liab_eoy': CompanyService._get_balance_value(balances, '1700', year_str),

                # Данные из отчета о прибылях и убытках
                'revenue_cur': CompanyService._get_fin_result_value(fin_results, '2110', year_str),
                'gross_profit_cur': CompanyService._get_fin_result_value(fin_results, '2100', year_str),
                'oper_profit_cur': CompanyService._get_fin_result_value(fin_results, '2200', year_str),
                'pbt_cur': CompanyService._get_fin_result_value(fin_results, '2300', year_str),
                'income_tax_cur': CompanyService._get_fin_result_value(fin_results, '2410', year_str),
                'net_profit_cur': CompanyService._get_fin_result_value(fin_results, '2400', year_str),
            }

            reports.append(report)

        return sorted(reports, key=lambda x: x['year'])

    @staticmethod
    def _get_balance_value(balances: Dict, code: str, year: str) -> Optional[float]:
        """Получает значение из баланса по коду и году"""
        try:
            indicators = balances.get('indicators', [])
            for indicator in indicators:
                if indicator.get('code') == code:
                    sum_data = indicator.get('sum', {})
                    return sum_data.get(year, 0.0) or 0.0
            return 0.0
        except (KeyError, TypeError, ValueError):
            return 0.0

    @staticmethod
    def _get_fin_result_value(fin_results: Dict, code: str, year: str) -> Optional[float]:
        """Получает значение из отчета о прибылях и убытках по коду и году"""
        try:
            indicators = fin_results.get('indicators', [])
            for indicator in indicators:
                if indicator.get('code') == code:
                    sum_data = indicator.get('sum', {})
                    return sum_data.get(year, 0.0) or 0.0
            return 0.0
        except (KeyError, TypeError, ValueError):
            return 0.0

    @staticmethod
    def prepare_analytics_data(reports: List[Dict]) -> tuple:
        """Подготовить данные для аналитики"""
        chart_data = {
            'years': [],
            'revenue': [],
            'net_profit': [],
            'assets': [],
            'equity': [],
            'profitability': []
        }

        enhanced_reports = []
        for report in reports:
            # Рассчитываем рентабельность по выручке
            revenue = report.get('revenue_cur', 0)
            net_profit = report.get('net_profit_cur', 0)

            if revenue and net_profit and revenue != 0:
                profitability = (net_profit / revenue) * 100
                report['profitability'] = profitability
            else:
                report['profitability'] = None

            enhanced_reports.append(report)

            # Заполняем данные для графиков
            chart_data['years'].append(report['year'])
            chart_data['revenue'].append(revenue or 0)
            chart_data['net_profit'].append(net_profit or 0)
            chart_data['assets'].append(report.get('balance_assets_eoy', 0) or 0)
            chart_data['equity'].append(report.get('equity_eoy', 0) or 0)
            chart_data['profitability'].append(report.get('profitability', 0) or 0)

        return enhanced_reports, json.dumps(chart_data)


class SearchServiceFacade:
    """Фасад для поисковых сервисов (остается без изменений)"""

    @staticmethod
    def search_companies(query: str, search_type: str, page: int = 1) -> tuple:
        """Поиск компаний по заданным параметрам"""
        if not query:
            return [], 0

        if search_type == "inn":
            companies, total_results = SearchService.search_by_inn(query, page)
        elif search_type == "okved":
            companies, total_results = SearchService.search_by_okved(query, page)
        elif search_type == "region":
            companies, total_results = SearchService.search_by_region(query, page)
        else:  # name
            companies, total_results = SearchService.search_by_name(query, page)

        total_pages = math.ceil(total_results / RESULTS_PER_PAGE)
        return companies, total_results, total_pages


class SessionManager:
    """Менеджер для работы с сессиями (остается без изменений)"""

    @staticmethod
    def save_search_params(session: dict, query: str, search_type: str, page: int):
        """Сохранить параметры поиска в сессии"""
        session['last_search'] = {
            'query': query,
            'search_type': search_type,
            'page': page
        }

    @staticmethod
    def get_last_search(session: dict) -> dict:
        """Получить последние параметры поиска из сессии"""
        return session.get('last_search', {
            'query': '',
            'search_type': 'name',
            'page': 1
        })