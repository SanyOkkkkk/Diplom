# api_service.py
import requests
import json
from typing import Optional, Dict, Any


class DatanewtonAPI:
    def __init__(self, api_key: str = "ET05PwvL9kHa"):
        self.api_key = api_key
        self.base_url = "https://api.datanewton.ru"

    def get_counterparty(self, inn: str = None, ogrn: str = None, filters: list = None) -> Optional[Dict[Any, Any]]:
        """
        Получение общей информации о контрагенте из ЕГРЮЛ/ЕГРИП
        """
        url = f"{self.base_url}/v1/counterparty"

        params = {"key": self.api_key}

        if inn:
            params["inn"] = inn
        if ogrn:
            params["ogrn"] = ogrn
        if filters:
            params["filters"] = filters

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе информации о контрагенте: {e}")
            return None

    def get_finance(self, inn: str = None, ogrn: str = None) -> Optional[Dict[Any, Any]]:
        """
        Получение финансовых показателей и отчетности
        """
        url = f"{self.base_url}/v1/finance"

        params = {"key": self.api_key}

        if inn:
            params["inn"] = inn
        if ogrn:
            params["ogrn"] = ogrn

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе финансовой информации: {e}")
            return None


# Глобальный экземпляр API
api_client = DatanewtonAPI()