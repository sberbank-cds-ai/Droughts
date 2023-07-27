# Pull base image
FROM ubuntu:20.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app
RUN apt-get update && apt-get install -y python3 python3-pip
RUN apt -y install libxt6 libxrender1 libxext6 libgl1-mesa-glx libqt5widgets5 ffmpeg
RUN pip install -r requirements.txt
# Create folders
RUN mkdir -p data/raw data/preprocessed data/celled
# Install GDAL for preprocessing

# Copy project
COPY . /app/

