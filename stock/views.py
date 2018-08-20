"""Модуль обработки запросов на получение страниц"""
from django.http.response import HttpResponseBadRequest
from django.shortcuts import render

from stock import models


def main(request):
    """Главная страница, список компаний

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)

    Returns:
        django.http.response.HttpResponseBase
    """
    return render(request, 'main.html', {'companies': models.Company.objects.all()})


def stock_company(request, symbol):
    """Акции компании

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании

    Returns:
        django.http.response.HttpResponseBase
    """
    content = {
        'symbol': symbol,
        'stocks': models.Stock.get_by_symbol_and_date(symbol=symbol)
    }
    return render(request, 'stocks.html', content)


def trades_company(request, symbol=None, insider=None):
    """Торги компании

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании
        insider(str): имя совладельца

    Returns:
        django.http.response.HttpResponseBase
    """
    content = {
        'symbol': symbol,
        'is_trades': request.path.endswith('insider/'),
        'trades': models.Trade.get_by_symbol_and_date(symbol=symbol, insider=insider)
    }
    return render(request, 'trades.html', content)


def stock_company_analytics(request, symbol=None):
    """Получения данных аналитики по тенденции акций

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании

    Returns:
        django.http.response.HttpResponseBase
    """
    content = {
        'symbol': symbol,
        'stocks': models.Stock.get_analytics_by_symbol_and_dates(symbol=symbol)
    }
    return render(request, 'stocks_analytics.html', content)


def stock_company_delta(request, symbol=None):
    """Сформировать страницу с разностью

    Args:
        request(django.core.handlers.wsgi.WSGIRequest)
        symbol(str): Сокращенное название компании

    Returns:
        django.http.response.HttpResponseBase
    """
    try:
        max_change_price = float(request.GET.get('value'))
        column_type = request.GET.get('type')

        deltas = models.Stock.get_delta(
            symbol=symbol, column_type=column_type, max_change_price=max_change_price)
    except Exception as ex:
        # todo переделать, сделал на скорую руку
        return HttpResponseBadRequest(ex)

    sort_delta_key = list(deltas.keys())
    sort_delta_key.sort()

    content = {
        'symbol': symbol,
        'stocks_delta': [
            (i, j['date_from'], j['date_to'], j['value'])
            for i in sort_delta_key
            for j in deltas[i]
        ]
    }
    return render(request, 'stocks_delta.html', content)
