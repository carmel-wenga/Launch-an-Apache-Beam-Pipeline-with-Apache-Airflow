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
│   │   └── run_beam_pipeline.py
│   ├── docker-compose.yml
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
* The ```dags``` folder contains the airflow pipelines,
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
docker compose run airflow-webserver airflow db init
```
This command applies database migration necessary for the web server to run.

### Start Airflow
Launch Apache Airflow with the docker compose command:

```shell
docker compose up
```
and open the admin web UI with ```localhost:8081```. The default username is ```airflow```, 
same for the password.

On the menu, go to ```Admin >> Connections``` and add a new postgres connection with the following values:
* Connection Id: ```target_db_id```
* Connection Type: ```Postgres```
* Host: ```target_db```
* Database: ```beam_db```
* Login: ```beam_user```
* Password: ```ra5hoxetRami5```
* Port: ```5432```

Or simply run the command below to create the connection id
```commandline
docker-compose exec airflow-webserver bash -c "airflow connections add 'target_db_id' \
--conn-type 'postgres' \
--conn-schema 'beam_db' \
--conn-login 'beam_user' \
--conn-password 'ra5hoxetRami5' \
--conn-host 'target_db' \
--conn-port '5432'"
```

## Run the Airflow DAG
You can now run your dag by clicking on the **Run** button or scheduling the dag on the 
```run_beam_pipeline.py``` script. By default, I configured the pipeline to run ```once``` on the ```2100-01-01T00:00```
using the ```start_date``` and ```schedule_interval``` parameters. Change the ```start_date``` parameter to run at 
you ease.

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