run the command below to initialize the database

```commandline
docker-compose run airflow-webserver airflow db init
```

```commandline
docker compose exec airflow-webserver bash
```
create a user and set the password
```commandline
airflow users create --username carmel --firstname Carmel --lastname WENGA --role Admin --email carmelweng@de.me
```

```commandline
docker build -t target_db .
```

Create a docker network to contain the database and the airflow 

```commandline
docker network create airflow_net
```

Run the database

```commandline
docker run --name target_db -p 5433:5432 --env-file .env --network=airflow_net -d postgres:13-alpine
```

describe why you are using the following in the docker compose file
```commandline
  user: "1000:0"
```

add a script/command to create connection id (airflow connection) for the airflow config

create a custom Option class to handler pipeline options from apache airflow beam operator.