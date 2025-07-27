-- Letterboxd Movie Recommendations Database Schema
-- Run this SQL in your Supabase SQL Editor to create all required tables

-- 1. Users table - stores user information and usage tracking
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    count INTEGER DEFAULT 1,
    first_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. User Statistics table - stores calculated user statistics
CREATE TABLE IF NOT EXISTS user_statistics (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    user_rating_mean REAL,
    user_rating_std REAL,
    letterboxd_rating_mean REAL,
    letterboxd_rating_std REAL,
    rating_differential_mean REAL,
    rating_differential_std REAL,
    letterboxd_rating_count_mean REAL,
    letterboxd_rating_count_std REAL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(username)
);

-- 3. User Ratings table - stores user movie ratings
CREATE TABLE IF NOT EXISTS user_ratings (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    movie_id VARCHAR(255) NOT NULL,
    user_rating REAL NOT NULL,
    liked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(username, movie_id)
);

-- 4. Movie URLs table - stores movie URLs for scraping
CREATE TABLE IF NOT EXISTS movie_urls (
    id SERIAL PRIMARY KEY,
    movie_id VARCHAR(255) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    deprecated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Movie Data table - stores movie information and metadata
CREATE TABLE IF NOT EXISTS movie_data (
    id SERIAL PRIMARY KEY,
    movie_id VARCHAR(255) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    release_year INTEGER,
    runtime INTEGER,
    genres TEXT,
    country_of_origin INTEGER,
    content_type VARCHAR(50),
    letterboxd_rating REAL,
    letterboxd_rating_count INTEGER,
    poster TEXT,
    -- Genre boolean columns
    is_action INTEGER DEFAULT 0,
    is_adventure INTEGER DEFAULT 0,
    is_animation INTEGER DEFAULT 0,
    is_comedy INTEGER DEFAULT 0,
    is_crime INTEGER DEFAULT 0,
    is_documentary INTEGER DEFAULT 0,
    is_drama INTEGER DEFAULT 0,
    is_family INTEGER DEFAULT 0,
    is_fantasy INTEGER DEFAULT 0,
    is_history INTEGER DEFAULT 0,
    is_horror INTEGER DEFAULT 0,
    is_music INTEGER DEFAULT 0,
    is_mystery INTEGER DEFAULT 0,
    is_romance INTEGER DEFAULT 0,
    is_science_fiction INTEGER DEFAULT 0,
    is_tv_movie INTEGER DEFAULT 0,
    is_thriller INTEGER DEFAULT 0,
    is_war INTEGER DEFAULT 0,
    is_western INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Application Metrics table - stores app usage metrics
CREATE TABLE IF NOT EXISTS application_metrics (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    new_users INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    recommendations_generated INTEGER DEFAULT 0,
    statistics_calculated INTEGER DEFAULT 0,
    watchlist_picks_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_statistics_username ON user_statistics(username);
CREATE INDEX IF NOT EXISTS idx_user_ratings_username ON user_ratings(username);
CREATE INDEX IF NOT EXISTS idx_user_ratings_movie_id ON user_ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_movie_urls_movie_id ON movie_urls(movie_id);
CREATE INDEX IF NOT EXISTS idx_movie_data_movie_id ON movie_data(movie_id);
CREATE INDEX IF NOT EXISTS idx_application_metrics_date ON application_metrics(date);

-- Add Row Level Security (RLS) policies if needed
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_statistics ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_ratings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE movie_urls ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE movie_data ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE application_metrics ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE users IS 'Stores user information and usage tracking';
COMMENT ON TABLE user_statistics IS 'Stores calculated user statistics and percentiles';
COMMENT ON TABLE user_ratings IS 'Stores user movie ratings scraped from Letterboxd';
COMMENT ON TABLE movie_urls IS 'Stores movie URLs for web scraping';
COMMENT ON TABLE movie_data IS 'Stores movie metadata and characteristics';
COMMENT ON TABLE application_metrics IS 'Stores daily application usage metrics'; 