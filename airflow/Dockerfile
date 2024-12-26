FROM apache/airflow:2.5.1-python3.8

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential

USER airflow

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
