FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y tesseract-ocr

WORKDIR /app

RUN pip install -r requirements.txt

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

CMD ["python", "main.py"]
