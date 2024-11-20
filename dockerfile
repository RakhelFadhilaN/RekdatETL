FROM python:3.9-slim

WORKDIR /app

USER root
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    curl \
    git \
    software-properties-common \
    procps-ng \  
    procps \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
    
RUN pip install --upgrade pip 

RUN pip install streamlit

RUN pip install --no-cache-dir scikit-learn

COPY dashboard/movie_dashboard.py .

EXPOSE 8501 

USER airflow

CMD ["streamlit", "run", "movie_dashboard.py", "--server.address=0.0.0.0"]