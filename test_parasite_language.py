#!/usr/bin/env python3

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import pandas as pd
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from lib.data_processing.scrape_movie_data import assign_languages


async def scrape_parasite_language():
    """Scrape Parasite movie to see what language data is returned"""

    url = "/film/parasite-2019/"
    movie_id = "426406"

    print(f"🎬 Scraping Parasite movie: {url}")
    print("=" * 50)

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

                print("📋 Raw JSON data keys:")
                for key in webData.keys():
                    print(f"   - {key}")

                print("\n🌍 Language Information:")
                if "inLanguage" in webData:
                    print(f"   Raw inLanguage data: {webData['inLanguage']}")

                    if (
                        isinstance(webData["inLanguage"], list)
                        and len(webData["inLanguage"]) > 0
                    ):
                        language = webData["inLanguage"][0]["name"]
                        print(f"   Extracted language (from list): {language}")
                    elif isinstance(webData["inLanguage"], dict):
                        language = webData["inLanguage"]["name"]
                        print(f"   Extracted language (from dict): {language}")
                    else:
                        language = "English"
                        print(f"   Default language: {language}")
                else:
                    language = "English"
                    print(f"   No language data found, defaulting to: {language}")

                # Look for language information in the page content
                print("\n🔍 Looking for language info in page content:")

                # Check for language in the film details section
                film_details = soup.find("div", {"class": "film-detail-content"})
                if film_details:
                    print("   Found film-detail-content section")
                    # Look for language mentions
                    text_content = film_details.get_text().lower()
                    if "korean" in text_content:
                        print("   Found 'Korean' in page content")
                    if "english" in text_content:
                        print("   Found 'English' in page content")

                # Check for language in the sidebar
                sidebar = soup.find("div", {"class": "sidebar"})
                if sidebar:
                    print("   Found sidebar section")
                    sidebar_text = sidebar.get_text().lower()
                    if "korean" in sidebar_text:
                        print("   Found 'Korean' in sidebar")

                # Check for any language-related elements
                language_elements = soup.find_all(
                    string=lambda text: text
                    and any(
                        lang in text.lower()
                        for lang in [
                            "korean",
                            "english",
                            "spanish",
                            "french",
                            "german",
                            "japanese",
                            "chinese",
                        ]
                    )
                )
                if language_elements:
                    print("   Found language mentions in page:")
                    for elem in language_elements[:10]:  # Show first 10
                        clean_text = elem.strip()
                        if (
                            clean_text and len(clean_text) < 100
                        ):  # Only show short, relevant text
                            print(f"     - {clean_text}")

                # Look for "Primary Language" specifically
                print("\n🎯 Looking for 'Primary Language' information:")

                # Search for "Primary Language" text and extract the language value
                primary_language_elements = soup.find_all(
                    string=lambda text: text and "Primary Language" in text
                )
                if primary_language_elements:
                    print("   ✅ Found 'Primary Language' mentions:")
                    for elem in primary_language_elements:
                        print(f"     - {elem.strip()}")
                        # Get the parent element to see the context
                        parent = elem.parent
                        if parent:
                            parent_text = parent.get_text().strip()
                            print(f"       Parent text: {parent_text}")

                            # Try to extract the language from the parent text
                            if "Primary Language" in parent_text:
                                # Look for the language after "Primary Language"
                                parts = parent_text.split("Primary Language")
                                if len(parts) > 1:
                                    after_primary = parts[1].strip()
                                    print(
                                        f"       After 'Primary Language': {after_primary}"
                                    )

                                    # Look for common language names
                                    languages = [
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
                                    ]
                                    for lang in languages:
                                        if lang in after_primary:
                                            print(f"       ✅ Found language: {lang}")
                                            language = lang
                                            break

                # Look for language in the sidebar specifically
                print("\n🔍 Checking sidebar for language info:")
                sidebar_sections = soup.find_all("section", {"class": "sidebar"})
                for i, section in enumerate(sidebar_sections):
                    print(f"   Checking sidebar section {i+1}")
                    section_text = section.get_text()
                    if "Primary Language" in section_text:
                        print("   ✅ Found 'Primary Language' in sidebar")
                        # Get the full context around Primary Language
                        lines = section_text.split("\n")
                        for j, line in enumerate(lines):
                            if "Primary Language" in line:
                                print(f"     Line {j}: {line.strip()}")
                                # Show surrounding lines for context
                                if j > 0:
                                    print(f"     Line {j-1}: {lines[j-1].strip()}")
                                if j < len(lines) - 1:
                                    print(f"     Line {j+1}: {lines[j+1].strip()}")
                    if "Language" in section_text:
                        print("   ✅ Found 'Language' mention in sidebar")

                # Look for any elements that might contain language info
                print("\n🔍 Looking for language-related elements:")
                language_related = soup.find_all(
                    string=lambda text: text
                    and any(
                        term in text
                        for term in [
                            "Language",
                            "Korean",
                            "English",
                            "Spanish",
                            "French",
                        ]
                    )
                )
                for elem in language_related[:15]:  # Show first 15
                    clean_text = elem.strip()
                    if clean_text and len(clean_text) < 200:
                        print(f"     - {clean_text}")

                # Look for the actual language value by examining the HTML structure
                print("\n🔍 Examining HTML structure for language:")

                # Find all elements that contain "Korean" and see their structure
                korean_elements = soup.find_all(
                    string=lambda text: text and "Korean" in text
                )
                for i, elem in enumerate(korean_elements[:5]):
                    print(f"   Korean element {i+1}:")
                    print(f"     Text: {elem.strip()}")
                    parent = elem.parent
                    if parent:
                        print(f"     Parent tag: {parent.name}")
                        print(f"     Parent class: {parent.get('class', 'No class')}")
                        print(f"     Parent text: {parent.get_text().strip()}")

                        # Check if this is near a "Primary Language" label
                        grandparent = parent.parent
                        if grandparent:
                            grandparent_text = grandparent.get_text()
                            if "Primary Language" in grandparent_text:
                                print(f"     ✅ Found near 'Primary Language' label!")
                                print(f"     Grandparent text: {grandparent_text}")
                                language = "Korean"
                                break

                # Test language mapping
                language_code = assign_languages(language)
                print(f"   Language code: {language_code}")

                print("\n🇰🇷 Country Information:")
                if "countryOfOrigin" in webData:
                    country = webData["countryOfOrigin"][0]["name"]
                    print(f"   Country: {country}")

                print("\n📝 Other Key Data:")
                if "name" in webData:
                    print(f"   Title: {webData['name']}")
                if "genre" in webData:
                    print(f"   Genres: {webData['genre']}")

    except Exception as e:
        print(f"❌ Error scraping Parasite: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_parasite_language())
