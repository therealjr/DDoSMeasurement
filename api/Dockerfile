FROM ubuntu:22.04

WORKDIR /app

COPY app.py /app/app.py

RUN apt-get update && apt-get install -y docker.io && pip install python3 flask sqlite3

ENTRYPOINT ["python", "app.py"]
