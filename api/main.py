import asyncio
from dotenv import load_dotenv
from flask import abort, Flask, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields


import os
import sys
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import lib.data_processing.database as database
from lib.data_processing.utils import (
    RecommendationFilterException,
    UserProfileException,
)
from lib.model.recommender import merge_recommendations, recommend_n_movies

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


# CONTENT ENDPOINTS


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
