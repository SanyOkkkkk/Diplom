import json
from typing import Dict, List, Any
from models import CompanyModel, SearchService
import math

RESULTS_PER_PAGE = 50


class CompanyService:
    """Сервис для работы с компаниями"""

    @staticmethod
    def get_company_with_reports(inn: str) -> tuple:
        """Получить компанию и её отчеты"""
        company = CompanyModel.get_by_inn(inn)
        if not company:
            return None, []

        reports = CompanyModel.get_reports(inn)
        return company, reports

    @staticmethod
    def prepare_analytics_data(reports: List) -> tuple:
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
            report_dict = dict(report)

            # Рассчитываем рентабельность по выручке
            if report['revenue_cur'] and report['net_profit_cur'] and report['revenue_cur'] != 0:
                profitability = (report['net_profit_cur'] / report['revenue_cur']) * 100
                report_dict['profitability'] = profitability
            else:
                report_dict['profitability'] = None

            enhanced_reports.append(report_dict)

            # Заполняем данные для графиков
            chart_data['years'].append(report['year'])
            chart_data['revenue'].append(report['revenue_cur'] if report['revenue_cur'] else 0)
            chart_data['net_profit'].append(report['net_profit_cur'] if report['net_profit_cur'] else 0)
            chart_data['assets'].append(report['balance_assets_eoy'] if report['balance_assets_eoy'] else 0)
            chart_data['equity'].append(report['equity_eoy'] if report['equity_eoy'] else 0)
            chart_data['profitability'].append(report_dict['profitability'] if report_dict['profitability'] else 0)

        return enhanced_reports, json.dumps(chart_data)


class SearchServiceFacade:
    """Фасад для поисковых сервисов"""

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
    """Менеджер для работы с сессиями"""

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