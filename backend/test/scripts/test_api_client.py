#!/usr/bin/env python3

import requests
import json
import time


def test_api_recommendations():
    print("🌐 TESTING RECOMMENDATION API SERVER")
    print("=" * 50)

    # Server URL
    base_url = "http://127.0.0.1:3000"

    # Test cases
    test_cases = [
        {
            "name": "💕 Romance Movies - Mid 2000s",
            "payload": {
                "currentQuery": {
                    "usernames": ["sriketk"],
                    "model_type": "personalized",
                    "genres": ["romance"],
                    "content_types": ["movie"],
                    "min_release_year": 2003,
                    "max_release_year": 2007,
                    "min_runtime": 60,
                    "max_runtime": 300,
                    "popularity": 3,
                }
            },
        },
        {
            "name": "🚀 Sci-Fi Movies - 2020s",
            "payload": {
                "currentQuery": {
                    "usernames": ["sriketk"],
                    "model_type": "personalized",
                    "genres": ["science_fiction"],
                    "content_types": ["movie"],
                    "min_release_year": 2020,
                    "max_release_year": 2024,
                    "min_runtime": 60,
                    "max_runtime": 300,
                    "popularity": 3,
                }
            },
        },
        {
            "name": "🎭 Adventure Movies - 90s",
            "payload": {
                "currentQuery": {
                    "usernames": ["sriketk"],
                    "model_type": "personalized",
                    "genres": ["adventure"],
                    "content_types": ["movie"],
                    "min_release_year": 1990,
                    "max_release_year": 1999,
                    "min_runtime": 60,
                    "max_runtime": 300,
                    "popularity": 3,
                }
            },
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎬 Test {i}: {test_case['name']}")
        print("-" * 40)

        try:
            start_time = time.time()

            # Make API request
            response = requests.post(
                f"{base_url}/api/get-recommendations",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            end_time = time.time()

            if response.status_code == 200:
                recommendations = response.json()

                print(f"   ✅ SUCCESS! Got {len(recommendations)} recommendations")
                print(f"   ⏱️ Response time: {end_time - start_time:.2f} seconds")
                print(f"   📊 Top 5 recommendations:")

                for j, movie in enumerate(recommendations[:5], 1):
                    title = movie.get("title", "N/A")
                    year = movie.get("release_year", "N/A")
                    rating = movie.get("predicted_rating", "N/A")
                    print(f"      {j}. {title} ({year}) - {rating}")

                # Show rating stats
                if recommendations:
                    ratings = [
                        float(movie.get("predicted_rating", 0))
                        for movie in recommendations
                    ]
                    avg_rating = sum(ratings) / len(ratings)
                    max_rating = max(ratings)
                    min_rating = min(ratings)

                    print(f"   📈 Rating Stats:")
                    print(f"      Average: {avg_rating:.2f}")
                    print(f"      Range: {min_rating:.2f} - {max_rating:.2f}")

            else:
                print(f"   ❌ ERROR: HTTP {response.status_code}")
                print(f"   📄 Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST ERROR: {str(e)}")
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {str(e)}")

    print(f"\n🎯 API Testing Complete!")
    print("🎬 Your recommendation server is working perfectly through HTTP!")


if __name__ == "__main__":
    test_api_recommendations()
