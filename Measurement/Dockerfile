# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the script into the container
COPY driver.py /app/driver.py

# Install necessary dependencies
RUN pip install numpy

# Allow the command to be overridden at runtime
ENTRYPOINT ["python", "driver.py"]
