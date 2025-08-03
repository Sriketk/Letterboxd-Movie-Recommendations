#!/usr/bin/env python3

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing import database


def test_fixed_database():
    print("🔧 TESTING FIXED DATABASE FUNCTION")
    print("=" * 50)

    try:
        # Clear the cache first
        print("🗑️  Clearing cache...")
        database.get_movie_data_cached.cache_clear()
        print("   ✅ Cache cleared")

        # Test the fixed function
        print("\n📊 Testing fixed get_movie_data()...")
        movie_data = database.get_movie_data()

        print(f"   ✅ Total movies retrieved: {len(movie_data)}")
        print(
            f"   📅 Release years: {movie_data['release_year'].min()} - {movie_data['release_year'].max()}"
        )

        # Test 2020s coverage
        movies_2020s = movie_data[
            (movie_data["release_year"] >= 2020) & (movie_data["release_year"] <= 2024)
        ]
        print(f"   🎬 2020s movies: {len(movies_2020s)}")

        if len(movies_2020s) > 0:
            year_dist = movies_2020s["release_year"].value_counts().sort_index()
            print("      Year distribution:")
            for year, count in year_dist.items():
                print(f"         {year}: {count} movies")

        # Test sci-fi coverage
        if "is_science_fiction" in movie_data.columns:
            sci_fi_movies = movie_data[movie_data["is_science_fiction"] == 1]
            print(f"   🚀 Total sci-fi movies: {len(sci_fi_movies)}")

            sci_fi_2020s = sci_fi_movies[
                (sci_fi_movies["release_year"] >= 2020)
                & (sci_fi_movies["release_year"] <= 2024)
            ]
            print(f"   🚀 2020s sci-fi movies: {len(sci_fi_2020s)}")

            if len(sci_fi_2020s) > 0:
                print("      Sample 2020s sci-fi:")
                for i, movie in enumerate(
                    sci_fi_2020s[["title", "release_year"]].head(10).itertuples(), 1
                ):
                    print(f"         {i:2d}. {movie.title} ({movie.release_year})")

        print(
            f"\n🎯 SUCCESS! Database fix working - got {len(movie_data)} movies instead of 1000!"
        )

    except Exception as e:
        print(f"❌ Error testing fixed database: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_fixed_database()
