import os
import logging

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator, BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator


PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")

path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'trips_data_all')

DATASET = "tripdata"
COLOR_RANGE= {'yellow':['tpep_pickup_datetime',2019],'green':['lpep_pickup_datetime',2021]}
YEARS_TO_PROCESS = [2019,2021]
INPUT_PART = "raw"
INPUT_FILETYPE = "parquet"

default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="gcs_to_bq_dag",
    schedule_interval="@daily", 
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['dte-de']
) as dag:
    for color,ds_col in COLOR_RANGE.items():
        gcs_2_gcs_task = GCSToGCSOperator(
            task_id=f"move_{color}_{DATASET}_{ds_col[1]}_file_task",
            source_bucket=BUCKET,
            source_object=f"{INPUT_PART}/{color}_{DATASET}/{ds_col[1]}/*.{INPUT_FILETYPE}",
            destination_bucket=BUCKET,
            destination_object=f"{color}/",
            move_object=False
        )

        bigquery_external_table_task = BigQueryCreateExternalTableOperator(
            task_id=f"bq_{color}_{DATASET}_external_table_task",
            table_resource={
                "tableReference": {
                    "projectId": PROJECT_ID,
                    "datasetId": BIGQUERY_DATASET,
                    "tableId": f"external_{color}_{DATASET}",
                },
                "externalDataConfiguration": {
                    "autodetect": True,
                    "sourceFormat": f"{INPUT_FILETYPE.upper()}",
                    "sourceUris": [f"gs://{BUCKET}/{color}/*"]
                },
            },
        )

        CREATE_PART_TABLE_QUERY=f"CREATE OR REPLACE TABLE {BIGQUERY_DATASET}.{color}_{DATASET}_partitoned \
                    PARTITION BY   DATE({ds_col[0]}) AS \
                    SELECT * FROM {BIGQUERY_DATASET}.external_{color}_{DATASET};"

        bq_create_partitioned_table_job =BigQueryInsertJobOperator(
            task_id=f"bq_create_{color}_{DATASET}_partitioned_table_task",
            configuration={
                "query": {
                    "query": CREATE_PART_TABLE_QUERY,
                    "useLegacySql": False,
                }
            },
        )
        gcs_2_gcs_task >> bigquery_external_table_task >> bq_create_partitioned_table_job
        