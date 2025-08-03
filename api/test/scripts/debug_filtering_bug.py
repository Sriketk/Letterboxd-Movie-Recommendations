#!/usr/bin/env python3

import asyncio
import sys
import os
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing.utils import get_processed_user_df


async def debug_filtering_bug():
    print("🔍 DEBUGGING FILTERING BUG")
    print("=" * 50)

    try:
        # Get user data
        print("📊 Loading user data...")
        processed_user_df, unrated, movie_data = await get_processed_user_df(
            user="sriketk"
        )

        # Focus on the problem movies
        problem_movies = ["Dune", "Everything Everywhere All at Once"]

        print(f"\n🎬 Checking problem movies:")

        for movie_title in problem_movies:
            print(f"\n🔍 Investigating: {movie_title}")

            # Find this movie in user's rated movies
            user_rated_match = processed_user_df[
                processed_user_df["title"].str.contains(
                    movie_title, case=False, na=False
                )
            ]

            if len(user_rated_match) > 0:
                print(f"   ✅ Found in user's ratings:")
                for _, movie in user_rated_match.iterrows():
                    print(f"      Title: {movie['title']}")
                    print(
                        f"      Movie ID: '{movie['movie_id']}' (type: {type(movie['movie_id'])})"
                    )
                    print(f"      URL: '{movie['url']}'")
                    print(f"      User Rating: {movie['user_rating']}")

                # Find this movie in the full database
                db_match = movie_data[
                    movie_data["title"].str.contains(movie_title, case=False, na=False)
                ]

                if len(db_match) > 0:
                    print(f"   ✅ Found in database:")
                    for _, movie in db_match.iterrows():
                        print(f"      Title: {movie['title']}")
                        print(
                            f"      Movie ID: '{movie['movie_id']}' (type: {type(movie['movie_id'])})"
                        )
                        print(f"      URL: '{movie['url']}'")

                    # Check if filtering should work
                    user_movie_id = str(user_rated_match.iloc[0]["movie_id"]).strip()
                    db_movie_id = str(db_match.iloc[0]["movie_id"]).strip()

                    print(f"\n   🔍 Filtering Check:")
                    print(f"      User movie_id: '{user_movie_id}'")
                    print(f"      DB movie_id: '{db_movie_id}'")
                    print(f"      IDs match: {user_movie_id == db_movie_id}")

                    # Check the filtering mask
                    user_movie_ids = (
                        processed_user_df["movie_id"].astype(str).str.strip()
                    )
                    db_movie_id_in_user_list = db_movie_id in user_movie_ids.values
                    print(f"      DB movie_id in user list: {db_movie_id_in_user_list}")

                    # Check if it's in unrated
                    unrated_ids = [str(uid).strip() for uid in unrated]
                    db_movie_id_in_unrated = db_movie_id in unrated_ids
                    print(f"      DB movie_id in unrated: {db_movie_id_in_unrated}")

                    # Manual mask check
                    should_be_excluded = (db_movie_id in user_movie_ids.values) or (
                        db_movie_id in unrated_ids
                    )
                    print(f"      Should be excluded: {should_be_excluded}")

                    if not should_be_excluded:
                        print(f"      ❌ BUG: Movie should be excluded but isn't!")

                        # Debug data types
                        print(f"\n   🔬 Data Type Analysis:")
                        print(
                            f"      processed_user_df movie_id dtype: {processed_user_df['movie_id'].dtype}"
                        )
                        print(
                            f"      movie_data movie_id dtype: {movie_data['movie_id'].dtype}"
                        )
                        print(
                            f"      unrated type: {type(unrated[0]) if unrated else 'empty'}"
                        )

                        # Check for exact match issues
                        print(f"\n   🎯 Exact Match Test:")
                        exact_matches = movie_data[
                            movie_data["movie_id"]
                            .astype(str)
                            .str.strip()
                            .isin(user_movie_ids)
                        ]
                        movie_found_in_exact = (
                            db_movie_id
                            in exact_matches["movie_id"].astype(str).str.strip().values
                        )
                        print(
                            f"      Movie found in exact match: {movie_found_in_exact}"
                        )
                else:
                    print(f"   ❌ Not found in database!")
            else:
                print(f"   ❌ Not found in user's ratings!")

        # Let's also check the actual filtering logic step by step
        print(f"\n🔍 MANUAL FILTERING TEST:")

        # Recreate the exact filtering from recommender.py
        initial_mask = (~movie_data["movie_id"].isin(processed_user_df["movie_id"])) & (
            ~movie_data["movie_id"].isin(unrated)
        )
        unseen = movie_data.loc[initial_mask].copy()

        print(f"   Total movies: {len(movie_data)}")
        print(f"   User rated: {len(processed_user_df)}")
        print(f"   Unrated: {len(unrated)}")
        print(f"   Unseen after filtering: {len(unseen)}")

        # Check if problem movies are in unseen
        for movie_title in problem_movies:
            problem_in_unseen = unseen[
                unseen["title"].str.contains(movie_title, case=False, na=False)
            ]
            if len(problem_in_unseen) > 0:
                print(
                    f"   ❌ {movie_title} found in unseen movies (should be filtered out)"
                )
            else:
                print(f"   ✅ {movie_title} correctly filtered out")

    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_filtering_bug())
