FROM python:3.9-slim

WORKDIR /app

COPY app.py /app/app.py

RUN apt-get update && apt-get install -y docker.io && pip install flask

ENTRYPOINT ["python", "app.py"]
