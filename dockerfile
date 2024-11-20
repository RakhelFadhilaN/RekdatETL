FROM apache/airflow:latest

WORKDIR /app

USER root
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    curl \
    git \
    software-properties-common \
    lsof\
    procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt

USER airflow
RUN pip install --no-cache-dir -r /requirements.txt





EXPOSE 8501 

CMD ["streamlit", "run", "movie_dashboard.py", "--server.address=0.0.0.0"]