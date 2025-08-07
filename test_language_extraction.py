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


async def test_language_extraction(movie_url, movie_name):
    """Test language extraction for a specific movie"""

    print(f"🎬 Testing: {movie_name}")
    print(f"   URL: {movie_url}")

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
                "https://letterboxd.com" + movie_url, timeout=60
            ) as response:

                if response.status != 200:
                    print(f"   ❌ Failed to fetch - status code: {response.status}")
                    return None

                soup = BeautifulSoup(await response.text(), "html.parser")
                script = str(soup.find("script", {"type": "application/ld+json"}))
                script = script[52:-20]  # Trimmed to useful json data

                try:
                    webData = json.loads(script)
                except Exception as e:
                    print(f"   ❌ Error parsing JSON: {e}")
                    return None

                # Extract basic movie info
                title = webData["name"]
                country = webData["countryOfOrigin"][0]["name"]

                # Extract language using the same logic as the scraping script
                language = "English"  # Default to English

                # First try JSON data
                if "inLanguage" in webData:
                    if (
                        isinstance(webData["inLanguage"], list)
                        and len(webData["inLanguage"]) > 0
                    ):
                        language = webData["inLanguage"][0]["name"]
                    elif isinstance(webData["inLanguage"], dict):
                        language = webData["inLanguage"]["name"]

                # If no language in JSON, try to find it in the HTML
                if language == "English":
                    # Look for language in text-slug elements
                    language_elements = soup.find_all("a", {"class": "text-slug"})

                    # First, look for "Primary Language" specifically
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
                                break

                    # If no "Primary Language" found, look for just "Language"
                    if not primary_language_found:
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
                                    break

                    # If still not found, look for any language mentions in text-slug elements
                    if language == "English":
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
                                break

                # Test language mapping
                language_code = assign_languages(language)

                print(f"   📊 Results:")
                print(f"      Country: {country}")
                print(f"      Language: {language}")
                print(f"      Language Code: {language_code}")
                print()

                return {
                    "title": title,
                    "country": country,
                    "language": language,
                    "language_code": language_code,
                }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


async def main():
    """Test language extraction on various movies"""

    # Test movies with different languages
    test_movies = [
        ("/film/parasite-2019/", "Parasite (Korean)"),
        ("/film/cargo-2017/", "Cargo (English)"),
        ("/film/amores-perros/", "Amores Perros (Spanish)"),
        ("/film/la-haine/", "La Haine (French)"),
        ("/film/run-lola-run/", "Run Lola Run (German)"),
    ]

    print("🌍 Testing Language Extraction on Various Movies")
    print("=" * 60)

    results = []

    for movie_url, movie_name in test_movies:
        result = await test_language_extraction(movie_url, movie_name)
        if result:
            results.append(result)
        await asyncio.sleep(1)  # Be respectful to Letterboxd

    print("📈 Summary:")
    print("=" * 30)
    for result in results:
        print(
            f"   {result['title']}: {result['language']} (Code: {result['language_code']})"
        )


if __name__ == "__main__":
    asyncio.run(main())
