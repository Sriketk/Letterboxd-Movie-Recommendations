#!/usr/bin/env python3

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from lib.data_processing.scrape_movie_data import assign_languages


async def test_parasite_language_extraction():
    """Test the language extraction specifically for Parasite"""

    url = "/film/parasite-2019/"
    movie_id = "426406"

    print(f"🎬 Testing language extraction for Parasite: {url}")
    print("=" * 60)

    # Set proper headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                "https://letterboxd.com" + url, timeout=60
            ) as response:

                if response.status != 200:
                    print(f"❌ Failed to fetch {url} - status code: {response.status}")
                    return

                soup = BeautifulSoup(await response.text(), "html.parser")
                script = str(soup.find("script", {"type": "application/ld+json"}))
                script = script[52:-20]  # Trimmed to useful json data

                try:
                    webData = json.loads(script)
                except Exception as e:
                    print(f"❌ Error parsing JSON: {e}")
                    return

                # Extract basic movie info
                title = webData["name"]
                country = webData["countryOfOrigin"][0]["name"]

                print(f"📽️  Movie: {title}")
                print(f"🇰🇷 Country: {country}")

                # Extract language using the same logic as the scraping script
                language = "English"  # Default to English

                # First try JSON data
                if "inLanguage" in webData:
                    if (
                        isinstance(webData["inLanguage"], list)
                        and len(webData["inLanguage"]) > 0
                    ):
                        language = webData["inLanguage"][0]["name"]
                        print(f"🌍 Language from JSON: {language}")
                    elif isinstance(webData["inLanguage"], dict):
                        language = webData["inLanguage"]["name"]
                        print(f"🌍 Language from JSON: {language}")

                        # If no language in JSON, try to find it in the HTML
                if language == "English":
                    print("🔍 No language in JSON, searching HTML...")

                    # Look for language in text-slug elements
                    language_elements = soup.find_all("a", {"class": "text-slug"})
                    print(f"   Found {len(language_elements)} text-slug elements")

                    # First, look for "Primary Language" specifically
                    print("   🔍 Step 1: Looking for 'Primary Language'...")
                    primary_language_found = False
                    for elem in language_elements:
                        elem_text = elem.get_text().strip()
                        # Check if this element is near a "Primary Language" label
                        parent = elem.parent
                        if parent:
                            parent_text = parent.get_text()
                            if "Primary Language" in parent_text:
                                language = elem_text
                                primary_language_found = True
                                print(f"   ✅ Found 'Primary Language': {language}")
                                break

                    # If no "Primary Language" found, look for just "Language"
                    if not primary_language_found:
                        print("   🔍 Step 2: Looking for 'Language' (not Primary)...")
                        for elem in language_elements:
                            elem_text = elem.get_text().strip()
                            # Check if this element is near a "Language" label (but not "Primary Language")
                            parent = elem.parent
                            if parent:
                                parent_text = parent.get_text()
                                if (
                                    "Language" in parent_text
                                    and "Primary Language" not in parent_text
                                ):
                                    language = elem_text
                                    print(f"   ✅ Found 'Language': {language}")
                                    break

                    # If still not found, look for any language mentions in text-slug elements
                    if language == "English":
                        print("   🔍 Step 3: Looking for any known language...")
                        for elem in language_elements:
                            elem_text = elem.get_text().strip()
                            # Check if it's a known language
                            known_languages = [
                                "Korean",
                                "English",
                                "Spanish",
                                "French",
                                "German",
                                "Italian",
                                "Japanese",
                                "Chinese",
                                "Russian",
                                "Portuguese",
                                "Hindi",
                                "Arabic",
                            ]
                            if elem_text in known_languages:
                                language = elem_text
                                print(f"   ✅ Found known language: {language}")
                                break

                # Test language mapping
                language_code = assign_languages(language)

                print(f"\n📊 Final Results:")
                print(f"   Language: {language}")
                print(f"   Language Code: {language_code}")

                # Show what the full movie data would look like
                movie_data = {
                    "movie_id": movie_id,
                    "url": url,
                    "title": title,
                    "content_type": "movie",
                    "release_year": int(webData["releasedEvent"][0]["startDate"]),
                    "runtime": int(
                        re.search(
                            r"(\d+)\s+mins",
                            soup.find("p", {"class": "text-footer"}).text,
                        ).group(1)
                    ),
                    "letterboxd_rating": webData["aggregateRating"]["ratingValue"],
                    "letterboxd_rating_count": webData["aggregateRating"][
                        "ratingCount"
                    ],
                    "genres": webData["genre"],
                    "country_of_origin": country,
                    "language": language,
                    "poster": webData["image"],
                }

                print(f"\n📋 Complete Movie Data:")
                for key, value in movie_data.items():
                    print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import re

    asyncio.run(test_parasite_language_extraction())
