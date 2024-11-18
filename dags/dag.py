#dag - directed acyclic graph
#task: 1) fetch data 2) clean 3) create and store
#operators: PythonOperator and PostgresOperator
#hooks - allow conn from aitflow to external databases
#dependencies : 

from datetime import datetime, timedelta
from airflow import DAG

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fetch_movie_data',
    default_args=default_args,
    description='A simple movie data fetching DAG',
    schedule_interval=timedelta(days=1),
)