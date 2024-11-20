# Movie Recommendations - End to End Data Engineering Project

## 👥 Team Members
   - Jhon Samuel Kudadiri (22/503772/TK/55066) 📚🤓🏆
   - Jovita Ayu Ramaniyya (22/503808/TK/55072)
   - Rakhel Fadhila Nastiti (22/504692/TK/55216) 🙌🤩👩🏻‍💻

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Data Sources](#data-sources)
- [Project Deliverables](#project-delivarables)

## Overview
The number of movies and TV shows is growing so fast, making it harder for people to find content that matches their interests. A movie recommendation system helps solve this problem by suggesting movies based on user preferences or similarities between movies.

Two popular sources for movie data are OMDB and TMDB. OMDB provides details such as ratings, Box Office, Awards,  genres, and runtime while TMDB gives details like title, overview, release date, and vote average. By combining both databases, we will be able to create a system for movie recommendations.

In this project, the recommendation system will use data from OMDB and TMDB and compare movie plots using cosine similarity to find and suggest movies with similar stories.

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
Report: [Published Notion](https://curse-snarl-0ec.notion.site/ETL-Movie-Data-Recommendation-Model-143dd068d33780c58c97f9c2311be770?pvs=4) <br>
Video:  https://drive.google.com/file/d/1lynFz__Ljc1T053-lvAmvepmo_RTKewL/view?usp=sharing


