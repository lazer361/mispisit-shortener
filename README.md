# Shortener

Лабораторная работа №1 по дисциплине «Методы и средства проектирования информационных систем и технологий».

Бездняков Александр, ИСТбд-42.

Shortener предназначен для создания коротких ссылок, получения QR-кодов и просмотра статистики переходов. В версии 0.0.1 реализована стартовая страница. Серверная часть использует Flask, страницы формируются шаблонизатором Jinja2.

## Запуск

```text
Репозиторий: https://github.com/lazer361/mispisit-shortener
Pull Request: https://github.com/lazer361/mispisit-shortener/pull/1
Образ: https://hub.docker.com/r/lazer361/mispisit-shortener

docker pull lazer361/mispisit-shortener:0.0.1
docker run --rm -p 8080:8080 lazer361/mispisit-shortener:0.0.1
```

Открыть http://localhost:8080.

## Локальная сборка

```sh
docker build -t shortener:0.0.1 .
docker run --rm -p 8080:8080 shortener:0.0.1
```

## Состав проекта

- `app.py` - маршрут главной страницы.
- `templates/index.html` - шаблон страницы.
- `requirements.txt` - версии пакетов.
- `Dockerfile` - описание сборки и запуска контейнера.

Python 3.12.12, Flask 3.1.3, Gunicorn 23.0.0. Контейнер слушает порт 8080.
