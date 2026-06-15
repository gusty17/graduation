FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cloud_job.py .
COPY feature_engineering.py .

CMD ["python", "cloud_job.py"]
