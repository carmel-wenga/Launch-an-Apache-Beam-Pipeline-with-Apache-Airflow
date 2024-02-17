from datetime import datetime, timedelta
from airflow import DAG
from airflow.models import Variable
from airflow.providers.apache.beam.operators.beam import BeamRunPythonPipelineOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.models.connection import Connection

import pendulum
import os

paris_tz = pendulum.timezone('Europe/Paris')
default_args = {
    'owner': 'airflow',
    'start_date': datetime(year=2024, month=2, day=15, hour=5, minute=2, tzinfo=paris_tz),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

target_db_parameters = Connection.get_connection_from_secrets('target_db_id')


def check_file_exists(**kwargs):
    file_path = kwargs.get("file_path")
    if not os.path.exists(file_path):
        return FileNotFoundError(f"No such file or directory: {file_path}")


with DAG(dag_id='beam_pipeline_dag', default_args=default_args, schedule_interval='@once',
         description='A simple DAG to run a Beam pipeline that reads data from a csv file and load into a postgres '
                     'database'
         ) as dag:

    # Check if the source csv file exists. The source file path is defined by an airflow variable 'source_csv_file'
    # The value of this airflow variable is /opt/airflow/workers/beam/source/salary_data.csv
    check_file_existence = PythonOperator(
        task_id='check_if_the_source_file_exists',
        python_callable=check_file_exists,
        op_kwargs={'file_path': Variable.get('source_csv_file')}
    )

    # create the salary table into the target Postgres database if it doesn't exist. The table name is defined in the
    # 'sink_postgres_table' airflow variable
    create_salary_table = PostgresOperator(
        task_id='create_salary_table',
        postgres_conn_id='target_db_id',
        sql=f"""
            CREATE TABLE IF NOT EXISTS {Variable.get('sink_postgres_table')}(
                age INTEGER NOT NULL,
                gender VARCHAR(10) NOT NULL,
                education_level VARCHAR(50) NOT NULL,
                job_title VARCHAR(50) NOT NULL,
                year_of_experience FLOAT NOT NULL,
                salary FLOAT NOT NULL
            );
            """
    )

    # the location of the beam pipeline is defined by the 'beam_pipeline_py_file' airflow variable
    # beam_pipeline_py_file='/opt/airflow/workers/beam/pipeline.py'
    launch_apache_beam = BeamRunPythonPipelineOperator(
        task_id='launch_apache_beam',
        py_file=Variable.get('beam_pipeline_py_file'),
        runner="DirectRunner",
        py_options=[],
        pipeline_options={
            'source': Variable.get('source_csv_file'),
            'target_host': target_db_parameters.host,
            'target_port': target_db_parameters.port,
            'db_name': target_db_parameters.schema,
            'table_name': Variable.get('sink_postgres_table'),
            'username': target_db_parameters.login,
            'password': target_db_parameters.password
        },
        py_requirements=[
            'apache-beam==2.52.0',
            'beam-postgres-connector==0.1.3',
            'psycopg2-binary==2.9.9'
        ],
        py_interpreter='python3.8',
        py_system_site_packages=False
    )

    check_file_existence >> create_salary_table >> launch_apache_beam
