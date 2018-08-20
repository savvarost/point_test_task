from django.core.management.base import BaseCommand

from parser.client import load_stock, load_trade


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        load_stock('goog')
        load_trade('goog')
        print()
        pass

