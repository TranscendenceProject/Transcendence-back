FROM python:3.12-alpine

WORKDIR /reminder

COPY ./reminder/* /reminder

RUN pip install -r requirements.txt 

CMD ["python", "manage.py", "runserver"]