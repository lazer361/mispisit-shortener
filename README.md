# Shortener

Учебный сервис сокращения ссылок. Лабораторные работы по дисциплине «Методы и средства проектирования информационных систем и технологий».

Бездняков Александр, ИСТбд-42.

## Версии проекта

| Работа | Содержание | Ветка | Образ |
|---|---|---|---|
| 1 | Flask и стартовая страница | [lab1](https://github.com/lazer361/mispisit-shortener/tree/lab1) | `lazer361/mispisit-shortener:0.0.1` |
| 2 | Создание ссылок, список, карточка и отказ | [lab2](https://github.com/lazer361/mispisit-shortener/tree/lab2) | `lazer361/mispisit-shortener:0.0.2` |
| 3 | Постоянное хранение в PostgreSQL | [lab3](https://github.com/lazer361/mispisit-shortener/tree/lab3) | `lazer361/mispisit-shortener:0.0.3` |
| 4 | Оформление интерфейса с Bootstrap | [lab4](https://github.com/lazer361/mispisit-shortener/tree/lab4) | `lazer361/mispisit-shortener:0.0.4` |

Код и инструкции запуска каждой работы находятся в соответствующей ветке. Изменения оформлены отдельными [Pull Request](https://github.com/lazer361/mispisit-shortener/pulls) в основную ветку. Ветка main содержит указатель версий.

Образы доступны в [Docker Hub](https://hub.docker.com/r/lazer361/mispisit-shortener) для `linux/amd64` и `linux/arm64`.

## Запуск четвёртой версии

```sh
git clone -b lab4 https://github.com/lazer361/mispisit-shortener shortener
cd shortener
docker compose up -d
```

Открыть http://localhost:8080. Приложение и PostgreSQL запускаются из готовых образов. Данные хранятся в именованном томе `dbdata`. Инструкции предыдущих версий приведены в их ветках.
