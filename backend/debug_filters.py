#!/usr/bin/env python3

import asyncio
import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from model.recommender import recommend_n_movies


async def test_filters():
    print("🔍 DEBUGGING FILTER IMPACT")
    print("=" * 50)

    # Test different combinations to see what's limiting results
    tests = [
        {
            "name": "🎯 Original Request",
            "params": {
                "genres": ["adventure"],
                "min_release_year": 1990,
                "max_release_year": 1999,
                "popularity": 3,
            },
        },
        {
            "name": "🌟 More Popular (level 2)",
            "params": {
                "genres": ["adventure"],
                "min_release_year": 1990,
                "max_release_year": 1999,
                "popularity": 2,
            },
        },
        {
            "name": "📅 Broader Years (1985-2005)",
            "params": {
                "genres": ["adventure"],
                "min_release_year": 1985,
                "max_release_year": 2005,
                "popularity": 3,
            },
        },
        {
            "name": "🎬 All Adventure (any year)",
            "params": {
                "genres": ["adventure"],
                "min_release_year": 1980,
                "max_release_year": 2024,
                "popularity": 4,
            },
        },
        {
            "name": "🎭 Multiple Genres",
            "params": {
                "genres": ["adventure", "action", "drama"],
                "min_release_year": 1990,
                "max_release_year": 1999,
                "popularity": 3,
            },
        },
    ]

    for test in tests:
        print(f"\n{test['name']}")
        print("-" * 30)

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
                top_3 = recommendations["recommendations"].head(3)
                for i, movie in enumerate(top_3.itertuples(), 1):
                    print(
                        f"      {i}. {movie.title} ({movie.release_year}) - {movie.predicted_rating}"
                    )
            else:
                print("      No movies found!")

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_filters())
