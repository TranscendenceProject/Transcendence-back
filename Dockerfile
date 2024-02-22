FROM python:3.12-slim-bullseye

RUN apt update && apt install -y libpq-dev redis

ENV PYTHONUNBUFFERED=1

WORKDIR /reminder

COPY ./reminder/* /reminder

RUN pip install psycopg2-binary
RUN pip install -r requirements.txt 

CMD ["bash", "-c", "redis-server --daemonize yes && python manage.py makemigrations && python manage.py migrate && daphne -e ssl:8000:privateKey=tls/cert.key.pem:certKey=tls/cert.pem pikaPong.asgi:application"]
