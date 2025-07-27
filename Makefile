# Letterboxd Movie Recommendations - Makefile
# Common commands for development and operations

.PHONY: help setup scrape-small scrape-medium scrape-large scrape-test start-api stop-api test-api status clean-cache test-recommendations check-overlap install

# Default target
help:
	@echo "🎬 Letterboxd Movie Recommendations - Available Commands:"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make setup          - Set up Python environment and install dependencies"
	@echo "  make install        - Install Python dependencies"
	@echo ""
	@echo "🎯 Scraping Commands:"
	@echo "  make scrape-test     - Scrape 20 movies (quick test)"
	@echo "  make scrape-small    - Scrape 100 movies"
	@echo "  make scrape-medium   - Scrape 500 movies"
	@echo "  make scrape-large    - Scrape 1000 movies"
	@echo ""
	@echo "🚀 API Server:"
	@echo "  make start-api       - Start the Flask API server"
	@echo "  make stop-api        - Stop the Flask API server"
	@echo "  make restart-api     - Restart the Flask API server"
	@echo ""
	@echo "🧪 Testing & Status:"
	@echo "  make test-api        - Test API endpoints"
	@echo "  make test-recommendations - Test movie recommendations"
	@echo "  make status          - Check database status and movie counts"
	@echo "  make check-overlap   - Check user/database movie overlap"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean-cache     - Clear movie data cache"
	@echo "  make urls-remaining  - Check remaining URLs in scraping queue"

# Setup and Installation
setup:
	@echo "🔧 Setting up Python environment..."
	cd backend && python -m venv venv
	@echo "✅ Virtual environment created"
	@echo "📦 Installing dependencies..."
	$(MAKE) install
	@echo "✅ Setup complete!"

install:
	@echo "📦 Installing Python dependencies..."
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Scraping Commands
scrape-test:
	@echo "🎬 Scraping 20 movies (test run)..."
	cd backend && source venv/bin/activate && python -m data_processing.scrape_movie_data -u -n 20

scrape-small:
	@echo "🎬 Scraping 100 movies..."
	cd backend && source venv/bin/activate && python -m data_processing.scrape_movie_data -u -n 100

scrape-medium:
	@echo "🎬 Scraping 500 movies..."
	cd backend && source venv/bin/activate && python -m data_processing.scrape_movie_data -u -n 500

scrape-large:
	@echo "🎬 Scraping 1000 movies..."
	cd backend && source venv/bin/activate && python -m data_processing.scrape_movie_data -u -n 1000

# API Server Management
start-api:
	@echo "🚀 Starting Flask API server..."
	cd backend && source venv/bin/activate && python main.py &
	@echo "✅ API server started on http://localhost:3000"

stop-api:
	@echo "🛑 Stopping Flask API server..."
	pkill -f "python main.py" 2>/dev/null || echo "No API server running"
	@echo "✅ API server stopped"

restart-api: stop-api
	@echo "🔄 Restarting API server..."
	sleep 2
	$(MAKE) start-api

# Testing Commands
test-api:
	@echo "🧪 Testing API endpoints..."
	@echo "📋 Testing /api/users:"
	curl -s http://localhost:3000/api/users | head -5
	@echo ""
	@echo "✅ API test complete"

test-recommendations:
	@echo "🎯 Testing movie recommendations..."
	curl -s -X POST http://localhost:3000/api/get-recommendations \
		-H "Content-Type: application/json" \
		-d '{"currentQuery":{"usernames":["sriketk"],"model_type":"personalized","genres":[],"content_types":[],"min_release_year":1900,"max_release_year":2030,"min_runtime":1,"max_runtime":500,"popularity":1}}' \
		| head -10

# Status and Monitoring
status:
	@echo "📊 Database Status:"
	cd backend && source venv/bin/activate && python -c "\
import data_processing.database as db; \
print(f'🎬 Movies in database: {len(db.get_movie_data())}'); \
print(f'📋 URLs in queue: {db.get_table_size(\"movie_urls\")}'); \
print(f'👥 Users in system: {len(db.get_user_list())}'); \
"

check-overlap:
	@echo "🔍 Checking user/database overlap..."
	cd backend && source venv/bin/activate && python -c "import data_processing.database as db; import asyncio; from data_processing.utils import get_user_dataframe; exec('''async def check(): movie_data = db.get_movie_data(); user_df = await get_user_dataframe(\"sriketk\", movie_data, update_urls=False, verbose=False); db_ids = set(movie_data[\"movie_id\"].values); user_ids = set(user_df[\"movie_id\"].values); overlap = db_ids.intersection(user_ids); unrated = db_ids - user_ids; print(f\"🎬 Movies in database: {len(db_ids)}\"); print(f\"⭐ User rated movies: {len(user_ids)}\"); print(f\"🎯 Already rated: {len(overlap)}\"); print(f\"🆕 Available for recommendations: {len(unrated)}\")'''); asyncio.run(check())"

urls-remaining:
	@echo "📋 Checking remaining URLs in scraping queue..."
	cd backend && source venv/bin/activate && python -c "\
import data_processing.database as db; \
remaining = db.get_table_size('movie_urls'); \
scraped = len(db.get_movie_data()); \
print(f'📋 URLs remaining in queue: {remaining}'); \
print(f'🎬 Movies scraped so far: {scraped}'); \
print(f'📈 Progress: {scraped/(scraped+remaining)*100:.1f}% complete'); \
"

# Maintenance
clean-cache:
	@echo "🧹 Clearing movie data cache..."
	cd backend && source venv/bin/activate && python -c "\
import data_processing.database as db; \
db.get_movie_data_cached.cache_clear(); \
print('✅ Cache cleared'); \
"

# Development helpers
dev-check:
	@echo "🔍 Development environment check..."
	@echo "Python version:"
	cd backend && source venv/bin/activate && python --version
	@echo "Key packages:"
	cd backend && source venv/bin/activate && pip list | grep -E "(Flask|supabase|pandas|scikit)"

# Quick workflow combinations
quick-test: scrape-test status test-api
	@echo "✅ Quick test workflow complete!"

full-setup: setup status
	@echo "✅ Full setup complete! Ready to start scraping." 