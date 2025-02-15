FROM python:3.9-slim

WORKDIR /app

COPY app.py /app/app.py

RUN pip install flask sqlite3

ENTRYPOINT ["python", "app.py"]
