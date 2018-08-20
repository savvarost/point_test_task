"""Модуль обработки запросов к апи"""
import datetime

from django.http.response import JsonResponse, HttpResponseBadRequest

from stock import models


def company(request):
    """Апи данных о компаниях

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)

    Returns:
        django.http.response.JsonResponse
    """
    return JsonResponse(
        {'companies': list(models.Company.objects.values('id', 'symbol', 'industry__id', 'industry__name'))}
    )


def stocks(request, symbol):
    """Апи для списка торгов компании

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol (str): Сокращенное название компании

    Returns:
        django.http.response.JsonResponse
    """
    stocks = list(models.Stock.get_by_symbol_and_date(
        symbol=symbol,
        field_values=[
            'date',
            'open',
            'high',
            'low',
            'close',
            'volume',
        ]
    ))
    return JsonResponse(
        {
            'symbol': symbol,
            'stocks': stocks,
        }
    )


def trades(request, symbol, insider=None):
    """Апи для полчения всех торгов а также совладельцев компании

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании
        insider(str): Наименование совладельца

    Returns:
        django.http.response.JsonResponse
    """
    trades = list(models.Trade.get_by_symbol_and_date(
        symbol=symbol,
        insider=insider,
        field_values=[
            'date',
            'last_price',
            'shares_traded',
            'shares_held',
            'type_transaction__name',
            'insider__name',
            'owner_type__name',
        ],
    ))

    return JsonResponse({
        'symbol': symbol,
        'trades': trades,
    })


def analytics(request, symbol):
    """Апи для получения данных аналитики по тенденции акций

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании

    Returns:
        django.http.response.JsonResponse
    """
    date_from = None
    date_to = None

    if date_from:
        try:
            date_from = datetime.datetime.strptime(date_from, '')
        except Exception:
            return HttpResponseBadRequest(
                'Не верно задана формат даты "date_from" - {}, используется формат 21-01-2018'.format(date_from))
    if date_to:
        try:
            date_to = datetime.datetime.strptime(date_to, '')
        except Exception:
            return HttpResponseBadRequest(
                'Не верно задана формат даты "date_to" - {}, используется формат 21-01-2018'.format(date_from))

    stocks = models.Stock.get_analytics_by_symbol_and_dates(
        symbol=symbol, date_from=date_from, date_to=date_to,
        field_values=[
            'date',
            'open',
            'open_r',
            'high',
            'high_r',
            'low',
            'low_r',
            'close',
            'close_r',
            'volume',
        ])
    return JsonResponse(
        {
            'symbol': symbol,
            'stocks': stocks,
        }
    )


def delta(request, symbol):
    """

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании

    Returns:
        django.http.response.JsonResponse
    """
    pass
