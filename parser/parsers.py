"""Модуль парсинга источника https://www.nasdaq.com"""
import re
import datetime

import bs4

# Регулярка поиска даты по формату 06/17/2017
_RE_DATE = re.compile('\d{2}/\d{2}/\d{4}')
# Регулярка поиска даты по формату 00:00
_RE_TIME = re.compile('\d{2}:\d{2}')


class UnknownFormat(Exception):
    """Неизвестный формат"""
    pass


class NotFoundData(Exception):
    """Не найден необходимые данные"""
    pass


def str2date(string):
    """
    Преобразование строки в дату

    Args:
        string(str): Строка с датой

    Returns:
        datetime.datetime
    """
    if not string:
        return None

    if _RE_DATE.search(string):
        return datetime.datetime.strptime(string, '%m/%d/%Y').date()
    elif _RE_TIME.search(string):
        return datetime.datetime.now().date()

    raise UnknownFormat('Неизвестный формат даты {}'.format(string))


def str2float(string):
    """
    Преобразование строки в float

    Args:
        string(str): Строка с числовым значением

    Returns:
        float
    """
    if not string:
        return None

    string = string.replace(',', '')
    return float(string)


class BaseParser:
    """Бызовый класс парсера"""

    def __init__(self, page):
        self._page = page
        self._page_bs = bs4.BeautifulSoup(page, 'html.parser')

    def get_data(self):
        """
        Главный метод парсинга

        Returns:
            dict
        """
        return {}


class ParserStock(BaseParser):
    """Парсер для страницы акций компании https://www.nasdaq.com/symbol/goog/historical"""

    def get_data(self):
        table_stock = self._page_bs.select_one('div#historicalContainer table')
        if not table_stock:
            raise NotFoundData('Не найдена таблица с акциями.')

        stocks = []
        for row in table_stock.select('tbody tr'):
            tds = [i.text.strip() for i in row.select('td')]
            if not any(tds):
                # Пустые строки пропускаем
                continue

            stocks.append({
                'date': str2date(tds[0]),
                'open': str2float(tds[1]),
                'high': str2float(tds[2]),
                'low': str2float(tds[3]),
                'close': str2float(tds[4]),
                'volume': str2float(tds[5]),
            })

        company_industry = None
        industry_bs = self._page_bs.find('b', text=re.compile('(?i)industry:'))
        if industry_bs:
            company_industry = industry_bs.find_next_sibling('a').text.strip()

        return {
            'stocks': stocks,
            'company_industry': company_industry,
        }


class ParserTrade(BaseParser):
    """Парсер для страницы торговли совледелцами комапнии https://www.nasdaq.com/symbol/cvx/insider-trades"""

    def get_data(self):
        table_trade = self._page_bs.select_one('div.genTable > table')
        if not table_trade:
            raise NotFoundData('Не найдена таблица с закупками.')

        trades = []
        for row in table_trade.select('tr'):
            tds = row.select('td')
            if not tds:
                continue

            insider_element, *tds = tds
            tds = [i.text.strip() for i in tds]
            if not any(tds):
                # Пустые строки пропускаем
                continue

            trades.append({
                'insider': {
                    'url': insider_element.find('a')['href'],
                    'name': insider_element.text.strip(),
                },
                'relation': tds[0],
                'date': str2date(tds[1]),
                'type_transaction': tds[2],
                'owner_type': tds[3],
                'shares_traded': str2float(tds[4]),
                'last_price': str2float(tds[5]),
                'shares_held': str2float(tds[6]),
            })

        company_industry = None
        industry_bs = self._page_bs.find('b', text=re.compile('(?i)industry:'))
        if industry_bs:
            company_industry = industry_bs.find_next_sibling('a').text.strip()

        next_page_url = None
        next_page_bs = self._page_bs.select_one('a#quotes_content_left_lb_NextPage')
        if next_page_bs:
            next_page_url = next_page_bs.get('href')

        return {
            'next_page_url': next_page_url,
            'trades': trades,
            'company_industry': company_industry,
        }
