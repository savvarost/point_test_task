"""monstock URL Configuration"""
from django.urls import path, re_path

from stock import api
from stock import views

urlpatterns = [
    path('', views.main),

    re_path('^api/$', api.company),
    re_path('^api/(?P<symbol>[^/]+)/$', api.stocks),
    re_path('^api/(?P<symbol>[^/]+)/insider/$', api.trades),
    re_path('^api/(?P<symbol>[^/]+)/analytics/$', api.analytics),
    re_path('^api/(?P<symbol>[^/]+)/insider/(?P<insider>[^/]+)/$', api.trades),

    re_path('^(?P<symbol>[^/]+)/$', views.stock_company),
    re_path('^(?P<symbol>[^/]+)/insider/$', views.trades_company),
    re_path('^(?P<symbol>[^/]+)/analytics/$', views.stock_company_analytics),
    re_path('^(?P<symbol>[^/]+)/insider/(?P<insider>[^/]+)/$', views.trades_company),
    re_path('^(?P<symbol>[^/]+)/delta/$', views.stock_company_delta),
]
