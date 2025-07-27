#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing.utils import get_processed_user_df
from model.recommender import recommend_n_movies


async def check_already_seen():
    print("🔍 CHECKING IF ALGORITHM RECOMMENDS ALREADY SEEN MOVIES")
    print("=" * 60)

    try:
        # First, let's get the user's rated movies
        print("📊 Step 1: Getting sriketk's rated movies...")
        processed_user_df, unrated, movie_data = await get_processed_user_df(
            user="sriketk"
        )

        print(f"   ✅ User has rated: {len(processed_user_df)} movies")
        print(f"   ✅ User has unrated: {len(unrated)} movies")
        print(f"   ✅ Total in database: {len(movie_data)} movies")
        print(
            f"   ✅ Unseen movies: {len(movie_data) - len(processed_user_df) - len(unrated)}"
        )

        # Get some sample rated movies
        if len(processed_user_df) > 0:
            print("\n   📝 Sample rated movies:")
            sample_rated = processed_user_df[
                ["title", "release_year", "user_rating"]
            ].head(5)
            for i, movie in enumerate(sample_rated.itertuples(), 1):
                print(
                    f"      {i}. {movie.title} ({movie.release_year}) - Rated: {movie.user_rating}/5"
                )

        # Now get recommendations
        print("\n🚀 Step 2: Getting sci-fi recommendations...")
        recommendations = await recommend_n_movies(
            num_recs=10,
            user="sriketk",
            model_type="personalized",
            genres=["science_fiction"],
            content_types=["movie"],
            min_release_year=2020,
            max_release_year=2024,
            min_runtime=60,
            max_runtime=300,
            popularity=3,
        )

        recommended_movies = recommendations["recommendations"]
        print(f"   ✅ Got {len(recommended_movies)} recommendations")

        # Check each recommended movie against user's rated movies
        print("\n🔍 Step 3: Checking for overlap with rated movies...")

        # Get list of movie IDs and URLs user has rated
        rated_movie_ids = set(processed_user_df["movie_id"].astype(str).str.strip())
        rated_urls = set(processed_user_df["url"].astype(str).str.strip())
        unrated_movie_ids = set(str(mid) for mid in unrated)

        print(f"   📊 User rated movie IDs: {len(rated_movie_ids)}")
        print(f"   📊 User unrated movie IDs: {len(unrated_movie_ids)}")

        overlap_found = False

        for i, movie in enumerate(recommended_movies.itertuples(), 1):
            movie_id = (
                str(movie.movie_id).strip() if hasattr(movie, "movie_id") else "N/A"
            )
            url = str(movie.url).strip() if hasattr(movie, "url") else "N/A"
            title = movie.title
            year = movie.release_year
            predicted_rating = movie.predicted_rating

            # Check if this movie was already rated
            already_rated_by_id = movie_id in rated_movie_ids
            already_rated_by_url = url in rated_urls
            is_unrated = movie_id in unrated_movie_ids

            status = "✅ UNSEEN"
            if already_rated_by_id or already_rated_by_url:
                status = "❌ ALREADY RATED"
                overlap_found = True
            elif is_unrated:
                status = "⚠️ IN UNRATED LIST"
                overlap_found = True

            print(f"   {i:2d}. {title} ({year}) - {predicted_rating} {status}")

            if already_rated_by_id or already_rated_by_url:
                # Find the user's actual rating
                if already_rated_by_id:
                    user_rating = processed_user_df[
                        processed_user_df["movie_id"].astype(str).str.strip()
                        == movie_id
                    ]["user_rating"].iloc[0]
                else:
                    user_rating = processed_user_df[
                        processed_user_df["url"].astype(str).str.strip() == url
                    ]["user_rating"].iloc[0]
                print(f"       🎯 User's actual rating: {user_rating}/5")

        # Summary
        print(f"\n🎯 FILTERING ANALYSIS:")
        if overlap_found:
            print("   ❌ PROBLEM: Algorithm recommended movies user has already seen!")
            print("   🐛 This indicates a bug in the filtering logic")
        else:
            print("   ✅ SUCCESS: All recommendations are unseen movies")
            print("   🎯 Filtering working correctly")

        # Let's also check if any sci-fi movies from 2020s were excluded correctly
        print(f"\n🔍 BONUS: Checking what 2020s sci-fi movies user HAS rated...")
        user_rated_2020s_scifi = processed_user_df[
            (processed_user_df["release_year"] >= 2020)
            & (processed_user_df["release_year"] <= 2024)
            & (processed_user_df["is_science_fiction"] == 1)
        ]

        if len(user_rated_2020s_scifi) > 0:
            print(
                f"   📊 User has rated {len(user_rated_2020s_scifi)} 2020s sci-fi movies:"
            )
            for i, movie in enumerate(
                user_rated_2020s_scifi[
                    ["title", "release_year", "user_rating"]
                ].itertuples(),
                1,
            ):
                print(
                    f"      {i}. {movie.title} ({movie.release_year}) - Rated: {movie.user_rating}/5"
                )
            print("   ✅ These were correctly excluded from recommendations")
        else:
            print("   📊 User has not rated any 2020s sci-fi movies")

    except Exception as e:
        print(f"❌ Error checking already seen: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_already_seen())
