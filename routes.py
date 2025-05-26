from flask import render_template, request, session
from services import CompanyService, SearchServiceFacade, SessionManager


class SearchController:
    """Контроллер для поиска"""

    @staticmethod
    def index():
        companies = []
        query = ""
        search_type = "name"
        current_page = 1
        total_results = 0
        total_pages = 0

        if request.method == "POST":
            query = request.form.get("query", "").strip()
            search_type = request.form.get("search_type", "name")
            current_page = int(request.form.get("page", 1))

            SessionManager.save_search_params(session, query, search_type, current_page)

            if query:
                companies, total_results, total_pages = SearchServiceFacade.search_companies(
                    query, search_type, current_page
                )

        elif request.method == "GET" and request.args.get("query"):
            # Обработка GET-запросов для пагинации
            query = request.args.get("query", "").strip()
            search_type = request.args.get("search_type", "name")
            current_page = int(request.args.get("page", 1))

            SessionManager.save_search_params(session, query, search_type, current_page)

            if query:
                companies, total_results, total_pages = SearchServiceFacade.search_companies(
                    query, search_type, current_page
                )

        elif request.method == "GET" and not request.args.get("query"):
            # Восстановление последнего поиска
            last_search = SessionManager.get_last_search(session)
            query = last_search.get('query', '')
            search_type = last_search.get('search_type', 'name')
            current_page = last_search.get('page', 1)

            if query:
                companies, total_results, total_pages = SearchServiceFacade.search_companies(
                    query, search_type, current_page
                )

        return render_template("search.html",
                               companies=companies,
                               query=query,
                               search_type=search_type,
                               current_page=current_page,
                               total_pages=total_pages,
                               total_results=total_results,
                               results_per_page=50)


class CompanyController:
    """Контроллер для работы с компаниями"""

    @staticmethod
    def company_details(inn: str):
        """Страница с детальной информацией о компании"""
        company, reports = CompanyService.get_company_with_reports(inn)

        if not company:
            return render_template("search.html", error="Компания не найдена"), 404

        return render_template("company_details.html",
                               company=company,
                               reports=reports)

    @staticmethod
    def analytics(inn: str):
        """Страница с финансовой аналитикой компании"""
        company, reports = CompanyService.get_company_with_reports(inn)

        if not company:
            return render_template("search.html", error="Компания не найдена"), 404

        enhanced_reports, chart_data = CompanyService.prepare_analytics_data(reports)

        return render_template("analytics.html",
                               company=company,
                               reports=enhanced_reports,
                               chart_data=chart_data)