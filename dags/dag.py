from datetime import datetime, timedelta
from airflow import DAG
import requests
import pandas as pd
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# API Configuration
TMDB_API_KEY = 'f0b53a601fc5fb5ecbf61da1c4f871eb'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
OMDB_API_KEY = '31ab3ef2'
OMDB_BASE_URL = 'http://www.omdbapi.com/'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 19),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'movie_data_etl',
    default_args=default_args,
    description='ETL pipeline for movie data from TMDB and OMDB APIs',
    schedule_interval=timedelta(days=1),
)

# Function to fetch movie data from both APIs
def fetch_movie_data(**context):
    def get_popular_movies():
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'page': 1
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            raise Exception(f"Error fetching popular movies: {response.status_code}")

    def get_movie_details_tmdb(movie_id):
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching TMDB details for movie ID {movie_id}: {response.status_code}")

    def get_movie_details_omdb(movie_title):
        url = OMDB_BASE_URL
        params = {
            't': movie_title,
            'apikey': OMDB_API_KEY
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return data
            return None
        else:
            raise Exception(f"Error fetching OMDB details for {movie_title}: {response.status_code}")

    # Fetch and combine data
    movies_data = []
    popular_movies = get_popular_movies()

    for movie in popular_movies:
        movie_id = movie['id']
        tmdb_details = get_movie_details_tmdb(movie_id)
        omdb_details = get_movie_details_omdb(tmdb_details['title'])

        movie_record = {
            'movie_id': movie_id,
            'title': tmdb_details['title'],
            'overview': tmdb_details['overview'],
            'release_date': tmdb_details['release_date'],
            'genres': ','.join([genre['name'] for genre in tmdb_details['genres']]),
            'tmdb_rating': tmdb_details['vote_average'],
            'imdb_rating': omdb_details.get('imdbRating', 'N/A') if omdb_details else 'N/A',
            'box_office': omdb_details.get('BoxOffice', 'N/A') if omdb_details else 'N/A',
            'awards': omdb_details.get('Awards', 'N/A') if omdb_details else 'N/A',
            'runtime': omdb_details.get('Runtime', 'N/A') if omdb_details else 'N/A',
            'fetch_date': datetime.now().strftime('%Y-%m-%d')
        }
        movies_data.append(movie_record)

    # Store the data in XCom for the next task
    context['task_instance'].xcom_push(key='movies_data', value=movies_data)

def insert_movie_data(**context):
    # Retrieve data from XCom
    movies_data = context['task_instance'].xcom_pull(key='movies_data')
    
    # Create PostgreSQL connection using hook
    pg_hook = PostgresHook(postgres_conn_id='movie_connection')
    
    # Insert data into PostgreSQL
    for movie in movies_data:
        pg_hook.run("""
            INSERT INTO movies (
                movie_id, title, overview, release_date, genres,
                tmdb_rating, imdb_rating, box_office, awards, runtime, fetch_date
            ) VALUES (
                %(movie_id)s, %(title)s, %(overview)s, %(release_date)s, %(genres)s,
                %(tmdb_rating)s, %(imdb_rating)s, %(box_office)s, %(awards)s, %(runtime)s, %(fetch_date)s
            )
            ON CONFLICT (movie_id) 
            DO UPDATE SET
                title = EXCLUDED.title,
                overview = EXCLUDED.overview,
                genres = EXCLUDED.genres,
                tmdb_rating = EXCLUDED.tmdb_rating,
                imdb_rating = EXCLUDED.imdb_rating,
                box_office = EXCLUDED.box_office,
                awards = EXCLUDED.awards,
                runtime = EXCLUDED.runtime,
                fetch_date = EXCLUDED.fetch_date
        """, parameters=movie)

# Create PostgreSQL table
create_table_sql = """
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    overview TEXT,
    release_date DATE,
    genres TEXT,
    tmdb_rating FLOAT,
    imdb_rating VARCHAR(10),
    box_office VARCHAR(50),
    awards TEXT,
    runtime VARCHAR(20),
    fetch_date DATE
);
"""

# Define tasks
create_table_task = PostgresOperator(
    task_id='create_movies_table',
    postgres_conn_id='movie_connection',
    sql=create_table_sql,
    dag=dag
)

fetch_movie_data_task = PythonOperator(
    task_id='fetch_movie_data',
    python_callable=fetch_movie_data,
    provide_context=True,
    dag=dag
)

insert_movie_data_task = PythonOperator(
    task_id='insert_movie_data',
    python_callable=insert_movie_data,
    provide_context=True,
    dag=dag
)

# Set task dependencies
create_table_task >> fetch_movie_data_task >> insert_movie_data_task