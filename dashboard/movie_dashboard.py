import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import numpy as np
from datetime import datetime
import os

def get_database_connection():
    database_url = os.getenv('DATABASE_URL', 
                            "postgresql://airflow:airflow@localhost:5432/movies")
    return create_engine(database_url)

# Load data from database
def load_data():
    engine = get_database_connection()
    query = """
    SELECT * FROM movies 
    WHERE release_date IS NOT NULL 
    AND tmdb_rating IS NOT NULL 
    AND imdb_rating != 'N/A'
    """
    df = pd.read_sql(query, engine)
    
    # Convert types
    df['release_date'] = pd.to_datetime(df['release_date'])
    df['imdb_rating'] = pd.to_numeric(df['imdb_rating'], errors='coerce')
    df['box_office'] = df['box_office'].replace('N/A', np.nan)
    if 'box_office' in df.columns:
        df['box_office'] = df['box_office'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['box_office'] = pd.to_numeric(df['box_office'], errors='coerce')

    
    return df

def main():
    st.set_page_config(page_title="Movie Analytics Dashboard", layout="wide")
    
    # Title and description
    st.title("🎬 Movie Analytics Dashboard")
    st.markdown("Analysis of popular movies from TMDB and OMDB APIs")
    
    # Load data
    df = load_data()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = df['release_date'].min().date()
    max_date = df['release_date'].max().date()
    date_range = st.sidebar.date_input(
        "Release Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Genre filter
    df['genres'] = df['genres'].fillna('')
    all_genres = [genre for genres in df['genres'].str.split(',') for genre in genres]
    unique_genres = sorted(list(set(all_genres)))
    selected_genres = st.sidebar.multiselect(
        "Select Genres",
        unique_genres,
        default=[]
    )
    
    # Filter data based on selections
    if df['release_date'].isna().any():
        df = df[df['release_date'].notna()]
    mask = (df['release_date'].dt.date >= date_range[0]) & (df['release_date'].dt.date <= date_range[1])
    if selected_genres:
        mask = mask & df['genres'].apply(lambda x: any(genre in x for genre in selected_genres) if isinstance(x, str) else False)
    filtered_df = df[mask]
    
    # Reset index to ensure no duplicate labels
    filtered_df = filtered_df.reset_index(drop=True).drop_duplicates()

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Movies", len(filtered_df))
    with col2:
        avg_tmdb = filtered_df['tmdb_rating'].mean() if not filtered_df.empty else 0

        st.metric("Avg TMDB Rating", f"{avg_tmdb:.1f}")
    with col3:
        avg_imdb = filtered_df['imdb_rating'].mean()
        st.metric("Avg IMDB Rating", f"{avg_imdb:.1f}")
    with col4:
        total_box_office = filtered_df['box_office'].sum()
        st.metric("Total Box Office", f"${total_box_office:,.0f}")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Rating Distribution")
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=filtered_df['tmdb_rating'], name='TMDB Rating', 
                                 nbinsx=20, opacity=0.7))
        fig.add_trace(go.Histogram(x=filtered_df['imdb_rating'], name='IMDB Rating', 
                                 nbinsx=20, opacity=0.7))
        fig.update_layout(barmode='overlay', title="Rating Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Ratings Correlation")
        fig = px.scatter(filtered_df, x='tmdb_rating', y='imdb_rating', 
                        title="TMDB vs IMDB Ratings",
                        trendline="ols")
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Genre Distribution")
        genre_counts = pd.Series([g.strip() for genres in filtered_df['genres'].str.split(',') 
                                for g in genres]).value_counts()
        fig = px.bar(x=genre_counts.index, y=genre_counts.values,
                    title="Movie Counts by Genre")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Release Timeline")
        timeline_data = filtered_df.groupby(filtered_df['release_date'].dt.to_period('M')).size()
        fig = px.line(x=timeline_data.index.astype(str), y=timeline_data.values,
                     title="Movies Released Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top rated movies table
    st.subheader("Top Rated Movies")
    top_movies = filtered_df.nlargest(10, 'tmdb_rating')[
        ['title', 'release_date', 'genres', 'tmdb_rating', 'imdb_rating', 'box_office']
    ]
    st.dataframe(top_movies.style.format({
        'release_date': lambda x: x.strftime('%Y-%m-%d'),
        'tmdb_rating': '{:.1f}',
        'imdb_rating': '{:.1f}',
        'box_office': '${:,.0f}'
    }))
    
    # Box office analysis
    st.subheader("Box Office Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
    # Check if required columns exist
        if 'genres' in filtered_df.columns and 'box_office' in filtered_df.columns:
        # Reset index and explode genres to create one row per genre
            filtered_df = filtered_df.reset_index(drop=True).drop_duplicates()

            genre_box_office_df = filtered_df.assign(
            genre=filtered_df['genres'].str.split(',').explode().str.strip()
        ).reset_index(drop=True)

        # Remove rows with missing genres or box office values
            genre_box_office_df = genre_box_office_df[~genre_box_office_df['genre'].isna()]
            genre_box_office_df = genre_box_office_df[~genre_box_office_df['box_office'].isna()]

        # Calculate average box office by genre
            box_office_by_genre = (
            genre_box_office_df.groupby('genre')['box_office']
            .mean(skipna=True)
            .sort_values(ascending=True)
        )
        else:
        # Create an empty series if required columns are missing
            box_office_by_genre = pd.Series(dtype=float)
        
        fig = px.bar(x=box_office_by_genre.values, y=box_office_by_genre.index,
                    title="Average Box Office by Genre",
                    orientation='h')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(filtered_df, x='tmdb_rating', y='box_office',
                        title="Rating vs Box Office",
                        trendline="ols")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()