import aiohttp
import argparse
import asyncio
from bs4 import BeautifulSoup
import json
import os
import pandas as pd
import re
import requests
import sys
import time
from typing import Any, Dict, Sequence, Tuple

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import data_processing.database as database
from data_processing.arg_checks import check_num_movies_argument_type


# Encodes genres as integers
def encode_genres(genres: Sequence[str]) -> int:

    genre_options = [
        "action",
        "adventure",
        "animation",
        "comedy",
        "crime",
        "documentary",
        "drama",
        "family",
        "fantasy",
        "history",
        "horror",
        "music",
        "mystery",
        "romance",
        "science_fiction",
        "tv_movie",
        "thriller",
        "war",
        "western",
    ]

    genre_binary = ""
    for genre in genre_options:
        if genre in genres:
            genre_binary += "1"
        else:
            genre_binary += "0"

    genre_int = int(genre_binary, 2)

    return genre_int


# Maps country of origin to numerical values
def assign_countries(country_of_origin: str) -> int:

    country_map = {
        "USA": 0,
        "UK": 1,
        "China": 2,
        "France": 3,
        "Japan": 4,
        "Germany": 5,
        "South Korea": 6,
        "Canada": 7,
        "India": 8,
        "Austrailia": 9,
        "Hong Kong": 10,
        "Italy": 11,
        "Spain": 12,
        "Brazil": 13,
        "USSR": 14,
    }

    return country_map.get(country_of_origin, len(country_map))


# Adds boolean genre columns from encoded genres integer
def add_genre_boolean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Populates boolean genre columns from the encoded genres integer"""

    genre_options = [
        "action",
        "adventure",
        "animation",
        "comedy",
        "crime",
        "documentary",
        "drama",
        "family",
        "fantasy",
        "history",
        "horror",
        "music",
        "mystery",
        "romance",
        "science_fiction",
        "tv_movie",
        "thriller",
        "war",
        "western",
    ]

    # Initialize all boolean columns to 0
    for genre in genre_options:
        df[f"is_{genre}"] = 0

    # Populate boolean columns from encoded genres
    for idx, row in df.iterrows():
        genres_int = row["genres"]
        if pd.isna(genres_int) or genres_int == 0:
            continue

        # Convert to binary and pad to 19 characters
        genre_binary = bin(int(genres_int))[2:].zfill(19)

        # Set boolean columns
        for i, genre in enumerate(genre_options):
            df.loc[idx, f"is_{genre}"] = int(genre_binary[i])

    return df


# Scrapes movie data
async def movie_crawl(
    movie_urls: pd.DataFrame,
    session: aiohttp.ClientSession,
    show_objects: bool,
    update_movie_data: bool,
    verbose: bool = False,
    batch_num: int = 1,
    total_batches: int = 1,
) -> Tuple[int, int, int, int]:

    movie_data = []
    deprecated_urls = []
    total_movies = len(movie_urls)
    successful_scrapes = 0
    failed_scrapes = 0

    print(f"🎬 Batch {batch_num}/{total_batches}: Processing {total_movies} movies...")

    for idx, (_, row) in enumerate(movie_urls.iterrows()):
        movie_num = idx + 1
        start_time = time.perf_counter()

        result, is_deprecated = await get_letterboxd_data(
            row=row, session=session, verbose=verbose
        )

        end_time = time.perf_counter()
        scrape_time = end_time - start_time

        if result:
            movie_data.append(result)
            successful_scrapes += 1
            status = "✅"
            title = result.get("title", "Unknown")
        else:
            failed_scrapes += 1
            status = "❌"
            title = row.get("movie_id", "Unknown")

        if is_deprecated:
            deprecated_urls.append({"movie_id": row["movie_id"], "url": row["url"]})
            status += " (deprecated)"

        # Calculate speed and ETA
        elapsed_total = time.perf_counter() - start_time if idx == 0 else None
        if movie_num > 1:
            avg_time_per_movie = (
                (time.perf_counter() - start_time) / movie_num
                if idx == 0
                else scrape_time
            )
            remaining_movies = total_movies - movie_num
            eta_seconds = (
                remaining_movies * avg_time_per_movie if avg_time_per_movie else 0
            )
            eta_str = (
                f", ETA: {eta_seconds:.0f}s"
                if eta_seconds > 0 and remaining_movies > 0
                else ""
            )
        else:
            eta_str = ""

        # Progress logging
        progress_pct = (movie_num / total_movies) * 100
        print(
            f"  [{movie_num}/{total_movies}] ({progress_pct:.1f}%) {status} {title[:40]}{'...' if len(title) > 40 else ''} ({scrape_time:.1f}s){eta_str}"
        )

        if show_objects and result:
            print(f"    📋 Data: {result}")

    # Processes movie data
    movie_data_df = pd.DataFrame(movie_data)
    if not movie_data_df.empty:
        print(f"  🔧 Processing {len(movie_data_df)} scraped movies...")
        movie_data_df["genres"] = movie_data_df["genres"].apply(
            lambda genres: [genre.lower().replace(" ", "_") for genre in genres]
        )
        movie_data_df["genres"] = movie_data_df["genres"].apply(encode_genres)
        movie_data_df["country_of_origin"] = movie_data_df["country_of_origin"].apply(
            assign_countries
        )

        # Add boolean genre columns
        print(f"  🏷️  Adding genre boolean columns...")
        movie_data_df = add_genre_boolean_columns(movie_data_df)

    num_updates = 0
    num_success_batches = 0
    num_failure_batches = 0
    num_deprecated_marked = 0

    # Updates movie data and genres in database
    if update_movie_data:
        try:
            if not movie_data_df.empty:
                print(f"  💾 Saving {len(movie_data_df)} movies to database...")
                database.update_movie_data(movie_data_df=movie_data_df)
                num_updates = len(movie_data_df)
                print(f"  ✅ Successfully saved {num_updates} movies to database")

                # Clean up: Delete successfully scraped URLs
                scraped_movie_ids = movie_data_df["movie_id"].tolist()
                print(f"  🗑️  Cleaning up {len(scraped_movie_ids)} scraped URLs...")
                database.delete_scraped_movie_urls(scraped_movie_ids)
                print(
                    f"  ✅ Successfully removed {len(scraped_movie_ids)} URLs from scraping queue"
                )
            else:
                print(f"  ⚠️  No movie data to save to database")

            num_success_batches = 1

        except Exception as e:
            print(f"  ❌ Failed to save movies to database: {e}")
            num_failure_batches = 1

        if deprecated_urls:
            deprecated_df = pd.DataFrame(deprecated_urls)
            try:
                print(f"  🗑️  Marking {len(deprecated_df)} URLs as deprecated...")
                database.mark_movie_urls_deprecated(deprecated_df=deprecated_df)
                num_deprecated_marked = len(deprecated_df)
                print(
                    f"  ✅ Successfully marked {num_deprecated_marked} URLs as deprecated"
                )
            except Exception as e:
                print(f"  ❌ Failed to mark deprecated URLs: {e}")
        else:
            print(f"  ℹ️  No deprecated URLs found in this batch")
    else:
        print(f"  🚫 Skipping database update (update_movie_data=False)")

    print(
        f"  📈 Batch {batch_num} summary: {successful_scrapes} ✅, {failed_scrapes} ❌, {len(deprecated_urls)} deprecated"
    )
    return num_success_batches, num_updates, num_failure_batches, num_deprecated_marked


# Gets Letterboxd data
async def get_letterboxd_data(
    row: pd.DataFrame, session: aiohttp.ClientSession, verbose: bool
) -> Tuple[Dict[str, Any] | None, bool]:

    movie_id = row["movie_id"]  # ID
    url = row["url"]  # URL

    # Scrapes relevant Letterboxd data from each page if possible
    try:
        # Add small delay to be respectful to Letterboxd's servers
        await asyncio.sleep(0.5)
        async with session.get("https://letterboxd.com" + url, timeout=60) as response:

            # Checks is URL is not found
            if response.status == 404 or response.status == 410:
                print(f"URL deprecated: {url} - status code: {response.status}")

                return None, True
            elif response.status != 200:
                print(f"Failed to fetch {url} - status code:", response.status)

                return None, False

            soup = BeautifulSoup(await response.text(), "html.parser")
            script = str(soup.find("script", {"type": "application/ld+json"}))
            script = script[52:-20]  # Trimmed to useful json data
            try:
                webData = json.loads(script)
            except Exception as e:
                print(f"Error while scraping {url} (JSON parsing): {e}")

                return None, False

            try:
                title = webData["name"]  # Title
                if verbose:
                    print(f"Scraping {title}")
                release_year = int(
                    webData["releasedEvent"][0]["startDate"]
                )  # Release year
                runtime = int(
                    re.search(
                        r"(\d+)\s+mins", soup.find("p", {"class": "text-footer"}).text
                    ).group(1)
                )  # Runtime
                rating = webData["aggregateRating"]["ratingValue"]  # Letterboxd rating
                rating_count = webData["aggregateRating"][
                    "ratingCount"
                ]  # Letterboxd rating count
                genre = webData["genre"]  # Genres
                country = webData["countryOfOrigin"][0]["name"]  # Country of origin
                poster = webData["image"]  # Poster
            except asyncio.TimeoutError:
                # Catches timeout
                print(f"Failed to scrape - timed out")

                return None, False
            except aiohttp.ClientOSError as e:
                print("Connection terminated by Letterboxd")
                raise e
            except:
                # Catches movies with missing data
                print(f"Failed to scrape {title} - missing data")

                return None, False

            try:
                tmdb_url = soup.find("a", {"data-track-action": "TMDB"})["href"]
                if "/movie/" in tmdb_url:  # Content type
                    content_type = "movie"
                else:
                    content_type = "tv"
            except Exception as e:
                # Catches movies missing content type
                print(f"Failed to scrape {title} - missing content type")

                return None, False

        return {
            "movie_id": movie_id,
            "url": url,
            "title": title,
            "content_type": content_type,
            "release_year": release_year,
            "runtime": runtime,
            "letterboxd_rating": rating,
            "letterboxd_rating_count": rating_count,
            "genres": genre,
            "country_of_origin": country,
            "poster": poster,
        }, False
    except aiohttp.ClientOSError as e:
        print(f"Connection terminated by Letterboxd for {url}: {e}")
        raise e
    except asyncio.TimeoutError:
        print(f"Failed to scrape {url} - timed out")

        return None, False
    except Exception as e:
        print(f"Failed to scrape {url} - {e}")

        return None, False


async def main(
    clear_movie_data_cache: bool,
    num_movies: str | int,
    show_objects: bool,
    movie_url: str | None,
    update_movie_data: bool,
) -> None:

    start = time.perf_counter()

    # Gets movie URLs
    all_movie_urls = database.get_movie_urls()

    # Filter out deprecated URLs
    all_movie_urls = all_movie_urls[all_movie_urls["is_deprecated"] == False]

    # NEW: Remove URLs for movies that are already in movie_data to avoid re-scraping
    try:
        existing_movie_ids = set(database.get_raw_movie_data()["movie_id"].tolist())
        before_filter = len(all_movie_urls)
        all_movie_urls = all_movie_urls[
            ~all_movie_urls["movie_id"].isin(existing_movie_ids)
        ]
        # Drop any accidental duplicate movie_id rows
        all_movie_urls = all_movie_urls.drop_duplicates(subset=["movie_id"])
        after_filter = len(all_movie_urls)
        print(
            f"🔍 Filtered out {before_filter - after_filter} already-scraped movies; {after_filter} URLs remain in queue"
        )
    except Exception as e:
        print(f"⚠️  Could not filter existing movies: {e}")

    if movie_url is not None:
        # Trims URL to match database format
        movie_url = movie_url.replace("https://letterboxd.com", "")

        # Adds trailing slash if necessary
        if not movie_url.endswith("/"):
            movie_url += "/"

        movie_urls = all_movie_urls[all_movie_urls["url"] == movie_url]
        if len(movie_urls) == 0:
            print("Movie url not in database")
    elif num_movies == "all":
        movie_urls = all_movie_urls
    else:
        movie_urls = all_movie_urls[:num_movies]

    # Creates URL batches
    batch_size = 500
    url_batches = [
        movie_urls.iloc[i : i + batch_size]
        for i in range(0, len(movie_urls), batch_size)
    ]

    # Processes each batch asynchronously
    session_refresh = 5
    results = []

    total_movies = len(movie_urls)
    total_batches = len(url_batches)
    print(f"\n🚀 Starting movie scraping process:")
    print(f"   📊 Total movies to scrape: {total_movies}")
    print(f"   📦 Total batches: {total_batches}")
    print(f"   🔄 Session refresh every {session_refresh} batches")
    print(f"   ⚡ Batch size: {batch_size} movies per batch\n")

    # Set proper headers to avoid being blocked by Letterboxd
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    session_num = 0
    for i in range(0, len(url_batches), session_refresh):
        session_num += 1
        batches_in_session = url_batches[i : i + session_refresh]
        movies_in_session = sum(len(batch) for batch in batches_in_session)

        print(
            f"🔗 Session {session_num}: Starting HTTP session for {len(batches_in_session)} batches ({movies_in_session} movies)"
        )

        connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        async with aiohttp.ClientSession(
            headers=headers, connector=connector, timeout=timeout
        ) as session:
            tasks = [
                movie_crawl(
                    movie_urls=batch,
                    session=session,
                    show_objects=show_objects,
                    update_movie_data=update_movie_data,
                    verbose=False,
                    batch_num=(i // session_refresh) * session_refresh + batch_idx + 1,
                    total_batches=total_batches,
                )
                for batch_idx, batch in enumerate(batches_in_session)
            ]
            session_results = await asyncio.gather(*tasks)
            results.extend(session_results)

        print(f"✅ Session {session_num} completed\n")

    if update_movie_data:
        num_success_batches = sum([r[0] for r in results])
        num_updates = sum([r[1] for r in results])
        num_failure_batches = sum([r[2] for r in results])
        num_deprecated = sum([r[3] for r in results])

        print(f"🎯 SCRAPING COMPLETE!")
        print(f"═══════════════════════════════════════")
        print(f"📊 Total movies processed: {total_movies}")
        print(f"✅ Successfully saved: {num_updates} movies")
        print(f"📦 Successful batches: {num_success_batches}")
        print(f"❌ Failed batches: {num_failure_batches}")
        print(f"🗑️  Deprecated URLs found: {num_deprecated}")
        if num_updates > 0:
            success_rate = (num_updates / total_movies) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")

        # Show remaining URLs in queue
        try:
            remaining_urls = database.get_table_size("movie_urls")
            print(f"📋 URLs remaining in queue: {remaining_urls}")
        except:
            pass
    else:
        print(f"🚫 Database update was disabled - no movies saved")

    finish = time.perf_counter()
    total_time = finish - start
    movies_per_second = total_movies / total_time if total_time > 0 else 0
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(f"🚀 Average speed: {movies_per_second:.2f} movies/second")
    print(f"═══════════════════════════════════════\n")

    # Clears movie data cache
    if clear_movie_data_cache:
        try:
            url = f'{os.getenv("BACKEND_URL")}/api/admin/clear-movie-data-cache'
            headers = {"Authorization": f'Bearer {os.getenv("ADMIN_SECRET_KEY")}'}
            requests.post(url=url, headers=headers)
            print("Successfully cleared movie data cache")
        except Exception as e:
            print("Failed to clear movie data cache")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Clear movie data cache
    parser.add_argument(
        "-c",
        "--clear-movie-data-cache",
        help="Clears the movie data cache.",
        action="store_true",
    )

    # Number of movies
    parser.add_argument(
        "-n",
        "--num_movies",
        type=check_num_movies_argument_type,
        help="Specifies the first n movies to scrape.",
        default="all",
    )

    # Show movie data object
    parser.add_argument(
        "-o",
        "--show-objects",
        help="Displays the movie data objects.",
        action="store_true",
    )

    # Scrape movie url
    parser.add_argument(
        "-l",
        "--movie_url",
        help="Specifies the URL of the movie to scrape.",
        default=None,
    )

    # Update movie data
    parser.add_argument(
        "-u",
        "--update-movie-data",
        help="Updates the movie data in the database.",
        action="store_true",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            clear_movie_data_cache=args.clear_movie_data_cache,
            num_movies=args.num_movies,
            show_objects=args.show_objects,
            movie_url=args.movie_url,
            update_movie_data=args.update_movie_data,
        )
    )
