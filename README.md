# Movie Recommendations - End to End Data Engineering Project

## 👥 Team Members
   - Jhon Samuel Kudadiri (22/503772/TK/55066) 📚🤓🏆
   - Jovita Ayu Ramaniyya (22/503808/TK/55072)
   - Rakhel Fadhila Nastiti (22/504692/TK/55216) 🙌🤩👩🏻‍💻

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Data Sources](#data-sources)
- [Project Deliverables](#project-delivarables)

## Overview
This project aims to develop a robust predictive model for estimating the IMDb vote averages of upcoming movies, supported by a comprehensive ETL (Extract, Transform, Load) pipeline. The pipeline will extract data from various sources, including genres, release dates, keywords derived from movie overviews, and real-time search interest metrics from Google Trends related to the movie title and its cast. By transforming and analyzing this historical data alongside recent audience behavior, the model will identify key factors that significantly influence viewer ratings and preferences. The insights derived from this model will empower filmmakers and marketers to make data-driven decisions regarding movie releases, promotional strategies, and target audience engagement. Ultimately, this project seeks to enhance the accuracy of box office forecasts and movie reception predictions, ensuring that studios can better align their productions with audience expectations while leveraging an efficient and scalable data processing framework.

## Project Structure
project/
├── dags/                         # Directory for Airflow DAGs
│   ├── __pycache__/              # Compiled Python files (automatically generated)
│   │   ├── dag.cpython-38.pyc    # Compiled version of the `dag.py` file
│   ├── dag.py                    # Main DAG file for Airflow workflows
├── dashboard/                    # Directory for dashboard code
│   ├── movie_dashboard.py        # Streamlit app for movie recommendations
├── logs/                         # Airflow logs directory
│   ├── dag_processor_manager/    # Logs for Airflow DAG processing
│   │   ├── dag_processor_manager.log  # Log file for DAG processor
│   ├── scheduler/                # Logs for Airflow scheduler
│       ├── 2024-11-18/           # Logs for a specific day
│       ├── native_dags/          # Example DAGs log directory
│           ├── example_dags/
│       ├── dag.py.log            # Log file for the `dag.py` DAG
├── .gitattributes                # Git attributes file
├── .gitignore                    # File specifying untracked files in Git
├── README.md                     # Project documentation
├── docker-compose.yml            # Docker Compose configuration for multi-container setup
├── dockerfile                    # Dockerfile for containerizing the project
├── movies.csv                    # CSV file containing movie data
├── requirements.txt              # Python dependencies

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/RakhelFadhilaN/RekdatETL.git
   ```
2. Navigate to the project directory:
   ```bash
   cd RekdatETL
   ```
3. Docker compose up:
   ```bash
   docker-compose up
   ```
   
## How to Run
- **Required Softwares**: Ensure you have Docker Desktop and Visual Studio Code IDE 
Links:<br>
  [Docker Desktop](https://www.docker.com/products/docker-desktop/) <br>
  [Visual Studio](https://code.visualstudio.com/Download)
  
- **Apache Airflow**: Start the Airflow web server and scheduler:
  ```bash
  airflow db init      # Initialize the database (first time only)
  airflow webserver --port 8080
  airflow scheduler
  ```

- **ETL Pipeline**: Visit `http://localhost:8080` in your browser to trigger the ETL pipeline via the Airflow dashboard.

- **Start Dashboard**: Launch the dashboard with:
  ```bash
  streamlit run src/dashboard/app.py
  ```

## Data Sources
1. **TMDB API**: Provide basic information (e.g., title, overview of the movie, genres, release date, and rating)
2. **OMDP API**: Adds details (e.g., IMDb rating, box office revenue, awards, and runtime)

## Project Deliverables
Report:https://curse-snarl-0ec.notion.site/ETL-Movie-Data-Recommendation-Model-143dd068d33780c58c97f9c2311be770?pvs=73
Video:    


