#!/usr/bin/env python3

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing import database


def check_database_directly():
    print("🔍 DIRECT DATABASE INSPECTION")
    print("=" * 50)

    try:
        # Get the movie data directly from database
        print("📊 Loading movie data from database...")
        movie_data = database.get_movie_data()

        print(f"✅ Total movies in database: {len(movie_data)}")
        print(
            f"📅 Release years range: {movie_data['release_year'].min()} - {movie_data['release_year'].max()}"
        )
        print()

        # Check 2020s movies
        movies_2020s = movie_data[
            (movie_data["release_year"] >= 2020) & (movie_data["release_year"] <= 2024)
        ]

        print(f"🎬 2020s Movies in Database: {len(movies_2020s)}")
        if len(movies_2020s) > 0:
            print("   Sample 2020s movies:")
            sample_2020s = movies_2020s[["title", "release_year", "genres"]].head(10)
            for i, movie in enumerate(sample_2020s.itertuples(), 1):
                print(f"      {i:2d}. {movie.title} ({movie.release_year})")

            # Year distribution for 2020s
            year_counts_2020s = movies_2020s["release_year"].value_counts().sort_index()
            print(f"\n   📅 2020s Year Distribution:")
            for year, count in year_counts_2020s.items():
                print(f"      {year}: {count} movies")

        print()

        # Check sci-fi movies
        print("🚀 Checking Sci-Fi Movies...")

        # Check if is_science_fiction column exists
        sci_fi_columns = [col for col in movie_data.columns if "science" in col.lower()]
        print(f"   Science fiction related columns: {sci_fi_columns}")

        if "is_science_fiction" in movie_data.columns:
            sci_fi_movies = movie_data[movie_data["is_science_fiction"] == 1]
            print(f"   Total sci-fi movies: {len(sci_fi_movies)}")

            if len(sci_fi_movies) > 0:
                print("   Sample sci-fi movies:")
                sample_sci_fi = sci_fi_movies[["title", "release_year"]].head(10)
                for i, movie in enumerate(sample_sci_fi.itertuples(), 1):
                    print(f"      {i:2d}. {movie.title} ({movie.release_year})")

                # Sci-fi by decade
                sci_fi_2020s = sci_fi_movies[
                    (sci_fi_movies["release_year"] >= 2020)
                    & (sci_fi_movies["release_year"] <= 2024)
                ]
                sci_fi_2010s = sci_fi_movies[
                    (sci_fi_movies["release_year"] >= 2010)
                    & (sci_fi_movies["release_year"] <= 2019)
                ]

                print(f"\n   🚀 Sci-fi by decade:")
                print(f"      2020s: {len(sci_fi_2020s)} movies")
                print(f"      2010s: {len(sci_fi_2010s)} movies")

                if len(sci_fi_2020s) > 0:
                    print("\n   Sample 2020s sci-fi:")
                    for i, movie in enumerate(
                        sci_fi_2020s[["title", "release_year"]].head(5).itertuples(), 1
                    ):
                        print(f"      {i}. {movie.title} ({movie.release_year})")

        print()

        # Check genres encoding
        print("🎭 Genre Information:")
        genre_columns = [col for col in movie_data.columns if col.startswith("is_")]
        print(f"   Genre columns found: {len(genre_columns)}")
        print(f"   Genre columns: {genre_columns[:10]}...")  # Show first 10

        # Check if there's a raw genres column
        if "genres" in movie_data.columns:
            print(f"   Raw genres column exists")
            sample_genres = movie_data[movie_data["genres"].notna()]["genres"].head(5)
            print("   Sample genre data:")
            for i, genres in enumerate(sample_genres, 1):
                print(f"      {i}. {genres}")

        print()

        # Check content types
        print("📺 Content Types:")
        if "content_type" in movie_data.columns:
            content_counts = movie_data["content_type"].value_counts()
            print("   Content type distribution:")
            for content_type, count in content_counts.items():
                print(f"      {content_type}: {count}")

        print()
        print("✅ Database inspection complete!")

    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_database_directly()
