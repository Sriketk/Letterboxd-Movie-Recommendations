#!/usr/bin/env python3

import asyncio
import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from model.recommender import recommend_n_movies


async def debug_scifi():
    print("🔍 DEBUGGING SCI-FI RECOMMENDATIONS")
    print("=" * 50)

    # Test different combinations to understand the limitation
    tests = [
        {
            "name": "🚀 2020s Sci-Fi (Original)",
            "params": {
                "genres": ["science_fiction"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 3,
            },
        },
        {
            "name": "🌟 2020s Sci-Fi (More Popular)",
            "params": {
                "genres": ["science_fiction"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 1,  # Most popular
            },
        },
        {
            "name": "🎭 2020s Sci-Fi (Very Obscure)",
            "params": {
                "genres": ["science_fiction"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 6,  # Most obscure
            },
        },
        {
            "name": "📅 2010s Sci-Fi",
            "params": {
                "genres": ["science_fiction"],
                "min_release_year": 2010,
                "max_release_year": 2019,
                "popularity": 3,
            },
        },
        {
            "name": "🎬 All Years Sci-Fi",
            "params": {
                "genres": ["science_fiction"],
                "min_release_year": 1980,
                "max_release_year": 2024,
                "popularity": 3,
            },
        },
        {
            "name": "🎪 2020s Multiple Genres",
            "params": {
                "genres": ["science_fiction", "action", "thriller"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "popularity": 3,
            },
        },
    ]

    for test in tests:
        print(f"\n{test['name']}")
        print("-" * 40)

        try:
            start_time = time.perf_counter()

            recommendations = await recommend_n_movies(
                num_recs=15,
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
                top_5 = recommendations["recommendations"].head(5)
                for i, movie in enumerate(top_5.itertuples(), 1):
                    print(
                        f"      {i}. {movie.title} ({movie.release_year}) - {movie.predicted_rating}"
                    )
            else:
                print("      No movies found!")

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")


if __name__ == "__main__":
    asyncio.run(debug_scifi())
