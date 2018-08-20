"""Модуль загрузки данных и сохранения данных"""
import os
import re
import threading
from functools import wraps
from queue import Queue

import requests

from parser import parsers
from stock import models

# Шаблон ссылки до акции компаниц
_URL_STOCK = 'https://www.nasdaq.com/symbol/{}/historical'
# Шаблон ссылки до торгов компании
_URL_TRADE = 'https://www.nasdaq.com/symbol/{}/insider-trades'
# Путь до корня проекта
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def retry(count=5):
    """Повторное выполнение метода при исключении NotFoundData

    Args:
        count(int): Количество попыток

    Returns:
        function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(count):
                try:
                    func(*args, **kwargs)
                except parsers.NotFoundData:
                    continue

                break

        return wrapper

    return decorator


class Worker(threading.Thread):
    """Многопоточный класс работы с очередью"""

    def __init__(self, tasks):
        """
        Args:
            tasks(Queue): Очередь задач
        """
        threading.Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            kwargs = self.tasks.get()
            try:
                self._run_task(**kwargs)
            except Exception as ex:
                # An exception happened in this thread
                print(ex)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()

    @retry(count=5)
    def _run_task(self, task_type, **kwargs):
        print(self.name, kwargs)
        if task_type == 'stock':
            self._stock(**kwargs)
        elif task_type == 'trade':
            self._trade(**kwargs)
        else:
            raise Exception('Тип не определен')

    def _trade(self, symbol, url):
        """Загрузка, парсинг и сохранение торгов

        Args:
            symbol(str): Сокращенное название компании
            url(str): Ссылка на источник
        """
        response = requests.get(url)
        parser = parsers.ParserTrade(response.text)
        data = parser.get_data()
        # Если есть следующая страница ставим ее в очередь
        next_url = data.pop('next_page_url')
        if next_url:
            page_number = int(re.search('(\d+)$', next_url).group(1))
            if page_number < 11:
                self.tasks.put({
                    'task_type': 'trade',
                    'symbol': symbol,
                    'url': next_url,
                })
        data.update({'company_symbol': symbol})
        models.Trade.store_trades(data)

    def _stock(self, symbol, url):
        """Загрузка, парсинг и сохранение акций

        Args:
            symbol(str): Сокращенное название компании
            url(str): Ссылка на источник
        """
        response = requests.get(url)
        parser = parsers.ParserStock(response.text)
        data = parser.get_data()
        data.update({'company_symbol': symbol})
        models.Stock.store_stocks(data)


class ThreadPool:
    """ Пул потоков для выполнения задач из очереди"""

    def __init__(self, num_threads):
        self.tasks = Queue()
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, **kwargs):
        """Добавить задачу в очередь"""
        self.tasks.put(kwargs)

    def add_tasks(self, tasks):
        """Добавить список задач в очередь"""
        for task in tasks:
            self.add_task(**task)

    def wait_completion(self):
        """Дождаться завершения всех задач в очереди"""
        self.tasks.join()


def read_symbol_company():
    """Загрузка информации о загружаемых данных компании

    Returns:
        list of str
    """
    with open(os.path.join(_ROOT_DIR, 'tickers.txt'), 'r') as file:
        text = file.read()
        symbols = text.split()
        return [i for i in symbols if i]


def get_tasks(symbol=None):
    """Генерируем скисок задач, на выполнение

    Args:
        symbol(str): Сокращенное название компании

    Returns:
        list of dict
    """
    if symbol:
        symbols = [symbol]
    else:
        symbols = read_symbol_company()
    result = []
    for symbol_ in symbols:
        result.append({
            'task_type': 'stock',
            'symbol': symbol_,
            'url': _URL_STOCK.format(symbol_),
        })

        result.append({
            'task_type': 'trade',
            'symbol': symbol_,
            'url': _URL_TRADE.format(symbol_),
        })

    return result


def start(count_tread=10, symbol=None):
    """Основной метод запуска загрузки данных в многопоточном режиме

    Args:
        count_tread(int): Количество потоков
        symbol(str): Количество потоков
    """
    thread_pool = ThreadPool(count_tread)
    thread_pool.add_tasks(get_tasks(symbol))
    thread_pool.wait_completion()
