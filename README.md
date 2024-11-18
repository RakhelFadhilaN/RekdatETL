# Movie Recommendations - End to End Data Engineering Project

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Architecture](#tech-architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Data Sources](#data-sources)
- [Data Processing and Transformation](#data-processing-and-transformation)
- [Machine Learning Model](#machine-learning-model)
- [Dashboard](#dashboard)
- [Deployment](#deployment)
- [Challenges and Solutions](#challenges-and-solutions)
- [Future Improvements](#future-improvements)
- [Conclusion](#conclusion)

## Overview
This project aims to develop a robust predictive model for estimating the IMDb vote averages of upcoming movies, supported by a comprehensive ETL (Extract, Transform, Load) pipeline. The pipeline will extract data from various sources, including genres, release dates, keywords derived from movie overviews, and real-time search interest metrics from Google Trends related to the movie title and its cast. By transforming and analyzing this historical data alongside recent audience behavior, the model will identify key factors that significantly influence viewer ratings and preferences. The insights derived from this model will empower filmmakers and marketers to make data-driven decisions regarding movie releases, promotional strategies, and target audience engagement. Ultimately, this project seeks to enhance the accuracy of box office forecasts and movie reception predictions, ensuring that studios can better align their productions with audience expectations while leveraging an efficient and scalable data processing framework.

## Features

## Tech Architecture

## Project Structure

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/movie_recommendation_project.git
   ```
2. Navigate to the project directory:
   ```bash
   cd movie_recommendation_project
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
## How to Run
- **Apache Airflow**: Start the Airflow web server and scheduler:
  ```bash
  airflow db init      # Initialize the database (first time only)
  airflow webserver --port 8080
  airflow scheduler
  ```

- **ETL Pipeline**: Visit `http://localhost:8080` in your browser to trigger the ETL pipeline via the Airflow dashboard.

- **Model Training**: Train the model by executing:
  ```bash
  python src/model/train_model.py
  ```

- **Start Dashboard**: Launch the dashboard with:
  ```bash
  streamlit run src/dashboard/app.py
  ```


## Data Sources

## Data Processing and Transformation

## ML(?) Model

## Dashboard

## Challenges & Solution

## Future Improvements

## Conclusions
