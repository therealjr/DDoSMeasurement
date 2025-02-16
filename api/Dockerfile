FROM ubuntu:22.04

WORKDIR /app

# Install required packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip sqlite3 docker.io && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install flask

# Copy the application
COPY app.py /app/app.py

# Set the entrypoint
ENTRYPOINT ["python3", "/app/app.py"]
