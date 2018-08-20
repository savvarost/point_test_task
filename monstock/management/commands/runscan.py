"""Описание команд"""
from django.core.management.base import BaseCommand

from parser.client import start


class LoadStocksAndTrades(BaseCommand):
    """Команда для загрузки акций и торгов источника https://www.nasdaq.com"""
    help = 'Команда для запуска загрузки акций и торгов источника https://www.nasdaq.com'

    def add_arguments(self, parser):
        """
        Добавление дополнительных параметров для команды

        Args:
            parser (argparse.ArgumentParser)
        """
        parser.add_argument(
            '--symbol',
            type=str,
            default=None,
            help='Загрузка по краткому наименование компании'
        )

        parser.add_argument(
            '--count_threads', '--count',
            type=int,
            default=10,
            help='Количество потоков'
        )

    def handle(self, *args, count_threads=10, symbol=None, **options):
        """Обработчик события

        Args:
            *args
            count_threads(int): Количество потоков
            symbol(str): Краткое название компании
            **options

        """
        start(count_tread=count_threads, symbol=symbol)
