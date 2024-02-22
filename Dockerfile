FROM python:3.12-slim-bullseye

RUN apt update && apt install -y libpq-dev redis libnss3-tools curl
RUN curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64" && \
    chmod +x mkcert-v*-linux-amd64 && \
    cp mkcert-v*-linux-amd64 /usr/local/bin/mkcert

ENV PYTHONUNBUFFERED=1

WORKDIR /reminder

COPY ./reminder/* /reminder

RUN mkcert -install
RUN mkcert -key-file key.pem -cert-file cert.pem localhost 127.0.0.1 ::1

RUN pip install psycopg2-binary
RUN pip install -r requirements.txt 

CMD ["bash", "-c", "redis-server --daemonize yes && python manage.py makemigrations && python manage.py migrate && daphne -e ssl:8000:privateKey=key.pem:certKey=cert.pem pikaPong.asgi:application"]
