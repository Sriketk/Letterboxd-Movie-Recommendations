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
            num_recs=20,  # Get more recommendations
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
        print(f"📊 Total movies found: {len(recommendations['recommendations'])}")
        print()
        print("🎯 Top recommendations:")

        for i, movie in enumerate(
            recommendations["recommendations"].head(20).itertuples(), 1
        ):
            print(
                f"   {i:2d}. {movie.title} ({movie.release_year}) - Predicted Rating: {movie.predicted_rating}"
            )

        # Show some stats
        ratings = recommendations["recommendations"]["predicted_rating"].astype(float)
        print(f"\n📈 Rating Stats:")
        print(f"   Average predicted rating: {ratings.mean():.2f}")
        print(f"   Highest predicted rating: {ratings.max():.2f}")
        print(f"   Lowest predicted rating: {ratings.min():.2f}")

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
