#!/usr/bin/env python3

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from lib.data_processing.scrape_movie_data import assign_languages


def test_language_mapping():
    """Test the language mapping function"""
    print("🧪 Testing Language Mapping Function")
    print("=" * 40)

    test_languages = [
        "English",
        "Spanish",
        "French",
        "German",
        "Italian",
        "Portuguese",
        "Russian",
        "Japanese",
        "Korean",
        "Chinese",
        "Hindi",
        "Arabic",
        "Swedish",
        "Norwegian",
        "Danish",
        "Dutch",
        "Polish",
        "Turkish",
        "Greek",
        "Hebrew",
        "Unknown Language",
    ]

    for lang in test_languages:
        code = assign_languages(lang)
        print(f"{lang:15} -> {code}")

    print("\n✅ Language mapping test completed!")


if __name__ == "__main__":
    test_language_mapping()
