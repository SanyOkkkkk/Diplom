import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("finance.db")     # Файл БД

#
# 1.  Карта полей CSV -> полей таблицы report
#
FIELD_MAP = {
    # Актив
    "11003": "intangible_assets_eoy",
    "11004": "intangible_assets_poy",
    "12003": "curr_assets_eoy",
    "12004": "curr_assets_poy",
    "16003": "balance_assets_eoy",
    "16004": "balance_assets_poy",
    # Капитал и результаты
    "13703": "retained_earnings_eoy",
    "13704": "retained_earnings_poy",
    "13003": "equity_eoy",
    "13004": "equity_poy",
    # Обязательства
    "14003": "lt_liabilities_eoy",
    "14004": "lt_liabilities_poy",
    "15003": "st_liabilities_eoy",
    "15004": "st_liabilities_poy",
    "17003": "balance_liab_eoy",
    "17004": "balance_liab_poy",
    # Отчёт о фин‑результатах
    "21103": "revenue_cur",
    "21104": "revenue_prev",
    "21003": "gross_profit_cur",
    "21004": "gross_profit_prev",
    "22003": "oper_profit_cur",
    "22004": "oper_profit_prev",
    "23003": "pbt_cur",
    "23004": "pbt_prev",
    "24103": "income_tax_cur",
    "24104": "income_tax_prev",
    "24003": "net_profit_cur",
    "24004": "net_profit_prev",
}

NUMERIC_COLS = set(FIELD_MAP.keys())           # коды‑числа
COMPANY_COLS = ("name", "inn", "okved", "okved_o",
                "measure", "tip", "kod_re")


def _clean_num(value: str):
    """'' -> None, иначе float"""
    if value == "" or value is None:
        return None
    return float(value.replace(" ", "").replace(",", "."))


def load(year):
    CSV_PATH = Path(f"data/company_us_{year}_predobrabotka.csv")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # ---- 2.  Company ----------------------------------------------
            company_data = (
                row["name"].strip(),    # имя уже без внешних кавычек
                row["inn"].strip(),
                row["okved"].strip(),
                row["okved_o"].strip(),
                row["measure"].strip(),
                row["tip"].strip(),
                row["kod_re"].strip(),
            )

            cur.execute("""
            INSERT INTO company (name, inn, okved, okved_o, measure, tip, kod_re)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(inn) DO UPDATE SET
                name      = excluded.name,
                okved     = excluded.okved,
                okved_o   = excluded.okved_o,
                measure   = excluded.measure,
                tip       = excluded.tip,
                kod_re    = excluded.kod_re
            """, company_data)

            cur.execute("SELECT company_id FROM company WHERE inn = ?", (row["inn"],))
            company_id = cur.fetchone()[0]


            # 3.2 Собираем значения показателей
            report_values = {
                "company_id": company_id,
                "year":       year,
            }
            for code_csv, col_db in FIELD_MAP.items():
                report_values[col_db] = _clean_num(row[code_csv])

            # 3.3 Динамический INSERT ... ON CONFLICT
            cols = ", ".join(report_values.keys())
            ph   = ", ".join("?" for _ in report_values)
            updates = ", ".join(f"{c}=excluded.{c}" for c in report_values if c not in ("company_id", "year"))

            cur.execute(f"""
            INSERT INTO report ({cols})
            VALUES ({ph})
            ON CONFLICT(company_id, year) DO UPDATE SET
            {updates}
            """, tuple(report_values.values()))

    conn.commit()
    conn.close()
    print("Импорт завершён.")

if __name__ == "__main__":
    for y in range(2012, 2019):
        print(f"Загружаем данные за {y} год")
        load(y)
