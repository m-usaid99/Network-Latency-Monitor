# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional required packages
RUN apt-get update && apt-get install -y iputils-ping

# Make the monitor_ping.sh script executable
RUN chmod +x monitor_ping.sh

# Run monitor_ping.sh when the container launches
ENTRYPOINT ["./monitor_ping.sh"]

