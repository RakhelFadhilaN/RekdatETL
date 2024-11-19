FROM  apache/airflow:latest

USER root
RUN apt-get update && \
    apt-get -y install git && \
    apt-get clean \
    python3-pip \
    python3-yaml \
    rsyslog systemd syst

USER airflow