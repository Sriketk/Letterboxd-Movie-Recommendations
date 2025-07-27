#!/usr/bin/env python3

import asyncio
import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing import database
from data_processing.utils import get_processed_user_df


async def debug_filtering_steps():
    print("🔍 DEBUGGING FILTERING STEP BY STEP")
    print("=" * 60)

    try:
        # Step 1: Get user data and movie data
        print("📊 Step 1: Loading user data and movie database...")
        processed_user_df, unrated, movie_data = await get_processed_user_df(
            user="sriketk"
        )

        print(f"   ✅ User rated movies: {len(processed_user_df)}")
        print(f"   ✅ Total movies in DB: {len(movie_data)}")
        print(f"   ✅ Unrated movies: {len(unrated)}")

        # Step 2: Find unseen movies (not rated by user)
        print("\n🎬 Step 2: Finding unseen movies...")
        initial_mask = (~movie_data["movie_id"].isin(processed_user_df["movie_id"])) & (
            ~movie_data["movie_id"].isin(unrated)
        )
        unseen = movie_data.loc[initial_mask].copy()
        print(f"   ✅ Unseen movies: {len(unseen)}")

        # Check 2020s sci-fi in unseen
        unseen_2020s_scifi = unseen[
            (unseen["release_year"] >= 2020)
            & (unseen["release_year"] <= 2024)
            & (unseen["is_science_fiction"] == 1)
        ]
        print(f"   📊 Unseen 2020s sci-fi: {len(unseen_2020s_scifi)}")
        if len(unseen_2020s_scifi) > 0:
            print("      Sample unseen 2020s sci-fi:")
            for i, movie in enumerate(
                unseen_2020s_scifi[["title", "release_year"]].head(5).itertuples(), 1
            ):
                print(f"         {i}. {movie.title} ({movie.release_year})")

        # Step 3: Apply genre filter
        print("\n🎭 Step 3: Applying genre filter (science_fiction)...")
        filter_mask = pd.Series(True, index=unseen.index)

        included_genres = ["is_science_fiction"]
        filter_mask &= unseen[included_genres].any(axis=1)

        after_genre_filter = unseen.loc[filter_mask]
        print(f"   ✅ After genre filter: {len(after_genre_filter)}")

        # Step 4: Apply special genre exclusions
        print("\n🚫 Step 4: Applying special genre exclusions...")
        special_genre_filters = {
            "animation": "is_animation",
            "horror": "is_horror",
            "documentary": "is_documentary",
        }

        for genre, col in special_genre_filters.items():
            if genre not in ["science_fiction"]:  # We only selected science_fiction
                before_count = filter_mask.sum()
                filter_mask &= unseen[col] == 0
                after_count = filter_mask.sum()
                print(
                    f"   📝 Excluding {genre}: {before_count} → {after_count} (-{before_count - after_count})"
                )

        after_special_exclusions = unseen.loc[filter_mask]
        print(f"   ✅ After exclusions: {len(after_special_exclusions)}")

        # Step 5: Apply content type filter
        print("\n📺 Step 5: Applying content type filter (movie)...")
        before_count = filter_mask.sum()
        filter_mask &= unseen["content_type"].isin(["movie"])
        after_count = filter_mask.sum()
        print(
            f"   📝 Content type filter: {before_count} → {after_count} (-{before_count - after_count})"
        )

        # Step 6: Apply year filter
        print("\n📅 Step 6: Applying year filter (2020-2024)...")
        before_count = filter_mask.sum()
        filter_mask &= (unseen["release_year"] >= 2020) & (
            unseen["release_year"] <= 2024
        )
        after_count = filter_mask.sum()
        print(
            f"   📝 Year filter: {before_count} → {after_count} (-{before_count - after_count})"
        )

        # Step 7: Apply runtime filter
        print("\n⏱️ Step 7: Applying runtime filter (60-300 min)...")
        before_count = filter_mask.sum()
        filter_mask &= (unseen["runtime"] >= 60) & (unseen["runtime"] <= 300)
        after_count = filter_mask.sum()
        print(
            f"   📝 Runtime filter: {before_count} → {after_count} (-{before_count - after_count})"
        )

        # Step 8: Apply popularity filter
        print("\n⭐ Step 8: Applying popularity filter (level 3)...")
        before_count = filter_mask.sum()

        popularity_map = {1: 1, 2: 0.7, 3: 0.4, 4: 0.2, 5: 0.1, 6: 0.05}
        threshold = np.percentile(
            unseen["letterboxd_rating_count"], 100 * (1 - popularity_map[3])
        )
        print(f"   📊 Popularity threshold (level 3): {threshold:.0f} rating count")

        filter_mask &= unseen["letterboxd_rating_count"] >= threshold
        after_count = filter_mask.sum()
        print(
            f"   📝 Popularity filter: {before_count} → {after_count} (-{before_count - after_count})"
        )

        # Final result
        final_movies = unseen.loc[filter_mask]
        print(f"\n🎯 FINAL RESULT: {len(final_movies)} movies")

        if len(final_movies) > 0:
            print("   🎬 Final sci-fi recommendations:")
            for i, movie in enumerate(
                final_movies[["title", "release_year", "letterboxd_rating_count"]]
                .head(10)
                .itertuples(),
                1,
            ):
                print(
                    f"      {i}. {movie.title} ({movie.release_year}) - {movie.letterboxd_rating_count} ratings"
                )
        else:
            print("   ❌ No movies survived all filters!")

            # Let's check what killed the 2020s sci-fi movies specifically
            print("\n🔍 DEBUGGING: What happened to known 2020s sci-fi movies?")

            # Get the 2020s sci-fi from the database
            all_2020s_scifi = movie_data[
                (movie_data["release_year"] >= 2020)
                & (movie_data["release_year"] <= 2024)
                & (movie_data["is_science_fiction"] == 1)
            ]

            print(f"   📊 Total 2020s sci-fi in DB: {len(all_2020s_scifi)}")

            for i, movie in enumerate(all_2020s_scifi.head(5).itertuples(), 1):
                movie_id = movie.movie_id
                title = movie.title
                year = movie.release_year
                rating_count = movie.letterboxd_rating_count

                # Check if user rated it
                user_rated = movie_id in processed_user_df["movie_id"].values
                unrated_movie = movie_id in unrated

                print(f"\n      {i}. {title} ({year})")
                print(f"         User rated: {user_rated}")
                print(f"         In unrated list: {unrated_movie}")
                print(
                    f"         Rating count: {rating_count} (threshold: {threshold:.0f})"
                )
                print(f"         Passes popularity filter: {rating_count >= threshold}")

    except Exception as e:
        print(f"❌ Error in debugging: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_filtering_steps())
