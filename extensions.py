import requests
import json
from config import API_KEY, DATA_TICKER

class APIException(Exception):
    pass


class Converter:
    @staticmethod
    def get_price(base, quote, amount):
        try:
            base_ticker = DATA_TICKER[base]
        except KeyError:
            raise APIException(f'Валюта {base} не найдена!\nСписок доступных валют см. /values')
        try:
            quote_ticker = DATA_TICKER[quote]
        except KeyError:
            raise APIException(f'Валюта {quote} не найдена!\nСписок доступных валют см. /values')
        if base_ticker == quote_ticker:
            raise APIException(f'Невозможно перевести одинаковые валюты {base}')
        try:
            amount = float(amount.replace(',', '.'))
        except ValueError:
            raise APIException(f'Неудалось обработать количество: {amount}')

        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{base_ticker}/{quote_ticker}/{amount}"
        r = requests.get(url)
        resp = json.loads(r.content)
        result = float(resp['conversion_result'])
        return result

