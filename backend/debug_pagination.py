#!/usr/bin/env python3

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from data_processing import database


def debug_pagination():
    print("🔍 DEBUGGING PAGINATION IN DETAIL")
    print("=" * 50)

    try:
        # Check table size
        table_size = database.get_table_size("movie_data")
        print(f"📊 Table size: {table_size}")

        # Clear cache first
        database.get_movie_data_cached.cache_clear()

        # Manually implement the same pagination logic
        batch_size = database.SUPABASE_MAX_ROWS
        print(f"📦 Batch size: {batch_size}")

        all_movie_data = []

        for offset in range(0, table_size, batch_size):
            print(
                f"\n🔄 Batch: offset={offset}, range={offset}-{offset + batch_size - 1}"
            )

            try:
                response = (
                    database.supabase.table("movie_data")
                    .select("*")
                    .range(offset, offset + batch_size - 1)
                    .execute()
                )

                batch_count = len(response.data) if response.data else 0
                print(f"   ✅ Retrieved: {batch_count} rows")

                if response and response.data:
                    all_movie_data.extend(response.data)
                    print(f"   📊 Total so far: {len(all_movie_data)} rows")

                    # Show some sample data from this batch
                    if len(response.data) > 0:
                        sample = response.data[0]
                        print(
                            f"   🎬 Sample: {sample.get('title', 'N/A')} ({sample.get('release_year', 'N/A')})"
                        )
                else:
                    print("   ❌ No data in response")
                    break

                # If we got less than expected, we might be at the end
                if batch_count < batch_size:
                    print(f"   🏁 End reached (got {batch_count} < {batch_size})")
                    break

            except Exception as e:
                print(f"   ❌ Error in batch: {e}")
                break

        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Expected: {table_size} rows")
        print(f"   Retrieved: {len(all_movie_data)} rows")
        print(f"   Success rate: {len(all_movie_data)/table_size*100:.1f}%")

        # If we're still missing data, let's try a different approach
        if len(all_movie_data) < table_size:
            print(
                f"\n🔍 ISSUE DETECTED: Missing {table_size - len(all_movie_data)} rows"
            )
            print("   Trying direct count query...")

            # Let's try getting a count with a different method
            count_response = (
                database.supabase.table("movie_data")
                .select("*", count="exact")
                .limit(0)
                .execute()
            )
            actual_count = count_response.count
            print(f"   Direct count query: {actual_count} rows")

            if actual_count != table_size:
                print(
                    f"   ⚠️  Table size mismatch! get_table_size() says {table_size}, but count says {actual_count}"
                )

    except Exception as e:
        print(f"❌ Error in pagination debug: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_pagination()
