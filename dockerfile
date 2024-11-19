FROM  apache/airflow:latest

USER root
RUN apt-get update && \
    && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-yaml \
    rsyslog systemd systemd-cron sudo \
    apt-get -y install git && \
    apt-get clean 

RUN pip3 install --upgrade pip 

RUN pip3 install streamlit

USER airflow