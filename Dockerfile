FROM python:3.11.2

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
ADD ./requirements.txt ./
ADD ./poetry.lock ./pyproject.toml ./

RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.in-project true
RUN poetry install

ADD ./ ./

WORKDIR /app/hunt_art
RUN poetry run python manage.py collectstatic --noinput

WORKDIR /app

# git добавляет символы \r, что вызывает проблемы при исполнении скриптов.
# bash-скрипты могут не работать из-за символов '\r'. Удаляем их, записываем результат
# в новый файл и затем обратно переименовываем файл в исходное название.
RUN cat run-server.sh | tr -d '\r' >> run-server_tmp.sh
RUN rm run-server.sh
RUN mv run-server_tmp.sh run-server.sh
RUN chmod 755 run-server.sh
