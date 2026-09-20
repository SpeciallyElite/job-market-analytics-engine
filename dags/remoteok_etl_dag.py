import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

DB_HOST = os.getenv('DB_HOST', 'de_postgres_container')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'de_database')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rootpassword')
DOCKER_NETWORK = os.getenv('DOCKER_NETWORK', 'etl_network')

default_args = {
    'owner': 'aarya',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='remoteok_etl_pipeline',
    default_args=default_args,
    description='Automated ETL Pipeline for RemoteOK Jobs',
    schedule_interval='0 8 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['etl', 'remoteok', 'postgres'],
) as dag:

    run_etl_task = DockerOperator(
        task_id='execute_etl_pipeline',
        image='de-etl_pipeline:latest',
        container_name='airflow_triggered_etl',
        api_version='auto',
        auto_remove=True,
        docker_url='unix://var/run/docker.sock',
        network_mode=DOCKER_NETWORK,
        mount_tmp_dir=False,
        environment={
        'DB_HOST': os.getenv('DB_HOST', 'de_postgres_container'),
        'DB_PORT': os.getenv('DB_PORT', '5432'),
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
    }
    )

    # run_etl_task