FROM apache/superset:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER superset

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install clickhouse-sqlalchemy clickhouse-driver