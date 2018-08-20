import requests

from parser.parsers import ParserStock, ParserTrade
from stock import models

_URL_STOCK = 'https://www.nasdaq.com/symbol/{}/historical'
_URL_TRADE = 'https://www.nasdaq.com/symbol/{}/insider-trades'


def load_stock(company_symbol):
    response = requests.get(_URL_STOCK.format(company_symbol))
    ps = ParserStock(response.text)
    d = ps.get_data()
    d.update({'company_symbol': company_symbol})
    models.Stock.store_stocks(d)


def load_stocks(company_symbols):
    load_stock('goog')
    pass


def load_trade(company_symbol):
    response = requests.get(_URL_TRADE.format(company_symbol))
    ps = ParserTrade(response.text)
    d = ps.get_data()
    d.update({'company_symbol': company_symbol})
    models.Trade.store_trades(d)


def load_trades():
    load_trade('goog')


import threading
from queue import Queue


class Treading(threading.Thread):

    def __init__(self, queue):
        """Инициализация потока"""
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        """Запуск потока"""
        while True:
            # Получаем url из очереди
            url = self.queue.get()

            # Скачиваем файл
            # self.download_file(url)

            # Отправляем сигнал о том, что задача завершена
            self.queue.task_done()

    # def download_file(self, task):
    #     """Скачиваем файл"""
    #     if task
    #         load_trade(symbol)


def read_symbol_company():
    """Загрузка информации о загружаемых данных компании

    Returns:
        list of str
    """
    with open('./tickets.txt', 'r') as file:
        text = file.read()
        symbols = text.strip()
        return [i for i in symbols if i]


def get_tasks():
    symbols = read_symbol_company()
    result = []
    for symbol in symbols:
        result.append({
            'type': 'stock',
            'url': _URL_STOCK.format(symbol),
        })

        for i in range(1,11):
            result.append({
                'type': 'trade',
                'url': _URL_TRADE.format(symbol),
            })



def start(count_tread=10):
    """
    Запускаем программу
    """
    queue = Queue()

    # Запускаем потом и очередь
    for i in range(5):
        t = Treading(queue)
        t.setDaemon(True)
        t.start()

    # for symbol in get_tasks():
    #     queue.put(url)

    # Ждем завершения работы очереди
    queue.join()
