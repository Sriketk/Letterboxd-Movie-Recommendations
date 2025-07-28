#!/usr/bin/env python3

import requests
import json
import time


def test_category_recommendations():
    print("🎬 TESTING CATEGORY-BASED RECOMMENDATIONS (NO USERNAME REQUIRED)")
    print("=" * 70)

    # Server URL
    base_url = "http://127.0.0.1:3000"

    # Test cases
    test_cases = [
        {
            "name": "🚀 Sci-Fi Movies - 2020s",
            "payload": {
                "genres": ["science_fiction"],
                "content_types": ["movie"],
                "min_release_year": 2020,
                "max_release_year": 2024,
                "min_runtime": 80,
                "max_runtime": 200,
                "popularity": 3,
                "num_recs": 10,
            },
        },
        {
            "name": "💕 Romance Movies - Mid 2000s",
            "payload": {
                "genres": ["romance"],
                "content_types": ["movie"],
                "min_release_year": 2003,
                "max_release_year": 2007,
                "min_runtime": 60,
                "max_runtime": 180,
                "popularity": 3,
                "num_recs": 10,
            },
        },
        {
            "name": "🎭 Popular Action Movies - Any Era",
            "payload": {
                "genres": ["action"],
                "content_types": ["movie"],
                "min_release_year": 1990,
                "max_release_year": 2024,
                "min_runtime": 90,
                "max_runtime": 200,
                "popularity": 1,  # Most popular
                "num_recs": 15,
            },
        },
        {
            "name": "🧛 Horror Movies - Recent",
            "payload": {
                "genres": ["horror"],
                "content_types": ["movie"],
                "min_release_year": 2015,
                "max_release_year": 2024,
                "min_runtime": 70,
                "max_runtime": 150,
                "popularity": 4,  # Less mainstream
                "num_recs": 8,
            },
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎬 Test {i}: {test_case['name']}")
        print("-" * 50)

        try:
            start_time = time.time()

            # Make API request
            response = requests.post(
                f"{base_url}/api/get-category-recommendations",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            end_time = time.time()

            if response.status_code == 200:
                recommendations = response.json()

                print(f"   ✅ SUCCESS! Got {len(recommendations)} recommendations")
                print(f"   ⏱️ Response time: {end_time - start_time:.2f} seconds")
                print(f"   📊 Top movies:")

                for j, movie in enumerate(
                    recommendations[: min(5, len(recommendations))], 1
                ):
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

    print(f"\n🎯 Category Recommendation Testing Complete!")
    print("🎬 No username required - works with pure category filtering!")


if __name__ == "__main__":
    test_category_recommendations()
