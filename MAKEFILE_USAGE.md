# 🎬 Makefile Commands Reference

This Makefile contains all the frequently used commands for the Letterboxd Movie
Recommendations project.

## 📋 Quick Start

```bash
# See all available commands
make help

# Check current status
make status

# Run a quick test scrape
make scrape-test
```

## 🔧 Common Workflows

### **Initial Setup**

```bash
make setup          # Set up environment and install dependencies
```

### **Scraping Movies**

```bash
make scrape-test     # 20 movies (quick test)
make scrape-small    # 100 movies
make scrape-medium   # 500 movies
make scrape-large    # 1000 movies
```

### **API Management**

```bash
make start-api       # Start Flask server on localhost:3000
make stop-api        # Stop the server
make restart-api     # Restart the server
make test-api        # Test API endpoints
```

### **Status & Monitoring**

```bash
make status          # Database overview
make check-overlap   # User/database movie overlap
make urls-remaining  # Scraping progress
```

### **Maintenance**

```bash
make clean-cache     # Clear movie data cache
```

## 📊 Example Output

### Status Check

```
🎬 Movies in database: 1000
📋 URLs in queue: 4134
👥 Users in system: 1
📈 Progress: 19.5% complete
```

### Overlap Check

```
🎬 Movies in database: 1000
⭐ User rated movies: 234
🎯 Already rated: 234
🆕 Available for recommendations: 766
```

## 🚀 Enhanced Features

All commands include:

-   ✅ **Beautiful emoji output** for easy reading
-   ✅ **Error handling** with graceful failures
-   ✅ **Progress tracking** for scraping operations
-   ✅ **Automatic environment activation**
-   ✅ **Real-time status updates**

## 💡 Pro Tips

-   Run `make status` before scraping to check current state
-   Use `make scrape-test` first to verify everything works
-   `make check-overlap` shows how many movies are available for recommendations
-   All commands handle the virtual environment automatically
