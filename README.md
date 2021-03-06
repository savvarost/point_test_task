Проект делится на 2 основных модуля:
* загрузки, парсинга и агрегации данных с источника (`./parser`)
* отображения инофрмации о проводимых акциях компаний

## Разворот и запуск django-проекта

Для разворота сервиса необзодимо выполнить следующие действия:

1. Установить необходимые пакеты для корректной работы приложений

```bash
$ pip3 install -r requirements.txt
```

2. Настроить подключение к БД в файле `monstock/settings.py` в соответствии с данными сервера БД в которой будут хранится данные приложения.

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'monstock',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

либо если к БД нет необходимости можно настроить запись в файл *.sqlite. (Установлен по умолчанию)

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'monstock',
    }
}
```

3. Запустить миграцию

```
python3 manage.py migrate
```

4. Запустить django-проект

```
python3 manage.py runserver 8000
```

5. Увидеть работу приложения можно в браузере по сслыке [`http://127.0.0.1:8000`][http://127.0.0.1:8000]

## Запуск загрузки данных с источника

Для запуска парсинга должны быть выполнены пункты 1-3 описанные в разделе выше.

Для загрузки, парсинга и сохранения данных на сервере необходимо выпонлнить команду
```
python3 manage.py runscan --symbol goog --count 10
```
где

параметр `--symbol`  (не обязательный параметр, по умолчанию проверяется файл `./tickers.txt`) загрузка информации о указанной компании

параметр `--count_threads` или `--count` (не обязательный параметр, по умолчанию значение 10) количество потоков