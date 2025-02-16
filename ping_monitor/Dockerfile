# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the script into the container
COPY driver.py /app/driver.py

# Install required dependencies, including 'ping'
RUN apt-get update && apt-get install -y iputils-ping sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install necessary dependencies
RUN pip install numpy pysqlite3 

# Allow the command to be overridden at runtime
ENTRYPOINT ["python", "driver.py"]
