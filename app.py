from flask import Flask
from routes import SearchController, CompanyController

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Замените на ваш секретный ключ


@app.route("/", methods=["GET", "POST"])
def index():
    """Главная страница поиска"""
    return SearchController.index()


@app.route("/company/<inn>")
def company_details(inn):
    """Страница с детальной информацией о компании"""
    return CompanyController.company_details(inn)


@app.route("/analytics/<inn>")
def analytics(inn):
    """Страница с финансовой аналитикой компании"""
    return CompanyController.analytics(inn)


if __name__ == "__main__":
    app.run(debug=True)