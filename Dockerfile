FROM python:3.12-slim-bullseye

RUN apt update && apt install -y libpq-dev

ENV PYTHONUNBUFFERED=1

WORKDIR /reminder

COPY ./reminder/* /reminder

RUN pip install psycopg2-binary
RUN pip install -r requirements.txt 

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]