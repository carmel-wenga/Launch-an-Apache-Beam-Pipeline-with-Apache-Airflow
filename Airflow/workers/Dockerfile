# Use the official Airflow image as a base
FROM apache/airflow:2.8.1

# Copy your requirements file
COPY requirements.txt /opt/airflow/workers/requirements.txt

# Install the Python packages
RUN pip install -r /opt/airflow/workers/requirements.txt