# models.py
import sqlite3
import math
from typing import List, Dict, Optional, Tuple
from api_service import api_client

DB_PATH = 'finance.db'
RESULTS_PER_PAGE = 50


class CompanyModel:
    """Модель для работы с данными компаний"""

    @staticmethod
    def get_by_inn_from_db(inn: str) -> Optional[sqlite3.Row]:
        """Получить базовую информацию о компании из БД (для поиска)"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                c.*,
                CASE
                    WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                    ELSE c.inn
                END as normalized_inn,
                COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
            FROM company c
            LEFT JOIN region r ON c.kod_re = r.kod_re
            WHERE c.inn = ? OR
                  (c.inn LIKE '%.0' AND SUBSTR(c.inn, 1, LENGTH(c.inn) - 2) = ?)
            LIMIT 1
        """, (inn, inn))

        company = cur.fetchone()
        conn.close()
        return company

    @staticmethod
    def get_by_inn_from_api(inn: str) -> Optional[Dict]:
        """Получить полную информацию о компании из API"""
        # Получаем общую информацию о компании
        company_data = api_client.get_counterparty(inn=inn, filters=["OWNER_BLOCK", "ADDRESS_BLOCK"])

        if not company_data:
            return None

        # Получаем финансовую информацию
        finance_data = api_client.get_finance(inn=inn)

        # Объединяем данные
        result = {
            'company_info': company_data,
            'finance_info': finance_data,
            'inn': inn
        }

        return result

    @staticmethod
    def get_reports_from_db(inn: str) -> List[sqlite3.Row]:
        """Получить финансовые отчеты компании из БД (для совместимости)"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT company_id
            FROM company
            WHERE inn = ? OR
                  (inn LIKE '%.0' AND SUBSTR(inn, 1, LENGTH(inn) - 2) = ?)
            LIMIT 1
        """, (inn, inn))

        company_row = cur.fetchone()
        if not company_row:
            conn.close()
            return []

        company_id = company_row['company_id']

        cur.execute("""
            SELECT *
            FROM report
            WHERE company_id = ?
            ORDER BY year
        """, (company_id,))

        reports = cur.fetchall()
        conn.close()
        return reports

    @staticmethod
    def get_similar_companies_by_okved(okved: str, current_inn: str, limit: int = 10) -> List[sqlite3.Row]:
        """Получить похожие компании по ОКВЭД"""
        if not okved:
            return []

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Ищем компании с точно таким же основным ОКВЭД, исключая текущую компанию
        cur.execute("""
            SELECT DISTINCT
                c.name,
                CASE
                    WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                    ELSE c.inn
                END as normalized_inn,
                c.okved,
                COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
            FROM company c
            LEFT JOIN region r ON c.kod_re = r.kod_re
            WHERE c.okved = ? 
            AND c.inn != ? 
            AND (c.inn NOT LIKE '%.0' OR SUBSTR(c.inn, 1, LENGTH(c.inn) - 2) != ?)
            ORDER BY c.name
            LIMIT ?
        """, (okved, current_inn, current_inn, limit))

        similar_companies = cur.fetchall()
        conn.close()
        return similar_companies


class SearchService:
    """Сервис для поиска компаний (остается без изменений)"""

    @staticmethod
    def search_by_name(search_term: str, page: int = 1) -> Tuple[List[sqlite3.Row], int]:
        """Поиск по названию компании с пагинацией"""
        search_term = search_term.upper()
        offset = (page - 1) * RESULTS_PER_PAGE

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Подсчет общего количества результатов
        cur.execute("""
            SELECT COUNT(DISTINCT CASE
                WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                ELSE c.inn
            END) as total
            FROM company c
            WHERE c.name LIKE ?
        """, (f'%{search_term}%',))

        total_results = cur.fetchone()['total']

        # Получение результатов для текущей страницы
        cur.execute("""
            SELECT
                c.name,
                CASE
                    WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                    ELSE c.inn
                END as normalized_inn,
                c.okved,
                COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
            FROM company c
            LEFT JOIN region r ON c.kod_re = r.kod_re
            WHERE c.name LIKE ?
            GROUP BY normalized_inn
            ORDER BY c.name
            LIMIT ? OFFSET ?
        """, (f'%{search_term}%', RESULTS_PER_PAGE, offset))

        results = cur.fetchall()
        conn.close()
        return results, total_results

    @staticmethod
    def search_by_inn(search_term: str, page: int = 1) -> Tuple[List[sqlite3.Row], int]:
        """Поиск по ИНН с пагинацией"""
        search_term = search_term.strip()
        offset = (page - 1) * RESULTS_PER_PAGE

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Подсчет общего количества результатов
        cur.execute("""
            SELECT COUNT(DISTINCT CASE
                WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                ELSE c.inn
            END) as total
            FROM company c
            WHERE c.inn LIKE ? OR
                  (c.inn LIKE '%.0' AND SUBSTR(c.inn, 1, LENGTH(c.inn) - 2) LIKE ?)
        """, (f'%{search_term}%', f'%{search_term}%'))

        total_results = cur.fetchone()['total']

        # Получение результатов для текущей страницы
        cur.execute("""
            SELECT
                c.name,
                CASE
                    WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                    ELSE c.inn
                END as normalized_inn,
                c.okved,
                COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
            FROM company c
            LEFT JOIN region r ON c.kod_re = r.kod_re
            WHERE c.inn LIKE ? OR
                  (c.inn LIKE '%.0' AND SUBSTR(c.inn, 1, LENGTH(c.inn) - 2) LIKE ?)
            GROUP BY normalized_inn
            ORDER BY c.name
            LIMIT ? OFFSET ?
        """, (f'%{search_term}%', f'%{search_term}%', RESULTS_PER_PAGE, offset))

        results = cur.fetchall()
        conn.close()
        return results, total_results

    @staticmethod
    def search_by_okved(search_term: str, page: int = 1) -> Tuple[List[sqlite3.Row], int]:
        """Поиск по коду ОКВЭД с пагинацией"""
        search_term = search_term.strip()
        offset = (page - 1) * RESULTS_PER_PAGE

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Подсчет общего количества результатов
        cur.execute("""
            SELECT COUNT(DISTINCT CASE
                WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                ELSE c.inn
            END) as total
            FROM company c
            WHERE c.okved LIKE ? OR c.okved_o LIKE ?
        """, (f'%{search_term}%', f'%{search_term}%'))

        total_results = cur.fetchone()['total']

        # Получение результатов для текущей страницы
        cur.execute("""
            SELECT
                c.name,
                CASE
                    WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                    ELSE c.inn
                END as normalized_inn,
                c.okved,
                COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
            FROM company c
            LEFT JOIN region r ON c.kod_re = r.kod_re
            WHERE c.okved LIKE ? OR c.okved_o LIKE ?
            GROUP BY normalized_inn
            ORDER BY c.name
            LIMIT ? OFFSET ?
        """, (f'%{search_term}%', f'%{search_term}%', RESULTS_PER_PAGE, offset))

        results = cur.fetchall()
        conn.close()
        return results, total_results

    @staticmethod
    def search_by_region(search_term: str, page: int = 1) -> Tuple[List[sqlite3.Row], int]:
        """Поиск по региону с группировкой связанных кодов и пагинацией"""
        search_term = search_term.upper()
        offset = (page - 1) * RESULTS_PER_PAGE

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Сначала находим все коды регионов, которые соответствуют поисковому запросу
        cur.execute("""
            SELECT DISTINCT kod_re, name
            FROM region
            WHERE kod_re LIKE ? OR
                  name LIKE ? OR
                  federal_district LIKE ?
        """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))

        found_regions = cur.fetchall()

        if found_regions:
            # Если нашли регионы по названию, собираем ВСЕ коды для этих регионов
            region_names = set()
            direct_codes = set()

            for region in found_regions:
                region_names.add(region['name'])
                direct_codes.add(region['kod_re'])

            # Теперь находим ВСЕ коды для найденных регионов
            if region_names:
                name_placeholders = ','.join('?' * len(region_names))
                cur.execute(f"""
                    SELECT DISTINCT kod_re
                    FROM region
                    WHERE name IN ({name_placeholders})
                """, list(region_names))

                all_related_codes = [row['kod_re'] for row in cur.fetchall()]
            else:
                all_related_codes = list(direct_codes)

            # Добавляем коды, найденные напрямую по поисковому запросу
            cur.execute("""
                SELECT DISTINCT kod_re
                FROM company
                WHERE kod_re LIKE ?
            """, (f'%{search_term}%',))

            direct_company_codes = [row['kod_re'] for row in cur.fetchall()]

            # Объединяем все коды
            all_codes = list(set(all_related_codes + direct_company_codes))

            if all_codes:
                # Подсчет общего количества результатов
                placeholders = ','.join('?' * len(all_codes))
                cur.execute(f"""
                    SELECT COUNT(DISTINCT CASE
                        WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                        ELSE c.inn
                    END) as total
                    FROM company c
                    WHERE c.kod_re IN ({placeholders})
                """, all_codes)

                total_results = cur.fetchone()['total']

                # Получение результатов для текущей страницы
                cur.execute(f"""
                    SELECT
                        c.name,
                        CASE
                            WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                            ELSE c.inn
                        END as normalized_inn,
                        c.okved,
                        COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
                    FROM company c
                    LEFT JOIN region r ON c.kod_re = r.kod_re
                    WHERE c.kod_re IN ({placeholders})
                    GROUP BY normalized_inn
                    ORDER BY c.name
                    LIMIT ? OFFSET ?
                """, all_codes + [RESULTS_PER_PAGE, offset])
            else:
                total_results = 0
                cur.execute("SELECT NULL WHERE 1=0")  # Пустой результат
        else:
            # Если по названию/округу ничего не нашли, ищем только по коду региона
            # Подсчет общего количества результатов
            cur.execute("""
                SELECT COUNT(DISTINCT CASE
                    WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                    ELSE c.inn
                END) as total
                FROM company c
                WHERE c.kod_re LIKE ?
            """, (f'%{search_term}%',))

            total_results = cur.fetchone()['total']

            # Получение результатов для текущей страницы
            cur.execute("""
                SELECT
                    c.name,
                    CASE
                        WHEN c.inn LIKE '%.0' THEN SUBSTR(c.inn, 1, LENGTH(c.inn) - 2)
                        ELSE c.inn
                    END as normalized_inn,
                    c.okved,
                    COALESCE(r.name || ', ' || r.federal_district, 'Код региона: ' || c.kod_re) as location
                FROM company c
                LEFT JOIN region r ON c.kod_re = r.kod_re
                WHERE c.kod_re LIKE ?
                GROUP BY normalized_inn
                ORDER BY c.name
                LIMIT ? OFFSET ?
            """, (f'%{search_term}%', RESULTS_PER_PAGE, offset))

        results = cur.fetchall()
        conn.close()
        return results, total_results