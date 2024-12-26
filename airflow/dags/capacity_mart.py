from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import os
import json
from clickhouse_connect import get_client


LOGS_DIR = "/opt/airflow/dags/data"
LOG_FILE = os.path.join(LOGS_DIR, "synthetic_platform_logs.json")
CLICKHOUSE_HOST = 'clickhouse-server'
CLICKHOUSE_TABLE = 'kubernetes_gpu_logs'

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

@task
def process_logs():
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, "r") as f:
        logs = []
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line: {line}. Error: {e}")

    client = get_client(host=CLICKHOUSE_HOST, username="default", password="")
    
    client.command(f"DROP TABLE IF EXISTS {CLICKHOUSE_TABLE}")
    create_table_query = f"""
    
    CREATE TABLE {CLICKHOUSE_TABLE} (
        timestamp DateTime,
        level String,
        service String,
        tenant String,
        gpu String,
        task_type String,
        model String,
        status String,
        gpu_utilization Float32,
        memory_usage_mb UInt32,
        message String
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """
    client.command(create_table_query)
    
    data = [
        (
            datetime.strptime(log["timestamp"], '%Y-%m-%dT%H:%M:%SZ'),
            log["level"],
            log["service"],
            log["tenant"],
            log["gpu"],
            log["task_type"],
            log["model"],
            log["status"],
            float(log["gpu_utilization"].strip('%')),
            log["memory_usage_mb"],
            log["message"]
        )
        for log in logs
    ]

    client.insert(
        table=CLICKHOUSE_TABLE,
        data=data,
        column_names=[
            "timestamp", "level", "service", "tenant", "gpu",
            "task_type", "model", "status", "gpu_utilization", "memory_usage_mb", "message"
        ]
    )


with DAG(
    dag_id="process_logs_to_clickhouse",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
) as dag:

    process_logs_task = process_logs()