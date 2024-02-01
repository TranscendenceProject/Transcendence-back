FROM python:3.12-slim-bullseye

RUN apt update && apt install -y libpq-dev redis
RUN redis-server --daemonize yes

ENV PYTHONUNBUFFERED=1

WORKDIR /reminder

COPY ./reminder/* /reminder

RUN pip install psycopg2-binary
RUN pip install -r requirements.txt 

CMD ["bash", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
