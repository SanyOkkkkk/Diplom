import sqlite3

def create_database(db_path: str):
    ddl = """
    -- -------------------------------------------------
    -- 1.  Companies
    -- -------------------------------------------------
    CREATE TABLE IF NOT EXISTS company (
        company_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        inn          TEXT    NOT NULL,            -- Russian TIN
        okved        TEXT,                        -- main OKVED
        okved_o      TEXT,                        -- additional OKVED
        measure      TEXT,                        -- units of measure
        tip          TEXT,                        -- form of ownership etc.
        kod_re       TEXT                         -- region code
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_company_inn ON company(inn);

    -- -------------------------------------------------
    -- 2.  Yearly reports
    -- -------------------------------------------------
    CREATE TABLE IF NOT EXISTS report (
        report_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id                  INTEGER NOT NULL,
        year                        INTEGER NOT NULL,

        -- Актив
        intangible_assets_eoy       REAL,   -- 11003
        intangible_assets_poy       REAL,   -- 11004
        curr_assets_eoy             REAL,   -- 12003
        curr_assets_poy             REAL,   -- 12004
        balance_assets_eoy          REAL,   -- 16003
        balance_assets_poy          REAL,   -- 16004

        -- Капитал и результаты
        retained_earnings_eoy       REAL,   -- 13703
        retained_earnings_poy       REAL,   -- 13704
        equity_eoy                  REAL,   -- 13003
        equity_poy                  REAL,   -- 13004

        -- Обязательства
        lt_liabilities_eoy          REAL,   -- 14003
        lt_liabilities_poy          REAL,   -- 14004
        st_liabilities_eoy          REAL,   -- 15003
        st_liabilities_poy          REAL,   -- 15004
        balance_liab_eoy            REAL,   -- 17003
        balance_liab_poy            REAL,   -- 17004

        -- Отчет о фин. результатах
        revenue_cur                 REAL,   -- 21103
        revenue_prev                REAL,   -- 21104
        gross_profit_cur            REAL,   -- 21003
        gross_profit_prev           REAL,   -- 21004
        oper_profit_cur             REAL,   -- 22003
        oper_profit_prev            REAL,   -- 22004
        pbt_cur                     REAL,   -- 23003
        pbt_prev                    REAL,   -- 23004
        income_tax_cur              REAL,   -- 24103
        income_tax_prev             REAL,   -- 24104
        net_profit_cur              REAL,   -- 24003
        net_profit_prev             REAL    -- 24004

        -- FK
        , FOREIGN KEY (company_id) REFERENCES company(company_id)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_report_company_year
        ON report(company_id, year);
    """

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(ddl)
    conn.commit()
    conn.close()
    print(f"Database created and schema applied to '{db_path}'.")

if __name__ == "__main__":
    db_file = "finance.db"
    create_database(db_file)
