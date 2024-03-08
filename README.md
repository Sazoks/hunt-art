# hunt-art

## Запуск
Что нужно для запуска:
1. Docker
2. Docker-Compose

Запуск состоит из 3-х пунктов:
1. Настройка переменных окружения
2. Сборка Docker-образа
3. Запуск

### Шаг 1 - Настройка переменных окружения
1. В корневой папке проекта лежит файл `.env-defaults`.
2. Создать в этой же папке файл с именем `.env`.
3. Скопировать содержимое `.env-defaults` в `.env`.

### Шаг 2 - Сборка Docker-образа
1. Открыть консоль в корневой папке проекта.
2. Ввести команду `docker-compose build --no-cache`

### Шаг 3 - Запуск
1. Открыть консоль в корневой папке проекта.
2. Ввести команду `docker-compose --env-file .env up`

> Чтобы остановить работу проекта, можно нажать `ctrl + c` комбинацию в консоле, где была выполнена вышеприведенная команда.

## Админка
|Логин|Пароль|Ссылка|
|-|-|-|
|admin|admin|http://localhost:8000/admin|
