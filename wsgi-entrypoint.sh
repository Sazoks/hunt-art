#!/bin/sh

# Переходим в папку проекта.
until cd /app/hunt_art/
do
    echo "Waiting for server volume..."
    sleep 2
done

# Запускаем миграции.
until poetry run python manage.py migrate
do
    echo "Waiting for db to be ready..."
    sleep 2
done

poetry run python manage.py createsuperuser --noinput

# Запускаем WSGI-сервер.
if [ $DJANGO_DEBUG = "True" ]
then 
    poetry run python manage.py runserver 0.0.0.0:8000
else
    poetry run gunicorn hunt_art.wsgi --bind 0.0.0.0:8000 --workers $WORKERS --threads $THREADS
fi
