from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.beam.operators.beam import BeamRunPythonPipelineOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.hooks.base_hook import BaseHook

default_args = {
    'owner': 'airflow',
    'start_date': datetime(year=2024, month=1, day=23, hour=22, minute=15),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

target_db_parameters = BaseHook.get_connection('target_db_id')

with DAG(dag_id='beam_pipeline_dag', default_args=default_args, schedule_interval='@once',
    description='A simple DAG to run a Beam pipeline that reads data from a csv file and load into a postgres database'
) as dag:

    # Task to create the salary table into the target PostgreSQL database
    create_salary_table = PostgresOperator(
        task_id='create_salary_table',
        postgres_conn_id='target_db_id',
        sql="""
            CREATE TABLE IF NOT EXISTS salaries(
                age INTEGER NOT NULL,
                gender VARCHAR(10) NOT NULL,
                education_level VARCHAR(50) NOT NULL,
                job_title VARCHAR(50) NOT NULL,
                year_of_experience FLOAT NOT NULL,
                salary FLOAT NOT NULL
            );
            """
    )

    launch_apache_beam = BeamRunPythonPipelineOperator(
        task_id='launch_apache_beam',
        py_file='/opt/airflow/workers/beam/pipeline.py',
        py_options=[],
        pipeline_options={
            'source': '/opt/airflow/workers/beam/source/salary_data.csv',
            'target_host': target_db_parameters.host,
            'target_port': target_db_parameters.port,
            'db_name': target_db_parameters.schema,
            'table_name': 'salaries',
            'username': target_db_parameters.login,
            'password': target_db_parameters.password
        },
        py_requirements=[
            'apache-beam==2.52.0',
            'beam-postgres-connector==0.1.3',
            'psycopg2-binary==2.9.9'
        ],
        py_interpreter='python3',
        py_system_site_packages=False
    )

    create_salary_table >> launch_apache_beam