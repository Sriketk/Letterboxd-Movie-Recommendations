# import aiohttp
from dotenv import load_dotenv
import json
import os
import pandas as pd
import sys
from typing import Dict, Sequence, Tuple

from upstash_redis import Redis

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from data_processing import database

from data_processing.scrape_user_ratings import get_user_ratings

load_dotenv()

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)


# Custom exceptions
class RecommendationFilterException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class UserProfileException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class WatchlistEmptyException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class WatchlistMoviesMissingException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class WatchlistOverlapException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


GENRES = [
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


# Gets user rating dataframe
async def get_user_dataframe(
    user: str, movie_data: pd.DataFrame, update_urls: bool, verbose: bool = False
) -> pd.DataFrame:

    # Gets and processes the user data
    try:
        async with aiohttp.ClientSession() as session:
            user_df, _ = await get_user_ratings(
                user=user,
                session=session,
                exclude_liked=True,
                verbose=False,
                update_urls=update_urls,
            )

            # Ensure movie_id columns have the same type for merging
        # Convert both to string and strip any whitespace
        user_df["movie_id"] = user_df["movie_id"].astype(str).str.strip()
        movie_data["movie_id"] = movie_data["movie_id"].astype(str).str.strip()

        # Also ensure URL columns are consistent
        user_df["url"] = user_df["url"].astype(str).str.strip()
        movie_data["url"] = movie_data["url"].astype(str).str.strip()

        if verbose:
            print(
                f"User data: {len(user_df)} rows, movie_id type: {user_df['movie_id'].dtype}"
            )
            print(
                f"Movie data: {len(movie_data)} rows, movie_id type: {movie_data['movie_id'].dtype}"
            )
            print(f"Sample user movie_ids: {user_df['movie_id'].head(3).tolist()}")
            print(f"Sample movie movie_ids: {movie_data['movie_id'].head(3).tolist()}")

        processed_user_df = user_df.merge(
            movie_data, how="left", on=["movie_id", "url"]
        )
        processed_user_df["rating_differential"] = (
            processed_user_df["user_rating"] - processed_user_df["letterboxd_rating"]
        )

        return processed_user_df
    except Exception as e:
        print(f"Error getting {user}'s dataframe:", e)
        import traceback

        traceback.print_exc()
        raise e


# Converts genre integers into one-hot encoding
def process_genres(row: pd.DataFrame) -> Dict[str, int]:

    # Handle both string and integer inputs from database
    genres_value = row["genres"]
    if isinstance(genres_value, str):
        # If it's a string, try to convert to int first
        try:
            genres_value = int(genres_value)
        except ValueError:
            # If conversion fails, assume it's 0 (no genres)
            genres_value = 0

    genre_binary = bin(genres_value)[2:].zfill(19)

    return {f"is_{genre}": int(genre_binary[pos]) for pos, genre in enumerate(GENRES)}


# Gets processed user df, unrated movies, and movie data
async def get_processed_user_df(
    user: str, update_urls: bool = True
) -> Tuple[pd.DataFrame, Sequence[int], pd.DataFrame]:

    # Gets and processes movie data from the database
    movie_data = database.get_movie_data()

    # Loads processed user df and unrated movies
    cache_key = f"user_df:{user}"
    cached = redis.get(cache_key)

    if cached is not None:
        user_df, unrated = json.loads(cached)
        user_df = pd.DataFrame(user_df)
    else:
        try:
            async with aiohttp.ClientSession() as session:
                user_df, unrated = await get_user_ratings(
                    user=user,
                    session=session,
                    exclude_liked=True,
                    verbose=False,
                    update_urls=update_urls,
                )
        except Exception:
            raise UserProfileException("User has not rated enough movies")

        redis.set(
            cache_key,
            json.dumps((user_df.to_dict("records"), unrated)),
            ex=3600,
        )

    # Ensure movie_id columns have the same type for merging
    user_df["movie_id"] = user_df["movie_id"].astype(str).str.strip()
    movie_data["movie_id"] = movie_data["movie_id"].astype(str).str.strip()

    # Also ensure URL columns are consistent
    user_df["url"] = user_df["url"].astype(str).str.strip()
    movie_data["url"] = movie_data["url"].astype(str).str.strip()

    try:
        processed_user_df = user_df.merge(movie_data, on=["movie_id", "url"])
    except Exception as e:
        print(f"Error merging user and movie data: {e}")
        print(
            f"User data types: movie_id={user_df['movie_id'].dtype}, url={user_df['url'].dtype}"
        )
        print(
            f"Movie data types: movie_id={movie_data['movie_id'].dtype}, url={movie_data['url'].dtype}"
        )
        raise e

    return processed_user_df, unrated, movie_data
