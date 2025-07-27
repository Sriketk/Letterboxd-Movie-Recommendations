#!/usr/bin/env python3

import asyncio
import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from model.recommender import recommend_n_movies


async def check_2020s_content():
    print("📊 CHECKING 2020s MOVIE DATABASE COVERAGE")
    print("=" * 50)

    # Test what's actually available from 2020s
    tests = [
        {
            "name": "🎬 All 2020s Movies (Any Genre)",
            "params": {
                "genres": [
                    "action",
                    "adventure",
                    "animation",
                    "comedy",
                    "crime",
                    "documentary",
                    "drama",
                    "family",
                    "fantasy",
                    "history",
                    "horror",
                    "music",
                    "mystery",
                    "romance",
                    "science_fiction",
                    "thriller",
                    "war",
                    "western",
                ],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 6,  # Most inclusive
            },
        },
        {
            "name": "🎭 2020s Drama Movies",
            "params": {
                "genres": ["drama"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 4,
            },
        },
        {
            "name": "🎪 2020s Action Movies",
            "params": {
                "genres": ["action"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 4,
            },
        },
        {
            "name": "🚀 Any Sci-Fi (2015-2024)",
            "params": {
                "genres": ["science_fiction"],
                "min_release_year": 2015,
                "max_release_year": 2024,
                "popularity": 6,
            },
        },
    ]

    for test in tests:
        print(f"\n{test['name']}")
        print("-" * 40)

        try:
            start_time = time.perf_counter()

            recommendations = await recommend_n_movies(
                num_recs=20,
                user="sriketk",
                model_type="personalized",
                content_types=["movie"],
                min_runtime=60,
                max_runtime=300,
                **test["params"],
            )

            end_time = time.perf_counter()
            count = len(recommendations["recommendations"])

            print(f"   ✅ Found {count} movies in {end_time - start_time:.2f}s")

            if count > 0:
                movies = recommendations["recommendations"].head(10)
                for i, movie in enumerate(movies.itertuples(), 1):
                    print(
                        f"      {i:2d}. {movie.title} ({movie.release_year}) - {movie.predicted_rating}"
                    )

                # Show year distribution for this test
                year_counts = (
                    recommendations["recommendations"]["release_year"]
                    .value_counts()
                    .sort_index()
                )
                print(f"\n      📅 Year breakdown:")
                for year, count in year_counts.items():
                    print(f"         {year}: {count} movies")
            else:
                print("      No movies found!")

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")


if __name__ == "__main__":
    asyncio.run(check_2020s_content())
