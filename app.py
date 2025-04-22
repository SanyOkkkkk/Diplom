from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
DB_PATH = 'finance.db'


def search_company_by_name(search_term):
    search_term = search_term.upper()
    print(search_term)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT name, okved_o, inn, kod_re
        FROM company
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 50
    """, (f'%{search_term}%',))

    results = cur.fetchall()
    print(results)
    conn.close()
    return results





@app.route("/", methods=["GET", "POST"])
def index():
    companies = []
    query = ""
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            companies = search_company_by_name(query)
    return render_template("search.html", companies=companies, query=query)


if __name__ == "__main__":
    app.run(debug=True)
