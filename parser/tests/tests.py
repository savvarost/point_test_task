"""Модуль тестирования парсинга и сохранения данных"""
import os

from django.test import TestCase

from parser import parsers
from stock import models

_THIS_PATH = os.path.dirname(os.path.abspath(__file__))


class TestParser(TestCase):

    def test_stock_raise_not_found_data(self):
        """Проверка отработки исключения отсутствия данных на странице"""
        with open(os.path.join(_THIS_PATH, 'files_example/stock_no_table.html'), 'r') as file:
            ps = parsers.ParserStock(file.read())
            with self.assertRaises(parsers.NotFoundData):
                ps.get_data()

    def test_stock(self):
        """Проверка загрузки и сохранения акций"""

        with open(os.path.join(_THIS_PATH, 'files_example/stock.html'), 'r') as file:
            ps = parsers.ParserStock(file.read())
            d = ps.get_data()
            d.update({'company_symbol': 'goog'})
            models.Stock.store_stocks(d)

            self.assertEqual(len(d['stocks']), models.Stock.objects.count())

    def test_trade(self):
        """Проверка загрузки и сохранения торгов"""

        with open(os.path.join(_THIS_PATH, 'files_example/trade.html'), 'r') as file:
            ps = parsers.ParserTrade(file.read())
            d = ps.get_data()
            d.update({'company_symbol': 'goog'})
            models.Trade.store_trades(d)

            self.assertEqual(len(d['trades']), models.Trade.objects.count())
