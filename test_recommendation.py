#!/usr/bin/env python3

import asyncio
import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from model.recommender import recommend_n_movies


async def test_recommendation():
    print("🎬 Testing recommendation system...")
    print("📋 Request parameters:")
    print("   Username: sriketk")
    print("   Genres: adventure")
    print("   Years: 1990-1999")
    print("   Content type: movie")
    print("   Popularity: 3 (semi-popular)")
    print("   Runtime: 60-300 minutes")
    print()

    start_time = time.perf_counter()

    try:
        recommendations = await recommend_n_movies(
            num_recs=10,  # Just get 10 for testing
            user="sriketk",
            model_type="personalized",
            genres=["adventure"],
            content_types=["movie"],
            min_release_year=1990,
            max_release_year=1999,
            min_runtime=60,
            max_runtime=300,
            popularity=3,
        )

        end_time = time.perf_counter()

        print(f"✅ SUCCESS! Got recommendations in {end_time - start_time:.2f} seconds")
        print()
        print("🎯 Top recommendations:")

        for i, movie in enumerate(
            recommendations["recommendations"].head(10).itertuples(), 1
        ):
            print(
                f"   {i}. {movie.title} ({movie.release_year}) - Predicted Rating: {movie.predicted_rating}"
            )

    except Exception as e:
        end_time = time.perf_counter()
        print(f"❌ ERROR after {end_time - start_time:.2f} seconds:")
        print(f"   {type(e).__name__}: {str(e)}")

        # Print detailed traceback for debugging
        import traceback

        print("\n🔍 Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_recommendation())
