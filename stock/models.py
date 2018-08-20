"""Модуль описания сущностей БД и их методов"""
import collections
import datetime

from django.db import models, connection


class BaseModels(models.Model):
    """Базовый класс модели"""

    # Колонки по которым идет сопоставление
    _COLS_TO_MATCH = NotImplemented

    @classmethod
    def get_with_save(cls, **kwargs):
        """
        Найти в БД запись по заданным полям в случае если ее нету добавить

        Returns:
            cls
        """
        filters = {
            i: kwargs[i] for i in cls._COLS_TO_MATCH
            if i in kwargs
        }

        query = cls.objects
        if filters:
            query = query.filter(**filters)

        ind = list(query[0:1])
        if ind:
            ind = ind[0]
        else:
            ind = cls(**kwargs)
            ind.save()

        return ind

    class Meta:
        abstract = True


class TypeTransaction(BaseModels):
    """Тип транзакций (справочник)"""
    _COLS_TO_MATCH = ['name']

    # Наименование
    name = models.CharField(max_length=255, null=False, db_index=True, unique=True)


class Industry(BaseModels):
    """Промышленность (справочник)"""
    _COLS_TO_MATCH = ['name']

    # Наименование
    name = models.CharField(max_length=255, null=False, db_index=True, unique=True)


class TypeOwner(BaseModels):
    """Тип владельца (справочник)"""
    _COLS_TO_MATCH = ['name']

    # Наименование
    name = models.CharField(max_length=255, null=False, db_index=True, unique=True)


class Relation(BaseModels):
    """Отношение к компании (справочник)"""
    _COLS_TO_MATCH = ['name']

    # наименование
    name = models.CharField(max_length=255, null=False, unique=True, db_index=True)


class Company(BaseModels):
    """Компании"""
    _COLS_TO_MATCH = ['symbol']

    # Аббревиатура
    symbol = models.CharField(max_length=255, null=False, db_index=True, unique=True)
    # Промышленность
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)


class Stock(BaseModels):
    """Акция"""
    _COLS_TO_MATCH = ['company', 'date']

    # Разрешенные колонки для метода get_delta
    _ACCESS_COL_DELTA = ['open', 'high', 'low', 'close']

    # Дата проведение акции
    date = models.DateField(null=False)
    # Цена открытия аукциона
    open = models.FloatField()
    # "High" is the highest sales price the stock has achieved during the regular trading hours, the intra-day high.
    high = models.FloatField()
    # "Low" is the lowest sales price the stock has fallen to during the regular trading hours, the intra-day low.
    low = models.FloatField()
    # "Close" is the period at the end of the trading session. Sometimes used to refer to closing price.
    close = models.FloatField()
    # "Volume" The closing daily official volumes represented graphically for each trading day.
    volume = models.IntegerField()
    # Компания
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)

    class Meta:
        # Уникальность записей по компании и дате,
        # то есть в один и тотже datetime не может быть более 1 записи у одной компании
        unique_together = (('company', 'date'),)
        index_together = (('company', 'date'),)

    @staticmethod
    def store_stocks(data):
        """
        Сохранение списка акций

        Args:
            data (dict): данные о акциях
                {
                    'company_industry': str
                    'company_symbol': str,
                    'stocks': list,
                }
        """
        ind = Industry.get_with_save(name=data.get('company_industry'))
        comp = Company.get_with_save(
            symbol=data.get('company_symbol'),
            industry=ind
        )

        for stock_date in data['stocks']:
            kw = {}
            stock = Stock(
                company=comp,
                **stock_date
            )

            # Ищем в БД акции по компании и дате, если получается найти то будем делать обновление
            st_s = list(Stock.objects.filter(company=comp, date=stock_date.get('date')).values_list('id')[0:1])
            if st_s:
                kw['force_update'] = True
                stock.id = st_s[0][0]

            stock.save(**kw)

    @classmethod
    def get_by_symbol_and_date(cls, symbol, date_from=None, date_to=None, field_values=None):
        """
        Получение акции по промежуток премени компании

        Args:
            symbol(str): Идентификатор компании
            date_from(datetime.datetime): Дата от (по умолчанию - 3 месяца от текущего дня)
            date_to(datetime.datetime): Дата по (по умолчанию сегодняшний день)
            field_values(list): Поля для формирования результата

        Returns:
            list of Stock
        """
        date_to = date_to or datetime.datetime.now()
        date_from = date_from or date_to - datetime.timedelta(days=30 * 3)

        query = Stock.objects.filter(
            company__symbol=symbol,
            date__gte=date_from,
            date__lte=date_to
        ).order_by('-date')

        if field_values:
            query = query.values(*field_values)

        return list(query.all())

    @classmethod
    def get_analytics_by_symbol_and_dates(cls, symbol, date_from=None, date_to=None, field_values=None):
        """Получение списка акций с аналитикой

        Args:
            symbol(str): Идентификатор компании
            date_from(datetime.datetime): Дата от (по умолчанию - 3 месяца от текущего дня)
            date_to(datetime.datetime): Дата по (по умолчанию сегодняшний день)
            field_values(list): Поля для формирования результата

        Returns:
            list
        """

        date_to = date_to or datetime.datetime.now()
        date_from = date_from or date_to - datetime.timedelta(days=90)

        query_raw = """SELECT
  s.*,
  100 - 100*lag("open") OVER "w" / "open" AS "open_r",
  100 - 100*lag("high") OVER "w" / "high" AS "high_r",
  100 - 100*lag("low") OVER "w" / "low" AS "low_r",
  100 - 100*lag("close") OVER "w" / "close" AS "close_r",
  100 - 100*lag("volume") OVER "w"::FLOAT / "volume"::FLOAT AS "valume_r"
FROM "stock_stock" s
  LEFT JOIN "stock_company" c on s."company_id" = c."id"
WHERE c."symbol" = %s
  AND s."date" >= %s
  AND s."date" <= %s
  WINDOW "w" AS (ORDER BY "date")
ORDER BY "date" DESC;"""

        rows = list(Stock.objects.raw(query_raw, (symbol, date_from, date_to)))

        if field_values:
            rows = [
                {
                    field_value: getattr(i, field_value, None)
                    for field_value in field_values
                }
                for i in rows
            ]

        return rows

    @classmethod
    def get_delta(cls, symbol, column_type, max_change_price):
        """

        Args:
            symbol(str): Сокращенное название компании
            column_type(str): Тип колонки
            max_change_price(float): Изменение цены акций

        Returns:
            dict
        """
        if column_type not in cls._ACCESS_COL_DELTA:
            raise Exception(
                'Указанный тип {} отсутствует в списке разрешенных {}'.format(column_type, cls._ACCESS_COL_DELTA))

        query_raw = """SELECT
  a."date",
  abs(a."{column_type}_r") as open_abs
FROM (
       SELECT
         *,
         lag("{column_type}") OVER "w" - "{column_type}" AS "{column_type}_r"
       FROM "stock_stock" s LEFT JOIN stock_company c on s.company_id = c.id
       WHERE c."symbol" = %s
       WINDOW "w" AS (ORDER BY "date" )
     ) as a""".format(column_type=column_type)

        with connection.cursor() as cursor:
            cursor.execute(query_raw, (symbol,))
            rows = cursor.fetchall()

        store_date = None
        curr_counter = 0
        result = collections.defaultdict(list)
        for date, value in rows:
            if store_date is None:
                store_date = date

            if value:
                curr_counter += value

            if curr_counter > max_change_price:
                delta = date - store_date
                result[delta].append({
                    'date_from': store_date,
                    'date_to': date,
                    'value': curr_counter,
                })

                store_date = None
                curr_counter = 0

        return result


class Insider(BaseModels):
    """Совладелец"""
    _COLS_TO_MATCH = ['name', 'url']

    # Наимаенование
    name = models.CharField(max_length=255, null=False, unique=True, db_index=True)
    # Ссылка на страницу совладельца
    url = models.CharField(max_length=255, null=False, unique=True, db_index=True)


class Insider2Company(BaseModels):
    """
    Связующая таблица совладельца и компании
    у совладелец может быть в нескольких компаниях
    """
    _COLS_TO_MATCH = ['company', 'insider']

    # Компания
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)
    # Совладелец
    insider = models.ForeignKey(Insider, on_delete=models.CASCADE, null=False)
    # Связь с компанией
    relation = models.ForeignKey(Relation, on_delete=models.CASCADE)

    class Meta:
        # Уникальность записей по компании и совладельцу
        unique_together = (('company', 'insider'),)
        index_together = (('company', 'insider'),)


class Trade(BaseModels):
    """Сделки/торги"""

    # Дата сделки
    date = models.DateField(null=False)
    # последняя цена
    last_price = models.FloatField()
    #
    shares_traded = models.IntegerField()
    #
    shares_held = models.IntegerField()
    # Тип транзакции
    type_transaction = models.ForeignKey(TypeTransaction, on_delete=models.CASCADE)
    # Совладелец
    insider = models.ForeignKey(Insider, on_delete=models.CASCADE, null=False)
    # Компания
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)
    # Тип владельца
    owner_type = models.ForeignKey(TypeOwner, on_delete=models.CASCADE)

    class Meta:
        # Уникальность записей по компании и дате,
        # unique_together = (('company', 'date'),)
        index_together = (('company', 'date'),)

    @staticmethod
    def store_trades(data):
        """
        Сохранение списка торгов совладельцев компании

        Args:
            data (dict): данные о акциях
                {
                    'company_industry': str
                    'company_symbol': str,
                    'trades': list,
                }
        """
        ind = Industry.get_with_save(name=data.get('company_industry'))
        comp = Company.get_with_save(
            symbol=data.get('company_symbol'),
            industry=ind
        )

        for trade_data in data['trades']:
            insider_dict = trade_data.pop('insider')
            insider = Insider.get_with_save(**insider_dict)

            relation_str = trade_data.pop('relation')
            relation = Relation.get_with_save(name=relation_str)

            owner_type_str = trade_data.pop('owner_type')
            owner_type = TypeOwner.get_with_save(name=owner_type_str)

            type_transaction_str = trade_data.pop('type_transaction')
            type_transaction = TypeTransaction.get_with_save(name=type_transaction_str)

            Insider2Company.get_with_save(
                insider=insider,
                company=comp,
                relation=relation
            )

            trade = Trade(
                company=comp,
                insider=insider,
                owner_type=owner_type,
                type_transaction=type_transaction,
                **trade_data
            )

            # Ищем в БД торги
            kw = {}
            st_s = list(Trade.objects.filter(
                company=comp,
                date=trade_data.get('date'),
                type_transaction=type_transaction,
                owner_type=owner_type,
                insider=insider
            ).values_list('id')[0:1])
            if st_s:
                kw['force_update'] = True
                trade.id = st_s[0][0]

            trade.save(**kw)

    @classmethod
    def get_by_symbol_and_date(cls, symbol, insider=None, date_from=None, date_to=None, field_values=None):
        """
        Получение акции по промежуток премени компании

        Args:
           symbol(str): Идентификатор компании
           insider(str): Имя совладелеца
           date_from(datetime.datetime): Дата от (по умолчанию - не задан)
           date_to(datetime.datetime): Дата по (по умолчанию - не задан)
           field_values(list): Поля для формирования результата

        Returns:
           list of Trade
        """
        query = Trade.objects.filter(company__symbol=symbol)
        if insider:
            query = query.filter(insider__name=insider)
        if date_to:
            query = query.filter(date__lte=date_to)
        if date_from:
            query = query.filter(date__gte=date_from)

        if field_values:
            query = query.values(*field_values)

        return list(query.order_by('-date').all())
