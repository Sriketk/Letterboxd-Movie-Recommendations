#!/usr/bin/env python3

import asyncio
import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from model.recommender import recommend_n_movies


async def test_romance_mid2000s():
    print("💕 Testing Romance Movies from Mid 2000s...")
    print("📋 Request parameters:")
    print("   Username: sriketk")
    print("   Genres: romance")
    print("   Years: 2003-2007 (mid 2000s)")
    print("   Content type: movie")
    print("   Popularity: 3 (semi-popular)")
    print("   Runtime: 60-300 minutes")
    print()

    start_time = time.perf_counter()

    try:
        recommendations = await recommend_n_movies(
            num_recs=20,  # Get more recommendations for variety
            user="sriketk",
            model_type="personalized",
            genres=["romance"],
            content_types=["movie"],
            min_release_year=2003,
            max_release_year=2007,
            min_runtime=60,
            max_runtime=300,
            popularity=3,
        )

        end_time = time.perf_counter()

        print(f"✅ SUCCESS! Got recommendations in {end_time - start_time:.2f} seconds")
        print(
            f"📊 Total romance movies found: {len(recommendations['recommendations'])}"
        )
        print()
        print("💕 Top romance recommendations:")

        for i, movie in enumerate(
            recommendations["recommendations"].head(20).itertuples(), 1
        ):
            print(
                f"   {i:2d}. {movie.title} ({movie.release_year}) - Predicted Rating: {movie.predicted_rating}"
            )

        # Show some stats
        if len(recommendations["recommendations"]) > 0:
            ratings = recommendations["recommendations"]["predicted_rating"].astype(
                float
            )
            print(f"\n📈 Rating Stats:")
            print(f"   Average predicted rating: {ratings.mean():.2f}")
            print(f"   Highest predicted rating: {ratings.max():.2f}")
            print(f"   Lowest predicted rating: {ratings.min():.2f}")

        # Show year distribution
        if len(recommendations["recommendations"]) > 0:
            year_counts = (
                recommendations["recommendations"]["release_year"]
                .value_counts()
                .sort_index()
            )
            print(f"\n📅 Year Distribution:")
            for year, count in year_counts.items():
                print(f"   {year}: {count} movies")

        # Show some sample titles to validate genre
        if len(recommendations["recommendations"]) > 0:
            print(f"\n🎬 Sample Titles (to verify romance genre):")
            sample_titles = recommendations["recommendations"]["title"].head(5).tolist()
            for i, title in enumerate(sample_titles, 1):
                print(f"   {i}. {title}")

    except Exception as e:
        end_time = time.perf_counter()
        print(f"❌ ERROR after {end_time - start_time:.2f} seconds:")
        print(f"   {type(e).__name__}: {str(e)}")

        # Print detailed traceback for debugging
        import traceback

        print("\n🔍 Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_romance_mid2000s())
