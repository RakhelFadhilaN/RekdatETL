from datetime import datetime, timedelta
from airflow import DAG
import requests
import pandas as pd
import logging
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from airflow.models import Variable
import os
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration remains the same
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
OMDB_BASE_URL = 'http://www.omdbapi.com/'
TMDB_API_KEY =  'f0b53a601fc5fb5ecbf61da1c4f871eb'
OMDB_API_KEY =  '31ab3ef2'

def get_api_key(key_name, env_var_name):
    api_key = Variable.get(key_name, default_var=os.getenv(env_var_name))
    if not api_key or api_key in ['f0b53a601fc5fb5ecbf61da1c4f871eb', '31ab3ef2']:
        raise ValueError(f"Valid API key not found for {key_name}")
    return api_key

# Default DAG arguments remain the same
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'comprehensive_movie_data_etl',
    default_args=default_args,
    description='Comprehensive Movie Data ETL Pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Updated CREATE_MOVIES_TABLE_SQL with page_number column
CREATE_MOVIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    overview TEXT,
    release_date DATE,
    genres TEXT,
    tmdb_rating FLOAT,
    imdb_rating VARCHAR(10),
    box_office VARCHAR(50),
    awards TEXT,
    runtime VARCHAR(20),
    fetch_date DATE,
    page_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Drop existing indexes if they exist
DROP INDEX IF EXISTS idx_movies_release_date;
DROP INDEX IF EXISTS idx_movies_genres;

-- Recreate indexes
CREATE INDEX idx_movies_release_date ON movies(release_date);
CREATE INDEX idx_movies_genres ON movies(genres);
"""

# Function to check if page_number column exists
CHECK_PAGE_NUMBER_SQL = """
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name = 'movies' 
    AND column_name = 'page_number'
);
"""

# SQL to add page_number column if it doesn't exist
ADD_PAGE_NUMBER_SQL = """
ALTER TABLE movies 
ADD COLUMN IF NOT EXISTS page_number INTEGER;
"""

def ensure_table_schema():
    """
    Ensure the table schema is up to date
    """
    try:
        pg_hook = PostgresHook(postgres_conn_id='movie_connection')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        # Check if page_number column exists
        cursor.execute(CHECK_PAGE_NUMBER_SQL)
        has_page_number = cursor.fetchone()[0]

        if not has_page_number:
            logger.info("Adding page_number column to movies table")
            cursor.execute(ADD_PAGE_NUMBER_SQL)
            conn.commit()
            logger.info("Successfully added page_number column")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error ensuring table schema: {str(e)}")
        raise


# Function to fetch movie data
def fetch_movie_data(**context):
    def safe_api_call(url, params, method='get', timeout=10):
        try:
            if method == 'get':
                response = requests.get(url, params=params, timeout=timeout)
            else:
                raise ValueError("Unsupported method")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API Call Error: {str(e)}")
            return None

    def get_popular_movies(page=1):
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'page': page
        }
        return safe_api_call(url, params)

    def get_movie_details_tmdb(movie_id):
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US'
        }
        return safe_api_call(url, params)

    def get_movie_details_omdb(movie_title):
        url = OMDB_BASE_URL
        params = {
            't': movie_title,
            'apikey': OMDB_API_KEY
        }
        response = safe_api_call(url, params)
        return response if response and response.get('Response') == 'True' else None

    # Main data fetching logic
    all_movies_data = []
    max_pages = 20  # Limit to 20 pages to control API calls

    try:
        # First, determine total pages
        initial_response = get_popular_movies(1)
        if not initial_response:
            logger.error("Failed to fetch initial page of movies")
            return []

        total_pages = min(initial_response.get('total_pages', 20), max_pages)
        logger.info(f"Will fetch {total_pages} pages of movies")

        # Fetch movies from all pages
        for page in range(1, total_pages + 1):
            logger.info(f"Processing page {page}")
            page_response = get_popular_movies(page)
            
            if not page_response:
                logger.warning(f"Skipped page {page}")
                continue

            movies = page_response.get('results', [])
            
            for movie in movies:
                try:
                    movie_id = movie['id']
                    
                    # Fetch TMDB details
                    tmdb_details = get_movie_details_tmdb(movie_id)
                    if not tmdb_details:
                        logger.warning(f"Skipping movie {movie_id} - TMDB details not found")
                        continue

                    # Fetch OMDB details
                    omdb_details = get_movie_details_omdb(tmdb_details.get('title', ''))

                    # Prepare movie record
                    movie_record = {
                        'movie_id': movie_id,
                        'title': tmdb_details.get('title', 'Unknown Title'),
                        'overview': tmdb_details.get('overview', ''),
                        'release_date': tmdb_details.get('release_date'),
                        'genres': ','.join([g['name'] for g in tmdb_details.get('genres', [])]),
                        'tmdb_rating': tmdb_details.get('vote_average', 0),
                        'imdb_rating': omdb_details.get('imdbRating', 'N/A') if omdb_details else 'N/A',
                        'box_office': omdb_details.get('BoxOffice', 'N/A') if omdb_details else 'N/A',
                        'awards': omdb_details.get('Awards', 'N/A') if omdb_details else 'N/A',
                        'runtime': omdb_details.get('Runtime', 'N/A') if omdb_details else 'N/A',
                        'fetch_date': datetime.now().date(),
                        'page_number': page
                    }
                    
                    all_movies_data.append(movie_record)
                    
                except Exception as e:
                    logger.error(f"Error processing individual movie: {str(e)}")
                    continue

        logger.info(f"Total movies fetched: {len(all_movies_data)}")
        
        # Push to XCom
        context['task_instance'].xcom_push(key='movies_data', value=all_movies_data)
        
        return all_movies_data

    except Exception as e:
        logger.error(f"Unexpected error in fetch_movie_data: {str(e)}")
        return []

# Function to insert movie data
def insert_movie_data(**context):
    """
    Insert movie data using execute_values for better performance
    """
    movies_data = context['task_instance'].xcom_pull(key='movies_data')
    
    if not movies_data:
        logger.warning("No movie data to insert")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(movies_data)
    
    # Get Postgres connection
    pg_hook = PostgresHook(postgres_conn_id='movie_connection')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    try:
        # Prepare data for insertion
        columns = df.columns.tolist()
        values = [tuple(x) for x in df.values]
        
        # SQL for insert/update (upsert)
        insert_sql = """
            INSERT INTO movies ({})
            VALUES %s
            ON CONFLICT (movie_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                overview = EXCLUDED.overview,
                release_date = EXCLUDED.release_date,
                genres = EXCLUDED.genres,
                tmdb_rating = EXCLUDED.tmdb_rating,
                imdb_rating = EXCLUDED.imdb_rating,
                box_office = EXCLUDED.box_office,
                awards = EXCLUDED.awards,
                runtime = EXCLUDED.runtime,
                fetch_date = EXCLUDED.fetch_date,
                page_number = EXCLUDED.page_number,
                created_at = CURRENT_TIMESTAMP
        """.format(','.join(columns))
        
        # Execute the insert
        execute_values(cursor, insert_sql, values, page_size=100)
        
        # Commit the transaction
        conn.commit()
        logger.info(f"Successfully inserted/updated {len(df)} movies")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting movies: {str(e)}")
        raise
    
    finally:
        cursor.close()
        conn.close()

def test_db_connection():
    """
    Test database connection and log connection details
    """
    try:
        pg_hook = PostgresHook(postgres_conn_id='movie_connection')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        logger.info(f"Database connection test successful: {result}")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        raise

# Create Tasks
test_db_connection_task = PythonOperator(
    task_id='test_db_connection',
    python_callable=test_db_connection,
    dag=dag
)

create_table_task = PostgresOperator(
    task_id='create_movies_table',
    postgres_conn_id='movie_connection',
    sql=CREATE_MOVIES_TABLE_SQL,
    dag=dag
)

ensure_schema_task = PythonOperator(
    task_id='ensure_schema',
    python_callable=ensure_table_schema,  # Removed provide_context=True
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

# Updated Task Dependencies
test_db_connection_task >> create_table_task >> ensure_schema_task >> fetch_movie_data_task >> insert_movie_data_task