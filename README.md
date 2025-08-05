# Letterboxd-Movie-Recommendations

Generate AI-powered movie recommendations, discover unique profile statistics,
and pick movies from your watchlist, all with just your Letterboxd username.

[www.recommendations.victorverma.com](https://www.recommendations.victorverma.com/)

## Special Thanks

This project is a fork of
[Victor Verma's Letterboxd-Movie-Recommendations](https://github.com/victorverma3/Letterboxd-Movie-Recommendations).
I would like to extend my sincere gratitude to Victor Verma for creating the
original backend code and architecture that made this project possible. His work
on the content-based filtering recommendation system and the comprehensive
backend infrastructure has been invaluable.

### Key Differences from Original

While this fork uses Victor's backend code and architecture, there are some
notable differences:

-   **Movie Database Source**: This implementation currently uses movies from
    the
    [Top 5000 Films of All Time](https://letterboxd.com/prof_ratigan/list/top-5000-films-of-all-time-calculated/)
    list as the recommendation database, rather than the original 100,000+ movie
    database.
-   **API Documentation**: This fork uses an OpenAPI specification for better
    API documentation and testing.
-   **Statistics Feature**: All statistics endpoints have been removed as this
    feature is not implemented in this fork.
-   **Future Plans**: I plan to expand the movie database by scraping actual
    reviews and sentiment analysis rather than just objective information such
    as runtime and genre, and adding more movies to provide a broader range of
    recommendations.

## Table of Contents

-   [Sitemap](#sitemap)
-   [Technologies](#technologies)
-   [Core Features](#core-features)
    -   [Recommendations](#recommendations)
        -   [Architecture](#architecture)
        -   [Movie Data Collection](#movie-data-collection)
        -   [User Rating Collection](#user-rating-collection)
        -   [Personalized Recommendation Model](#personalized-recommendation-model)
        -   [General Recommendation Model](#general-recommendation-model)
        -   [Multi-User Recommendations](#multi-user-recommendations)
    -   [Statistics](#statistics)
        -   [Basic Statistics](#basic-statistics)
        -   [Genre Statistics](#genre-statistics)
        -   [User Rating Distribution](#user-rating-distribution)
    -   [Watchlist Picker](#watchlist-picker)
-   [Inspiration](#inspiration)
-   [Limitations](#limitations)
-   [Future Improvements](#future-improvements)

## Full Description

For a complete description of the project, including detailed explanations of
the architecture, features, and implementation details, please refer to the
[original repository](https://github.com/victorverma3/Letterboxd-Movie-Recommendations)
by Victor Verma.
