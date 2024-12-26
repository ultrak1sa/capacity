from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta, date
from clickhouse_connect import get_client
import pandas as pd

CLICKHOUSE_HOST = "clickhouse-server"
SOURCE_TABLE = "kubernetes_gpu_logs"
RESULT_TABLE = "daily_computational_costs"

TEAM_MAPPING = {
    "NLP": "Natural Language Processing Team",
    "Poople": "People Analytics Team",
    "Antropuc": "Anthropocentric AI Team",
    "CrowdAI-RU": "Crowdsourcing Team Russia",
    "CrowdAI-EU": "Crowdsourcing Team Europe",
    "CrowdAI-US": "Crowdsourcing Team USA",
}

GPU_COSTS = {
    "NVIDIA V100": 3.0,
    "NVIDIA A100": 4.5,
    "NVIDIA RTX 3080": 2.0,
}

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

@task
def calculate_costs():
    client = get_client(host=CLICKHOUSE_HOST, username="default", password="")

    query = f"""
    SELECT 
        toDate(timestamp) AS day,
        tenant,
        gpu,
        COUNT(*) AS tasks,
        SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
        SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_tasks,
        AVG(gpu_utilization) AS avg_gpu_utilization,
        SUM(memory_usage_mb) AS total_memory_usage_mb
    FROM 
        {SOURCE_TABLE}
    GROUP BY 
        day, tenant, gpu
    ORDER BY 
        day ASC
    """
    data = client.query(query).result_rows
    columns = ["day", "tenant", "gpu", "tasks", "completed_tasks", "failed_tasks", "avg_gpu_utilization", "total_memory_usage_mb"]
    df = pd.DataFrame(data, columns=columns)

    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["team"] = df["tenant"].map(TEAM_MAPPING)
    df["gpu_cost_per_task"] = df["gpu"].map(GPU_COSTS)
    df["total_cost"] = df["gpu_cost_per_task"] * df["completed_tasks"]

    df = df[df["tasks"] > 0]

    start_date = df["day"].min()
    end_date = df["day"].max()
    all_days = pd.date_range(start=start_date, end=end_date, freq="D")
    index = pd.MultiIndex.from_product(
        [all_days, df["tenant"].unique(), df["gpu"].unique()],
        names=["day", "tenant", "gpu"]
    )
    df = df.set_index(["day", "tenant", "gpu"]).reindex(index).reset_index()

    df["tasks"] = df["tasks"].fillna(0).astype(int)
    df["completed_tasks"] = df["completed_tasks"].fillna(0).astype(int)
    df["failed_tasks"] = df["failed_tasks"].fillna(0).astype(int)
    df["avg_gpu_utilization"] = df["avg_gpu_utilization"].fillna(25.0)
    df["total_memory_usage_mb"] = df["total_memory_usage_mb"].fillna(0).astype(int)
    df["team"] = df["tenant"].map(TEAM_MAPPING).fillna("Unknown")
    df["gpu_cost_per_task"] = df["gpu"].map(GPU_COSTS).fillna(0.0)
    df["total_cost"] = (df["gpu_cost_per_task"] * df["completed_tasks"]).fillna(0.0)

    client.command(f"DROP TABLE IF EXISTS {RESULT_TABLE}")
    create_table_query = f"""
    CREATE TABLE {RESULT_TABLE} (
        day Date,
        tenant String,
        gpu String,
        tasks UInt32,
        completed_tasks UInt32,
        failed_tasks UInt32,
        avg_gpu_utilization Float32,
        total_memory_usage_mb UInt32,
        team String,
        gpu_cost_per_task Float32,
        total_cost Float32
    ) ENGINE = MergeTree()
    ORDER BY (day, tenant, gpu)
    """
    client.command(create_table_query)

    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
    client.insert(RESULT_TABLE, rows)
    print(f"Данные успешно загружены в таблицу {RESULT_TABLE}.")

with DAG(
    dag_id="calculate_daily_costs",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
) as dag:
    
    calculate_costs_task = calculate_costs()