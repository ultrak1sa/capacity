from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import os
import json
import random

LOGS_DIR = "/opt/airflow/dags/data"
OUTPUT_LOG_FILE = os.path.join(LOGS_DIR, "synthetic_platform_logs.json")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

@task
def generate_logs():
    tenants = ['NLP', 'Poople', 'Antropuc', 'CrowdAI-RU', 'CrowdAI-EU', 'CrowdAI-US']
    gpus = ['NVIDIA V100', 'NVIDIA A100', 'NVIDIA H100', 'NVIDIA B100', 'NVIDIA RTX 3080']
    task_types = ['pre-training', 'inference']
    models = ['ResNet50', 'BERT', 'GPT-3', 'GPT-2', 'BERT-Large', 'BERT-XL', 'GPT-J', 'GPT-Neo', 'GPT-J-6B']
    log_levels = ['INFO', 'ERROR']
    services = ['ml_platform', 'gpu_manager']
    statuses = ['Pending', 'Completed', 'Failed']
    namespaces = ['default', 'ml-tasks', 'gpu-computations']

    status_weights = [0.8, 0.1, 0.1]
    level_weights = [0.9, 0.1]

    os.makedirs(LOGS_DIR, exist_ok=True)

    end_time = datetime.now()
    start_time = end_time - timedelta(days=730)

    num_logs = 1_000_000
    logs = []

    for _ in range(num_logs):
        timestamp = start_time + timedelta(
            seconds=random.randint(0, int((end_time - start_time).total_seconds()))
        )
        log = {
            "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "level": random.choices(log_levels, weights=level_weights, k=1)[0],
            "service": random.choice(services),
            "tenant": random.choice(tenants),
            "gpu": random.choice(gpus),
            "task_type": random.choice(task_types),
            "model": random.choice(models),
            "status": random.choices(statuses, weights=status_weights, k=1)[0],
            "message": f"Task {random.choices(statuses, weights=status_weights, k=1)[0]} at {timestamp.strftime('%H:%M:%S')}",
            "gpu_utilization": f"{random.uniform(10, 100):.2f}%",
            "memory_usage_mb": random.randint(100, 32000)
        }
        logs.append(log)

    with open(OUTPUT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

# Определяем DAG
with DAG(
        dag_id="generate_logs_dag",
        default_args=default_args,
        schedule_interval="@daily",
        start_date=days_ago(1),
        catchup=False,
) as dag:
    generate_logs_task = generate_logs()




