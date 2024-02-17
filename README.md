The goal of this simple project is to launch or schedule an apache beam pipeline with apache airflow launched with 
docker and docker-compose.

The beam pipeline read csv data and load the data into a postgres database. 
The beam pipeline used here is the one defined in 
[this repository](https://github.com/carmel-wenga/Apache-Beam-Pipeline-To-load-CSV-data-into-a-PostgreSQL-Table). 
Check it out if you want to know more.

## Dependencies
* python==3.8
* airflow==2.8.1
* apache-beam==2.52.0
* apache-airflow-providers-apache-beam==5.5.0
* apache-airflow-providers-postgres==5.10.0

## Project structure
```commandline
Launch-an-Apache-Beam-Pipeline-with-Apache-Airflow
├── Airflow
│   ├── dags
│   ├── docker-compose.yml
│   ├── staging_dags
│   │   └── run_beam_pipeline.py
│   ├── logs
│   └── workers
│       ├── beam
│       │   ├── pipeline.py
│       │   └── source
│       │       └── salary_data.csv
│       ├── Dockerfile
│       └── requirements.txt
├── README.md
└── TargetDB

```

___
The ***TargetDB*** folder contains only a ```.env``` database environment variable to 
necessary to launch the postgres container. Below is the content of the 
```.env``` file.

```commandline
POSTGRES_DB=beam_db
POSTGRES_USER=beam_user
POSTGRES_PASSWORD=ra5hoxetRami5
```
___
Folder ***Airflow*** contains all the necessary files to launch Apache Airflow and 
run airflow dags. The ***airflow*** instance is launched with the 
```RootFolder/Airflow/docker-compose.yml``` file.
* The ```dags``` folder is dedicated to contain the airflow dags,
* The ```staging_dags``` folder is a staging area for reviewing airflow dags before moving them to the ```dags``` 
folder for execution by the airflow scheduler,
* The ```logs``` is designed to contains airflow pipeline executions logs,
* ```workers``` contains necessary the files to set the workers environment (install 
airflow plugins and requirements) and the apache beam pipelines to run.

## Launch the Target Database

As a recall, the goal here is run an apache beam pipeline that will read a csv file and 
load the data into a postgres database. The target database here is launched in a separate 
docker container, not included in the ```docker-compose.yml``` of the airflow environment.

For communication to be possible between airflow and the target database, both must belong 
to the same docker network.

First create a docker network ```airflow_net``` with the command below
```commandline
docker network create airflow_net
```

Then run a postgres container:
```commandline
docker run --name target_db -p 5433:5432 --env-file .env --network=airflow_net -d postgres:13-alpine
```
* ```--name target_db```: set the name of the container,
* ```-p 5433:5432```: listening to port 5433 on localhost and 5432 inside the container,
* ```--network airflow_net```: put the container inside the ```airflow_net``` network
* ```--env-file .env```: load postgres environment variables from the ```.env``` file
* ```postgres:13-alpine```: the version of the docker image to pull from dockerhub

With option ```-d```, the container is running in detached mode.

Note that all the containers running apache airflow will the assigned to the same ```airflow_net``` 
docker network.


## Launch Apache Airflow

### Apply database migrations
```shell
docker compose run airflow-webserver airflow db migrate
```
This command applies database migration necessary for the web server to run.

### Start Airflow
Launch Apache Airflow in detach mode with the docker compose command:

```shell
docker compose up -d
```
and open the admin web UI with ```localhost:8081```. The default username is ```airflow```, 
same for the password.

### Create Airflow connection object for the target database
On the menu, go to ```Admin >> Connections``` and add a new postgres connection with the following values:
* Connection Id: ```target_db_id```
* Connection Type: ```Postgres```
* Host: ```target_db```
* Database: ```beam_db```
* Login: ```beam_user```
* Password: ```ra5hoxetRami5```
* Port: ```5432```

Or run the command below to create the connection id
```commandline
docker-compose exec airflow-webserver bash -c "airflow connections add 'target_db_id' \
--conn-type 'postgres' \
--conn-schema 'beam_db' \
--conn-login 'beam_user' \
--conn-password 'ra5hoxetRami5' \
--conn-host 'target_db' \
--conn-port '5432'"
```

### Create the airflow variables that are used in the DAG
* The ```sink_postgres_table``` variable sets the name of the destination table: "**salary_data**" is this case, but you can set 
anything you want. The table will be automatically created in the target postgres database,
* The ```source_csv_file``` variable contains the path to the source csv file,
* The ```beam_pipeline_py_file``` variable contains the path to the beam pipeline launched by airflow.

```shell
docker compose exec airflow-webserver bash -c "airflow variables set sink_postgres_table salary_data"
docker compose exec airflow-webserver bash -c "airflow variables set source_csv_file /opt/airflow/workers/beam/source/salary_data.csv"
docker compose exec airflow-webserver bash -c "airflow variables set beam_pipeline_py_file /opt/airflow/workers/beam/pipeline.py"
```

## Run the Airflow DAG

### Copy/Move the run_beam_pipeline.py DAG from the staging to the dags folder
```shell
$ cd Launch an Apache Beam Pipeline with Apache Airflow/Airflow
$ mv staging_dags/run_beam_pipeline.py dags/
```

It will take 3-5 min for airflow to detect the dags.

### Schedule the DAG
You can run your dag by clicking on the **Run** button or just schedule the dag by changing the the ```start_date``` 
and ```schedule_interval``` parameters of the DAG object. By default, I configured the pipeline to run ```once``` on 
the ```2100-01-01T00:00```. Change the ```start_date``` parameter to run at you ease.

```python
default_args = {
    'owner': 'airflow',
    'start_date': datetime(year=2100, month=1, day=1, hour=00, minute=00),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}
...
with DAG(dag_id='beam_pipeline_dag', default_args=default_args, schedule_interval='@once',
    description='A simple DAG to run a Beam pipeline that reads data from a csv file and load into a postgres database'
) as dag:
    ...
```
You can also change the schedule interval as follows to run the dag every 5 minutes for example.
```commandline
schedule_interval='*/5 * * * *'
```

### Inspect the sink table & check the result
Connect to the target_db container

```shell
docker exec -it target_db bash
```
1. The connect to the postgres database
```shell
psql -U beam_user -d beam_db
```
2. Use the ```\d``` command to list the relations (tables) and confirm that the table defined by the sink_postgres_table variable has 
been created.
```shell
            List of relations
 Schema |    Name     | Type  |   Owner   
--------+-------------+-------+-----------
 public | salary_data | table | beam_user
(1 row)
```
3. Run the ```select``` query to confirm that the data from the csv file have beam copied to the target table
```shell
select * from salary_table;
```
```shell
 age | gender | education_level |               job_title               | year_of_experience | salary 
-----+--------+-----------------+---------------------------------------+--------------------+--------
  32 | Male   | Bachelor        | Software Engineer                     |                  5 |  90000
  28 | Female | Master          | Data Analyst                          |                  3 |  65000
  45 | Male   | PhD             | Senior Manager                        |                 15 | 150000
  36 | Female | Bachelor        | Sales Associate                       |                  7 |  60000
  52 | Male   | Master          | Director                              |                 20 | 200000
  29 | Male   | Bachelor        | Marketing Analyst                     |                  2 |  55000
  42 | Female | Master          | Product Manager                       |                 12 | 120000
  31 | Male   | Bachelor        | Sales Manager                         |                  4 |  80000
  26 | Female | Bachelor        | Marketing Coordinator                 |                  1 |  45000
  38 | Male   | PhD             | Senior Scientist                      |                 10 | 110000
  29 | Male   | Master          | Software Developer                    |                  3 |  75000

```
#### Author
***Christian Carmel WENGA***