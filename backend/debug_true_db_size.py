#!/usr/bin/env python3

import sys
import os
import pandas as pd
from tqdm import tqdm

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing import database


def check_true_database_size():
    print("🔍 CHECKING TRUE DATABASE SIZE")
    print("=" * 50)

    try:
        # Method 1: Check table size directly
        print("📊 Method 1: Checking table size...")
        table_size = database.get_table_size("movie_data")
        print(f"   ✅ Total rows in movie_data table: {table_size}")

        # Method 2: Use the cached function (limited)
        print("\n📊 Method 2: Using cached get_movie_data()...")
        cached_data = database.get_movie_data()
        print(f"   ✅ Cached function returns: {len(cached_data)} rows")

        # Method 3: Direct query with pagination (like other functions do)
        print("\n📊 Method 3: Direct query with proper pagination...")

        # Use the same pattern as get_user_ratings()
        batch_size = 10000  # Smaller batches to be safe
        all_movie_data = []

        print(f"   Loading {table_size} rows in batches of {batch_size}...")

        for offset in tqdm(range(0, table_size, batch_size), desc="Loading movie data"):
            try:
                response = (
                    database.supabase.table("movie_data")
                    .select("*")
                    .range(
                        offset, offset + batch_size - 1
                    )  # Supabase range is inclusive
                    .execute()
                )

                if response and response.data:
                    all_movie_data.extend(response.data)
                    print(
                        f"      Batch {offset//batch_size + 1}: {len(response.data)} rows"
                    )
                else:
                    print(f"      Batch {offset//batch_size + 1}: No data returned")

            except Exception as e:
                print(f"      ❌ Error in batch {offset//batch_size + 1}: {e}")
                break

        print(f"\n   ✅ Total rows retrieved with pagination: {len(all_movie_data)}")

        # Convert to DataFrame and analyze
        if all_movie_data:
            full_movie_df = pd.DataFrame.from_records(all_movie_data)

            print("\n📈 Full Database Analysis:")
            print(f"   Total movies: {len(full_movie_df)}")

            if "release_year" in full_movie_df.columns:
                print(
                    f"   Release years: {full_movie_df['release_year'].min()} - {full_movie_df['release_year'].max()}"
                )

                # 2020s analysis
                movies_2020s = full_movie_df[
                    (full_movie_df["release_year"] >= 2020)
                    & (full_movie_df["release_year"] <= 2024)
                ]
                print(f"   2020s movies: {len(movies_2020s)}")

                if len(movies_2020s) > 0:
                    year_dist = movies_2020s["release_year"].value_counts().sort_index()
                    print("   2020s distribution:")
                    for year, count in year_dist.items():
                        print(f"      {year}: {count} movies")

            # Check sci-fi
            if "is_science_fiction" in full_movie_df.columns:
                sci_fi_movies = full_movie_df[full_movie_df["is_science_fiction"] == 1]
                print(f"   Total sci-fi movies: {len(sci_fi_movies)}")

                sci_fi_2020s = sci_fi_movies[
                    (sci_fi_movies["release_year"] >= 2020)
                    & (sci_fi_movies["release_year"] <= 2024)
                ]
                print(f"   2020s sci-fi movies: {len(sci_fi_2020s)}")

                if len(sci_fi_2020s) > 0:
                    print("   Sample 2020s sci-fi:")
                    for i, movie in enumerate(
                        sci_fi_2020s[["title", "release_year"]].head(10).itertuples(), 1
                    ):
                        print(f"      {i:2d}. {movie.title} ({movie.release_year})")

            # Show the difference
            print(f"\n🎯 KEY FINDING:")
            print(f"   Cached function limit: {len(cached_data)} rows")
            print(f"   True database size: {len(full_movie_df)} rows")
            print(
                f"   Missing data: {len(full_movie_df) - len(cached_data)} rows ({((len(full_movie_df) - len(cached_data))/len(full_movie_df)*100):.1f}%)"
            )

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_true_database_size()
