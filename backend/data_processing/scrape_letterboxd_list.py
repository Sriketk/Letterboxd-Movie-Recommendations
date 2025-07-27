import aiohttp
import argparse
import asyncio
from bs4 import BeautifulSoup
from bs4.element import Tag
import os
import sys
from typing import Any, Dict, Sequence
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import data_processing.database as database


class ListEmptyException(Exception):
    pass


# Gets movies from any Letterboxd list
async def get_letterboxd_list(
    list_url: str, session: aiohttp.ClientSession = None
) -> Sequence[str]:
    """
    Scrapes a Letterboxd list and returns movie URLs

    Args:
        list_url: Full URL to the Letterboxd list (e.g., https://letterboxd.com/username/list/list-name/)
        session: aiohttp session for making requests

    Returns:
        List of movie URLs from the list
    """

    # Scrapes a single list page
    async def fetch_list_page(page_number: int) -> Sequence[str]:
        # Handle pagination by appending /page/X to the URL
        if page_number == 1:
            page_url = list_url.rstrip("/")
        else:
            page_url = f"{list_url.rstrip('/')}/page/{page_number}"

        print(f"Scraping: {page_url}")

        async with session.get(page_url) as page:
            if page.status != 200:
                print(f"Error {page.status} accessing {page_url}")
                return []

            soup = BeautifulSoup(await page.text(), "html.parser")

            # Look for movie poster containers (same as watchlist)
            movies = soup.select("li.poster-container")

            if not movies:
                # Try alternative selectors for different list layouts
                movies = soup.select(".film-poster")
                if not movies:
                    movies = soup.select(".poster")

            print(f"Found {len(movies)} movies on page {page_number}")
            return [get_url(movie=movie) for movie in movies if get_url(movie)]

    movie_urls = []
    page_number = 1

    while True:
        data = await fetch_list_page(page_number=page_number)
        if not data:  # Stops loop on empty page
            break

        # Extends movie list with next page data
        movie_urls.extend(data)
        page_number += 1

        # Add delay to be respectful
        await asyncio.sleep(1)

    if not movie_urls:
        raise ListEmptyException(f"No movies found in list: {list_url}")

    return movie_urls


# Gets movie URL from HTML element
def get_url(movie: Tag) -> str:
    """Extract movie URL from Letterboxd HTML element"""

    if not movie:
        return None

    # Try multiple ways to get the URL depending on the HTML structure
    url = None

    # Method 1: data-target-link attribute (used in watchlists)
    if movie.div and movie.div.get("data-target-link"):
        url = movie.div.get("data-target-link")

    # Method 2: href in nested anchor tag
    elif movie.find("a"):
        url = movie.find("a").get("href")

    # Method 3: data-film-slug attribute
    elif movie.get("data-film-slug"):
        url = f"/film/{movie.get('data-film-slug')}/"

    if url and not url.startswith("http"):
        # Convert relative URL to absolute URL and clean it
        url = url.replace("https://www.letterboxd.com", "")  # Remove if already there
        if not url.startswith("/"):
            url = "/" + url
        return url

    return url


# Add movies from list to database
async def scrape_and_add_list(list_url: str, update_urls: bool = True):
    """
    Scrape a Letterboxd list and add movie URLs to database

    Args:
        list_url: URL of the Letterboxd list to scrape
        update_urls: Whether to add URLs to the database
    """

    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        try:
            print(f"🎬 Scraping Letterboxd list: {list_url}")
            movie_urls = await get_letterboxd_list(list_url, session)

            print(f"📊 Found {len(movie_urls)} movies in the list")

            if update_urls:
                # Prepare URLs for database insertion
                import pandas as pd

                url_records = []
                for i, url in enumerate(movie_urls):
                    # Generate a simple movie_id from the URL
                    movie_id = (
                        url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
                    )
                    if not movie_id:
                        movie_id = f"list_movie_{i}"

                    url_records.append(
                        {"movie_id": movie_id, "url": url, "deprecated": False}
                    )

                # Create DataFrame and update database
                urls_df = pd.DataFrame(url_records)

                try:
                    database.update_movie_urls(urls_df)
                    print(
                        f"✅ Successfully added {len(url_records)} movie URLs to database"
                    )
                except Exception as e:
                    print(f"❌ Error updating database: {e}")
                    # Try adding individually if batch fails
                    added_count = 0
                    for record in url_records:
                        try:
                            single_df = pd.DataFrame([record])
                            database.update_movie_urls(single_df)
                            added_count += 1
                        except Exception as e2:
                            if "duplicate key" not in str(e2):
                                print(f"  Error adding {record['url']}: {e2}")
                    print(
                        f"✅ Successfully added {added_count}/{len(url_records)} URLs individually"
                    )

            # Show sample URLs
            print(f"\n🎯 Sample URLs from the list:")
            for url in movie_urls[:5]:
                print(f"  {url}")

            end_time = time.perf_counter()
            print(f"\n⏱️ Completed in {end_time - start_time:.1f} seconds")

            return movie_urls

        except Exception as e:
            print(f"❌ Error scraping list: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape movies from a Letterboxd list")

    parser.add_argument(
        "--list-url",
        required=True,
        help="Full URL to the Letterboxd list (e.g., https://letterboxd.com/username/list/list-name/)",
    )

    parser.add_argument(
        "--update-urls",
        action="store_true",
        help="Add the scraped movie URLs to the database",
    )

    args = parser.parse_args()

    asyncio.run(scrape_and_add_list(args.list_url, args.update_urls))
