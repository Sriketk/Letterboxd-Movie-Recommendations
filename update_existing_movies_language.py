#!/usr/bin/env python3

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import pandas as pd
import sys
import os
import time
from typing import Dict, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from lib.data_processing import database
from lib.data_processing.scrape_movie_data import assign_languages

async def scrape_movie_language(movie_url: str, session: aiohttp.ClientSession) -> str:
    """Scrape language information for a single movie"""
    
    try:
        # Add small delay to be respectful to Letterboxd's servers
        await asyncio.sleep(0.5)
        
        async with session.get("https://letterboxd.com" + movie_url, timeout=60) as response:
            
            if response.status != 200:
                print(f"   ❌ Failed to fetch {movie_url} - status code: {response.status}")
                return "English"  # Default to English
            
            soup = BeautifulSoup(await response.text(), "html.parser")
            script = str(soup.find("script", {"type": "application/ld+json"}))
            script = script[52:-20]  # Trimmed to useful json data
            
            try:
                webData = json.loads(script)
            except Exception as e:
                print(f"   ❌ Error parsing JSON for {movie_url}: {e}")
                return "English"
            
            # Extract language information
            language = "English"  # Default to English
            
            # First try JSON data
            if "inLanguage" in webData:
                if isinstance(webData["inLanguage"], list) and len(webData["inLanguage"]) > 0:
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
                            if "Language" in parent_text and "Primary Language" not in parent_text:
                                language = elem_text
                                break
                
                # If still not found, look for any language mentions in text-slug elements
                if language == "English":
                    for elem in language_elements:
                        elem_text = elem.get_text().strip()
                        # Check if it's a known language
                        known_languages = [
                            "Korean", "English", "Spanish", "French", "German", "Italian", 
                            "Japanese", "Chinese", "Russian", "Portuguese", "Hindi", "Arabic"
                        ]
                        if elem_text in known_languages:
                            language = elem_text
                            break
            
            return language
            
    except Exception as e:
        print(f"   ❌ Error scraping {movie_url}: {e}")
        return "English"

async def update_movies_language():
    """Update all existing movies in the database with language information"""
    
    print("🌍 Updating existing movies with language information")
    print("=" * 60)
    
    # Get all existing movies from database
    print("📊 Loading existing movies from database...")
    movies_df = database.get_movie_data()
    
    print(f"   Found {len(movies_df)} movies in database")
    
    # Filter out movies that already have language information (if any)
    if 'language' in movies_df.columns:
        movies_without_language = movies_df[movies_df['language'].isna() | (movies_df['language'] == 0)]
        print(f"   {len(movies_without_language)} movies need language information")
    else:
        movies_without_language = movies_df
        print(f"   All {len(movies_without_language)} movies need language information")
    
    if len(movies_without_language) == 0:
        print("✅ All movies already have language information!")
        return
    
    # Set up HTTP session
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    
    async with aiohttp.ClientSession(headers=headers, connector=connector, timeout=timeout) as session:
        
        # Process movies in batches
        batch_size = 50
        total_movies = len(movies_without_language)
        successful_updates = 0
        failed_updates = 0
        
        print(f"\n🚀 Starting language extraction for {total_movies} movies...")
        print(f"   Batch size: {batch_size}")
        print(f"   Estimated time: {total_movies * 0.5 / 60:.1f} minutes")
        
        for i in range(0, total_movies, batch_size):
            batch = movies_without_language.iloc[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_movies + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} movies)...")
            
            # Create tasks for this batch
            tasks = []
            for _, movie in batch.iterrows():
                task = scrape_movie_language(movie['url'], session)
                tasks.append((movie['movie_id'], movie['title'], task))
            
            # Execute tasks
            batch_results = []
            for movie_id, title, task in tasks:
                try:
                    language = await task
                    language_code = assign_languages(language)
                    batch_results.append({
                        'movie_id': movie_id,
                        'language': language,
                        'language_code': language_code
                    })
                    print(f"   ✅ {title[:40]}{'...' if len(title) > 40 else ''}: {language} (Code: {language_code})")
                    successful_updates += 1
                except Exception as e:
                    print(f"   ❌ {title[:40]}{'...' if len(title) > 40 else ''}: Error - {e}")
                    failed_updates += 1
            
            # Update database with batch results
            if batch_results:
                try:
                    # Create DataFrame for batch update
                    batch_df = pd.DataFrame(batch_results)
                    
                    # Get the full movie data for these movies
                    batch_movies = movies_df[movies_df['movie_id'].isin(batch_df['movie_id'])]
                    
                    # Update the language column
                    for _, row in batch_df.iterrows():
                        movie_idx = batch_movies[batch_movies['movie_id'] == row['movie_id']].index[0]
                        movies_df.loc[movie_idx, 'language'] = row['language_code']
                    
                    print(f"   💾 Updated {len(batch_results)} movies in database")
                    
                except Exception as e:
                    print(f"   ❌ Error updating database: {e}")
                    failed_updates += len(batch_results)
                    successful_updates -= len(batch_results)
            
            # Progress update
            progress = ((i + len(batch)) / total_movies) * 100
            print(f"   📈 Progress: {progress:.1f}% ({i + len(batch)}/{total_movies})")
    
    # Final database update
    print(f"\n💾 Final database update...")
    try:
        # Update the database with all the language information
        database.update_movie_data(movies_df)
        print(f"   ✅ Successfully updated database with language information")
    except Exception as e:
        print(f"   ❌ Error in final database update: {e}")
    
    print(f"\n🎯 UPDATE COMPLETE!")
    print(f"═══════════════════════════════════════")
    print(f"📊 Total movies processed: {total_movies}")
    print(f"✅ Successful updates: {successful_updates}")
    print(f"❌ Failed updates: {failed_updates}")
    if successful_updates > 0:
        success_rate = (successful_updates / total_movies) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")
    print(f"═══════════════════════════════════════")

if __name__ == "__main__":
    asyncio.run(update_movies_language())
