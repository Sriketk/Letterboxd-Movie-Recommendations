import asyncio
from dotenv import load_dotenv
from flask import abort, Flask, jsonify, Response, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields
import gdown
import json
import os
import sys
import time

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

from data_processing import database
from data_processing.calculate_user_statistics import (
    get_user_percentiles,
    get_user_statistics,
)
from data_processing.utils import (
    get_user_dataframe,
    RecommendationFilterException,
    UserProfileException,
    WatchlistEmptyException,
    WatchlistOverlapException,
)
from data_processing.watchlist_picks import get_user_watchlist_picks
from model.recommender import merge_recommendations, recommend_n_movies
from model.recommender import recommend_movies_by_category

load_dotenv()

app = Flask(__name__)
cors = CORS(app, origins="*")

# Initialize Flask-RESTX
api = Api(
    app,
    version="1.0",
    title="Letterboxd Movie Recommendations API",
    description="A powerful movie recommendation system based on Letterboxd ratings",
    doc="/docs/",  # This creates the Swagger UI at /docs/
)

# Create namespaces
recommendations_ns = api.namespace("api", description="Movie recommendation operations")
users_ns = api.namespace("api", description="User operations")
stats_ns = api.namespace("api", description="Statistics operations")
content_ns = api.namespace("api", description="Content operations")
admin_ns = api.namespace("api/admin", description="Admin operations")

# Define request models
recommendation_query = api.model(
    "RecommendationQuery",
    {
        "usernames": fields.List(
            fields.String, required=True, description="List of Letterboxd usernames"
        ),
        "model_type": fields.String(
            required=True, description="Model type", enum=["personalized", "general"]
        ),
        "genres": fields.List(
            fields.String, required=True, description="List of genres"
        ),
        "content_types": fields.List(
            fields.String,
            required=True,
            description="Content types",
            enum=["movie", "tv"],
        ),
        "min_release_year": fields.Integer(
            required=True, description="Minimum release year"
        ),
        "max_release_year": fields.Integer(
            required=True, description="Maximum release year"
        ),
        "min_runtime": fields.Integer(
            required=True, description="Minimum runtime in minutes"
        ),
        "max_runtime": fields.Integer(
            required=True, description="Maximum runtime in minutes"
        ),
        "popularity": fields.Integer(
            required=True, description="Popularity level (1-6)", min=1, max=6
        ),
    },
)

recommendation_request = api.model(
    "RecommendationRequest",
    {
        "currentQuery": fields.Nested(
            recommendation_query, required=True, description="Query parameters"
        )
    },
)

category_recommendation_request = api.model(
    "CategoryRecommendationRequest",
    {
        "num_recs": fields.Integer(description="Number of recommendations", default=25),
        "genres": fields.List(fields.String, description="List of genres"),
        "content_types": fields.List(
            fields.String, description="Content types", default=["movie", "tv"]
        ),
        "min_release_year": fields.Integer(
            description="Minimum release year", default=1900
        ),
        "max_release_year": fields.Integer(
            description="Maximum release year", default=2100
        ),
        "min_runtime": fields.Integer(description="Minimum runtime", default=0),
        "max_runtime": fields.Integer(description="Maximum runtime", default=1000),
        "popularity": fields.Integer(description="Popularity level", default=3),
    },
)

statistics_request = api.model(
    "StatisticsRequest",
    {"username": fields.String(required=True, description="Letterboxd username")},
)

watchlist_data = api.model(
    "WatchlistData",
    {
        "userList": fields.List(
            fields.String, required=True, description="List of usernames"
        ),
        "overlap": fields.Boolean(required=True, description="Overlap requirement"),
        "pickType": fields.String(required=True, description="Pick type"),
        "numPicks": fields.Integer(required=True, description="Number of picks"),
    },
)

watchlist_request = api.model(
    "WatchlistRequest",
    {
        "data": fields.Nested(
            watchlist_data, required=True, description="Watchlist data"
        )
    },
)

# Define response models
movie_recommendation = api.model(
    "MovieRecommendation",
    {
        "title": fields.String(description="Movie title"),
        "release_year": fields.Integer(description="Release year"),
        "predicted_rating": fields.String(description="Predicted rating"),
        "poster": fields.String(description="Poster URL"),
        "url": fields.String(description="Letterboxd URL"),
    },
)

user_list_response = api.model(
    "UserListResponse",
    {"users": fields.List(fields.String, description="List of usernames")},
)

health_response = api.model(
    "HealthResponse",
    {
        "status": fields.String(description="Health status"),
        "message": fields.String(description="Status message"),
    },
)


# RECOMMENDATION ENDPOINTS
@recommendations_ns.route("/get-recommendations")
class MovieRecommendations(Resource):
    @api.expect(recommendation_request)
    @api.marshal_list_with(movie_recommendation)
    @api.doc(
        description="Get personalized movie recommendations based on user preferences",
        responses={
            200: "Success - Returns list of movie recommendations",
            406: "Not Acceptable - No movies match the filter criteria",
            500: "Internal Server Error - User profile error or other server issues",
        },
    )
    def post(self):
        """Get movie recommendations for specified users and criteria"""

        start = time.perf_counter()

        data = request.json.get("currentQuery")
        usernames = data.get("usernames")
        model_type = data.get("model_type")
        genres = data.get("genres")
        content_types = data.get("content_types")
        min_release_year = data.get("min_release_year")
        max_release_year = data.get("max_release_year")
        min_runtime = data.get("min_runtime")
        max_runtime = data.get("max_runtime")
        popularity = data.get("popularity")

        # Gets movie recommendations
        try:
            if len(usernames) == 1:
                recommendations = asyncio.run(
                    recommend_n_movies(
                        num_recs=25,
                        user=usernames[0],
                        model_type=model_type,
                        genres=genres,
                        content_types=content_types,
                        min_release_year=min_release_year,
                        max_release_year=max_release_year,
                        min_runtime=min_runtime,
                        max_runtime=max_runtime,
                        popularity=popularity,
                    )
                )

                recommendations = recommendations["recommendations"].to_dict(
                    orient="records"
                )

            else:
                tasks = [
                    recommend_n_movies(
                        num_recs=500,
                        user=username,
                        model_type=model_type,
                        genres=genres,
                        content_types=content_types,
                        min_release_year=min_release_year,
                        max_release_year=max_release_year,
                        min_runtime=min_runtime,
                        max_runtime=max_runtime,
                        popularity=popularity,
                    )
                    for username in usernames
                ]
                all_recommendations = asyncio.run(asyncio.gather(*tasks))

                # Merges recommendations
                merged_recommendations = merge_recommendations(
                    num_recs=25, all_recommendations=all_recommendations
                )
                recommendations = merged_recommendations.to_dict(orient="records")

        except RecommendationFilterException as e:
            abort(406, str(e))
        except UserProfileException as e:
            abort(500, str(e))
        except Exception as e:
            abort(500, "Error getting recommendations")

        # Updates user logs in database
        try:
            database.update_many_user_logs(usernames)
            print(f'Successfully logged {", ".join(map(str, usernames))} in database')
        except:
            print(f'Failed to log {", ".join(map(str, usernames))} in database')

        finish = time.perf_counter()
        print(
            f'Generated movie recommendations for {", ".join(map(str, usernames))} in {finish - start} seconds'
        )

        return recommendations


@recommendations_ns.route("/get-category-recommendations")
class CategoryRecommendations(Resource):
    @api.expect(category_recommendation_request)
    @api.marshal_list_with(movie_recommendation)
    @api.doc(
        description="Get movie recommendations based solely on category filters (no username required)"
    )
    def post(self):
        """Get category-based movie recommendations"""

        start = time.perf_counter()

        # Accept both { currentQuery: {...} } and direct JSON bodies
        payload = request.json
        data = (
            payload.get("currentQuery")
            if isinstance(payload, dict) and payload.get("currentQuery")
            else payload
        )

        # Extract filter parameters with sensible defaults
        num_recs = data.get("num_recs", 25)
        genres = data.get("genres", [])
        content_types = data.get("content_types", ["movie", "tv"])
        min_release_year = data.get("min_release_year", 1900)
        max_release_year = data.get("max_release_year", 2100)
        min_runtime = data.get("min_runtime", 0)
        max_runtime = data.get("max_runtime", 1000)
        popularity = data.get("popularity", 3)

        try:
            recommendations_df = asyncio.run(
                recommend_movies_by_category(
                    num_recs=num_recs,
                    genres=genres,
                    content_types=content_types,
                    min_release_year=min_release_year,
                    max_release_year=max_release_year,
                    min_runtime=min_runtime,
                    max_runtime=max_runtime,
                    popularity=popularity,
                )
            )

            recommendations = recommendations_df.to_dict(orient="records")

        except RecommendationFilterException as e:
            abort(406, str(e))
        except Exception as e:
            abort(500, "Error getting category recommendations")

        finish = time.perf_counter()
        print(f"Generated category-based recommendations in {finish - start} seconds")

        return recommendations


# USER ENDPOINTS
@users_ns.route("/users")
class Users(Resource):
    @api.doc(description="Get list of all users")
    def get(self):
        """Get a list of all users"""
        try:
            users = database.get_user_list()
            return users
        except Exception as e:
            print("Failed to get user list")
            abort(500, "Failed to get user list")


# STATISTICS ENDPOINTS
@stats_ns.route("/get-statistics")
class Statistics(Resource):
    @api.expect(statistics_request)
    @api.doc(description="Get user statistics and profile analysis")
    def post(self):
        """Get user statistics"""

        start = time.perf_counter()

        username = request.json.get("username")

        # Gets movie data from database
        try:
            movie_data = database.get_movie_data()
        except Exception as e:
            print("Failed to get movie data")
            abort(500, "Failed to get movie data")

        # Gets user dataframe
        try:
            user_df = asyncio.run(
                get_user_dataframe(username, movie_data, update_urls=True, verbose=True)
            )
        except UserProfileException as e:
            abort(500, str(e))

        # Updates user log in database
        try:
            database.update_user_log(username)
            print(f"Successfully logged {username} in database")
        except:
            print(f"Failed to log {username} in database")

        # Gets user stats
        try:
            user_stats = asyncio.run(get_user_statistics(user_df))
            statistics = {"simple_stats": user_stats}
        except:
            abort(500, "Failed to calculate user statistics")

        # Updates user stats in database
        try:
            database.update_user_statistics(username, user_stats)
            print(f"Successfully updated statistics for {username} in database")
        except:
            print(f"Failed to update statistics for {username} in database")

        # Gets user distribution values
        statistics["distribution"] = {
            "user_rating_values": user_df["user_rating"].tolist(),
            "letterboxd_rating_values": user_df["letterboxd_rating"].dropna().tolist(),
        }

        # Gets user percentiles
        try:
            user_percentiles = get_user_percentiles(user_stats)
            statistics["percentiles"] = user_percentiles
        except:
            abort(500, "Failed to get user percentiles")

        finish = time.perf_counter()
        print(
            f"Calculated profile statistics for {username} in {finish - start} seconds"
        )

        return statistics


@stats_ns.route("/get-watchlist-picks")
class WatchlistPicks(Resource):
    @api.expect(watchlist_request)
    @api.doc(description="Get watchlist picks for multiple users")
    def post(self):
        """Get watchlist picks"""

        start = time.perf_counter()

        data = request.json.get("data")
        user_list = data.get("userList")
        overlap = data.get("overlap")
        pick_type = data.get("pickType")
        model_type = "personalized"  # TODO implemented frontend
        num_picks = data.get("numPicks")

        # Gets watchlist picks
        try:
            watchlist_picks = asyncio.run(
                get_user_watchlist_picks(
                    user_list=user_list,
                    overlap=overlap,
                    pick_type=pick_type,
                    model_type=model_type,
                    num_picks=num_picks,
                )
            )
        except WatchlistOverlapException as e:
            abort(406, str(e))
        except WatchlistEmptyException as e:
            abort(500, str(e))

        # Updates user logs in database
        try:
            database.update_many_user_logs(user_list)
            print(f'Successfully logged {", ".join(map(str, user_list))} in database')
        except:
            print(f'Failed to log {", ".join(map(str, user_list))} in database')

        finish = time.perf_counter()
        print(
            f'Picked from watchlist for {", ".join(map(str, user_list))} in {finish - start} seconds'
        )

        return watchlist_picks


# CONTENT ENDPOINTS
@content_ns.route("/get-frequently-asked-questions")
class FAQ(Resource):
    @api.doc(description="Get frequently asked questions")
    def get(self):
        """Get frequently asked questions"""
        try:
            with open("data/faq.json", "r") as f:
                faq = json.load(f)
            return faq
        except Exception as e:
            print(e)
            abort(500, "Failed to get frequently asked questions")


@content_ns.route("/get-application-metrics")
class ApplicationMetrics(Resource):
    @api.doc(description="Get application metrics")
    def get(self):
        """Get application metrics"""
        try:
            metrics = database.get_application_metrics()
            return metrics
        except Exception as e:
            print(e)
            abort(500, "Failed to get application metrics")


@content_ns.route("/get-release-notes")
class ReleaseNotes(Resource):
    @api.doc(description="Get release notes")
    def get(self):
        """Get release notes"""
        try:
            with open("data/release_notes.json", "r") as f:
                notes = json.load(f)
            return notes
        except Exception as e:
            print(e)
            abort(500, "Failed to get release notes")


# ADMIN ENDPOINTS
@admin_ns.route("/clear-movie-data-cache")
class ClearCache(Resource):
    @api.doc(description="Clear movie data cache (admin only)")
    def post(self):
        """Clear movie data cache"""
        auth = request.headers.get("Authorization")
        if auth != f'Bearer {os.getenv("ADMIN_SECRET_KEY")}':
            abort(401, description="Unauthorized")

        database.get_movie_data_cached.cache_clear()
        return {"message": "Successfully cleared movie data cache"}, 200


# Add a simple health check endpoint
@api.route("/health")
class HealthCheck(Resource):
    @api.marshal_with(health_response)
    @api.doc(description="Health check endpoint")
    def get(self):
        """Check if the API is running"""
        return {
            "status": "sriket what is ups",
            "message": "Movie recommendation API is running",
        }, 200


if __name__ == "__main__":
    print("🚀 Starting Letterboxd Movie Recommendations API")
    print("📖 Swagger documentation available at: http://127.0.0.1:3000/docs/")
    print("🎬 API endpoints available at: http://127.0.0.1:3000/api/")
    print("🔧 All endpoints from main.py now included!")
    app.run(debug=True, port=4000)
