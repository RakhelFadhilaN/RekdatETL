from datetime import datetime, timedelta
from airflow import DAG
import requests
import pandas as pd
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.bash import BashOperator


# API Configuration
TMDB_API_KEY = 'f0b53a601fc5fb5ecbf61da1c4f871eb'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
OMDB_API_KEY = '6357410a'#31ab3ef2
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
    schedule_interval=timedelta(hours=1),
    catchup=False,
)

# Function to fetch movie data
def fetch_movie_data(**context):
    def validate_date(date_str):
        """Validate and parse a date string. Return None if invalid or empty."""
        try:
            if date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            return None
        except ValueError:
            return None

    def get_popular_movies(page=1):
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'page': page
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
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

    # Fetch last fetched page from metadata table
    pg_hook = PostgresHook(postgres_conn_id='movie_connection')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT last_fetched_page FROM metadata WHERE id = 1;")
    result = cursor.fetchone()
    last_page = result[0] if result else 1

    print(f"Resuming from page {last_page}")

    movies_data = []
    num_pages = 10  # Fetch 10 pages at a time

    for page in range(last_page, last_page + num_pages):
        response_data = get_popular_movies(page)
        popular_movies = response_data.get('results', [])
        total_pages = response_data.get('total_pages')

        print(f"Fetching page {page} of {total_pages}")
        
        for movie in popular_movies:
            try:
                movie_id = movie['id']
                tmdb_details = get_movie_details_tmdb(movie_id)
                omdb_details = get_movie_details_omdb(tmdb_details['title'])

                release_date = validate_date(tmdb_details.get('release_date'))

                movie_record = {
                    'movie_id': movie_id,
                    'title': tmdb_details['title'],
                    'overview': tmdb_details['overview'],
                    'release_date': release_date if release_date else '1900-01-01',
                    'genres': ','.join([genre['name'] for genre in tmdb_details['genres']]),
                    'tmdb_rating': tmdb_details['vote_average'],
                    'imdb_rating': omdb_details.get('imdbRating', 'N/A') if omdb_details else 'N/A',
                    'box_office': omdb_details.get('BoxOffice', 'N/A') if omdb_details else 'N/A',
                    'awards': omdb_details.get('Awards', 'N/A') if omdb_details else 'N/A',
                    'runtime': omdb_details.get('Runtime', 'N/A') if omdb_details else 'N/A',
                }
                movies_data.append(movie_record)
                print(f"Processed movie: {movie_record['title']}")

            except Exception as e:
                print(f"Error processing movie {movie.get('id')}: {str(e)}")
                continue

    print(f"Total movies fetched: {len(movies_data)}")
    
    # Update metadata table with the last fetched page
    new_last_page = last_page + num_pages
    cursor.execute("""
        INSERT INTO metadata (id, last_fetched_page) 
        VALUES (1, %s) 
        ON CONFLICT (id) DO UPDATE SET last_fetched_page = EXCLUDED.last_fetched_page;
    """, (new_last_page,))
    conn.commit()
    conn.close()

    context['task_instance'].xcom_push(key='movies_data', value=movies_data)

def insert_movie_data(**context):
    movies_data = context['task_instance'].xcom_pull(key='movies_data')
    pg_hook = PostgresHook(postgres_conn_id='movie_connection')

    for movie in movies_data:
        pg_hook.run("""
            INSERT INTO movies (
                movie_id, title, overview, release_date, genres,
                tmdb_rating, imdb_rating, box_office, awards, runtime
            ) VALUES (
                %(movie_id)s, %(title)s, %(overview)s, %(release_date)s, %(genres)s,
                %(tmdb_rating)s, %(imdb_rating)s, %(box_office)s, %(awards)s, %(runtime)s
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
                runtime = EXCLUDED.runtime
        """, parameters=movie)

# Create PostgreSQL tables
create_movies_table_sql = """
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
    runtime VARCHAR(20)
);
"""

create_metadata_table_sql = """
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY,
    last_fetched_page INTEGER
);
"""

# Define tasks
create_tables_task = PostgresOperator(
    task_id='create_tables',
    postgres_conn_id='movie_connection',
    sql=f"{create_movies_table_sql} {create_metadata_table_sql}",
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

refresh_streamlit_task = BashOperator(
    task_id='refresh_streamlit_dashboard',
    bash_command=('pkill -f "streamlit run" || true && '
        'nohup streamlit run /dashboard/dashboard.py --server.port 8501 > /tmp/streamlit.log 2>&1 &'),
    dag=dag,
)

# Set task dependencies
create_tables_task >> fetch_movie_data_task >> insert_movie_data_task >> refresh_streamlit_task
