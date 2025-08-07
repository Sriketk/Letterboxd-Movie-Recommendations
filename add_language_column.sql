-- Add language column to existing movie_data table
-- Run this SQL in your Supabase SQL Editor to add the language column

ALTER TABLE movie_data 
ADD COLUMN IF NOT EXISTS language INTEGER DEFAULT 0;

-- Add comment to document the new column
COMMENT ON COLUMN movie_data.language IS 'Numerical representation of the movie language (0=English, 1=Spanish, 2=French, 3=German, 8=Korean, etc.)';
