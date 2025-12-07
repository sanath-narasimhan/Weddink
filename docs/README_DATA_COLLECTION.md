# WEDDink Data Collection System

## 📋 Overview

The Data Collection System enables you to **scrape Pinterest** using the [Apify Pinterest Scraper](https://console.apify.com/actors/NmOWmFiz40AgzJNxT/input), rank results by **CLIP-based similarity** to your existing sample database, and **interactively select** images to expand your welcome board collection.

---

## 🚀 Quick Start

### 1. Setup Apify API Token

Get your Apify API token from: https://console.apify.com/account/integrations

Set it as an environment variable:

```bash
export APIFY_API_TOKEN='your_apify_token_here'
```

Or on Windows:
```cmd
set APIFY_API_TOKEN=your_apify_token_here
```

### 2. Install Dependencies

All required dependencies are already in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Start the Application

```bash
python frontend.py
```

Navigate to: **http://localhost:5000/data-collection**

---

## 🎯 How It Works

### **Workflow Overview**

```
1. User Input → 2. Pinterest Scraping → 3. Similarity Ranking → 4. User Selection → 5. Download & Save
```

### **Step-by-Step Process**

#### **Step 1: Configure Search Parameters**
- **Event Type**: engagement, haldi, mehendi, sangeet, wedding, reception
- **Budget Range**: ₹3000-5000, ₹5001-8000, ₹8001-15000
- **Color Theme**: pastel, bold, gold white, etc.
- **Max Results**: Recommended 25 per query (increases to ~100+ total with multiple query variations)

#### **Step 2: Pinterest Scraping**
The system:
- Creates 2-4 optimized Pinterest search queries
- Uses Apify API to scrape pins (actual image URLs, not just pin pages)
- Deduplicates results across queries
- Returns metadata: title, description, saves, comments, creator

#### **Step 3: CLIP Similarity Ranking**
For each scraped image:
- Downloads and generates CLIP embedding
- Compares against **all existing sample images** in database
- Calculates similarity scores (0-100%)
- Identifies best matching sample (event type + budget)
- Ranks results by similarity

#### **Step 4: Interactive Selection**
The UI displays:
- **Image grid** with thumbnails
- **Similarity badges** showing match percentage
- **Best match info** (which sample it resembles)
- **Checkboxes** for selection
- **Bulk select/deselect** controls

#### **Step 5: Download & Database Integration**
When you click "Download Selected":
- Downloads full-resolution images
- Saves to appropriate directory structure:
  ```
  downloaded_images/
    Welcome_board_decor_(budget)/
      EventType/
        user_selected/
          user_selected_{pin_id}_{timestamp}.jpg
          user_selected_{pin_id}_{timestamp}.json  (metadata)
  ```
- Metadata includes: pin_id, url, title, similarity_score, download timestamp
- Updates database statistics automatically

---

## 📊 Database Statistics

The **Statistics Dashboard** shows:
- **Total Images**: All images in database
- **Provided Samples**: Original 36 seed images
- **User Selected**: Images you've curated via this tool

Statistics refresh automatically after downloads.

---

## 🛠️ Components

### **1. Apify Pinterest Scraper** (`apify_pinterest_scraper.py`)

**Features:**
- Integrates with Apify Pinterest Scraper actor
- Configurable max results (default: 25 per query)
- Multi-query support with automatic deduplication
- Rate limiting and timeout handling
- Returns structured JSON with image URLs

**Usage:**
```python
from apify_pinterest_scraper import ApifyPinterestScraper

scraper = ApifyPinterestScraper(api_token='your_token')
result = scraper.scrape_pinterest_search(
    search_query="wedding welcome board pastel",
    max_results=25
)

print(f"Found {result['total_results']} pins")
```

### **2. Similarity Ranker** (`similarity_ranker.py`)

**Features:**
- CLIP ViT-B/32 model for image embeddings
- Loads existing sample database on initialization
- Calculates cosine similarity scores
- Event type and budget filtering
- Diversity selection (avoids near-duplicates)

**Usage:**
```python
from similarity_ranker import SimilarityRanker

ranker = SimilarityRanker()
ranked_results = ranker.rank_scraped_results(
    scraped_results=scraped_pins,
    event_type='wedding',
    budget_range='5001-8000',
    top_k=50
)

# Get diverse top results
diverse = ranker.get_diverse_top_results(ranked_results, top_k=25)
```

### **3. Flask Backend Endpoints** (in `frontend.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/data-collection` | GET | Data collection UI page |
| `/scrape-pinterest` | POST | Scrape & rank Pinterest results |
| `/download-selected-images` | POST | Download selected images |
| `/database-stats` | GET | Get database statistics |

### **4. Interactive UI** (`templates/data_collection.html`)

**Features:**
- Real-time database statistics
- Search form with validation
- Loading states with spinner
- Image grid with hover effects
- Similarity score badges
- Checkbox selection with visual feedback
- Bulk select/deselect controls
- Success/error notifications

---

## 📈 Recommended Settings

### **For Initial Data Collection:**
- **Max Results**: 25-30 per query
- **Top K Results**: 25-50 diverse results
- **Selection Strategy**: Select top 10-15 with >70% similarity

### **For Expanding Specific Categories:**
```python
# Under-represented event types
Event: "haldi", Budget: "8001-15000", Color: "yellow turmeric"

# Specific aesthetic needs
Event: "engagement", Budget: "5001-8000", Color: "pastel pink mint"
```

### **Quality Criteria:**
✅ Similarity score > 60% (good match to existing samples)  
✅ Clear welcome board/sign visible  
✅ Good image quality (not blurry)  
✅ Relevant to event type and budget  
❌ Avoid invitations, cards, unrelated decor

---

## 🔧 Advanced Configuration

### **Increase Scraping Depth**

Modify in `apify_pinterest_scraper.py`:
```python
# Increase max results per query
scrape_result = scraper.scrape_multiple_queries(
    queries, 
    max_results_per_query=50  # Default: 25
)
```

### **Adjust Similarity Threshold**

Modify in `similarity_ranker.py`:
```python
# Filter results by minimum similarity
ranked_results = [
    r for r in ranked_results 
    if r['similarity_score'] > 0.6  # 60% threshold
]
```

### **Custom Query Generation**

Modify in `apify_pinterest_scraper.py`:
```python
def create_search_queries(event_type, budget_range, color_theme):
    queries = [
        f"{event_type} welcome board {color_theme} indian wedding",
        f"{event_type} entrance sign decor {color_theme}",
        f"personalized {event_type} welcome display",
        # Add more custom queries
    ]
    return queries
```

---

## 🐛 Troubleshooting

### **Error: "No Apify API token provided"**
```bash
# Set environment variable before starting app
export APIFY_API_TOKEN='your_token_here'
python frontend.py
```

### **Error: "No sample embeddings found"**
Make sure you have images in `downloaded_images/` directory with proper structure.

### **Slow Scraping**
- Reduce `max_results` to 10-15
- Reduce number of query variations
- Apify scraping takes ~30-90 seconds per query

### **Low Similarity Scores**
- Check if you have enough sample images in the target category
- Try different color themes or broader queries
- Some Pinterest results may be off-topic (filter manually)

### **Image Download Failures**
- Some Pinterest images may be restricted or deleted
- Check your internet connection
- Failed downloads are reported but don't stop the batch

---

## 📦 Output Structure

After downloading selected images:

```
downloaded_images/
├── Welcome_board_decor_(5001-8000)/
│   ├── Wedding/
│   │   ├── provided_sample/          # Original samples
│   │   │   ├── sample_xxx.jpg
│   │   │   └── sample_yyy.jpg
│   │   └── user_selected/            # Your curated images
│   │       ├── user_selected_1234567_20251029_143022.jpg
│   │       ├── user_selected_1234567_20251029_143022.json
│   │       ├── user_selected_9876543_20251029_143045.jpg
│   │       └── user_selected_9876543_20251029_143045.json
```

**Metadata JSON Example:**
```json
{
  "pin_id": "1234567890",
  "pin_url": "https://www.pinterest.com/pin/1234567890/",
  "title": "Beautiful Wedding Welcome Board",
  "description": "Elegant acrylic sign with gold lettering",
  "similarity_score": 0.847,
  "downloaded_at": "2025-10-29T14:30:22",
  "event_type": "wedding",
  "budget_range": "5001-8000"
}
```

---

## 🎨 Best Practices

### **Data Quality**
1. **Review before downloading**: Check image quality and relevance
2. **Start small**: Download 5-10 images per session to maintain quality
3. **Diverse selection**: Include varied styles, colors, and compositions
4. **Document reasoning**: Use metadata to track why images were selected

### **Database Management**
1. **Regular backups**: Copy `downloaded_images/` directory
2. **Periodic cleanup**: Remove low-quality or duplicate images
3. **Balance categories**: Ensure even distribution across events and budgets
4. **Track sources**: User-selected folder keeps curation history

### **Optimization**
1. **Batch processing**: Select 10-20 images at once
2. **Off-peak scraping**: Apify performs better outside peak hours
3. **Cache results**: Save scrape results JSON for later review
4. **Incremental growth**: Add 20-30 images per category over time

---

## 🔗 Integration with Main Search

Downloaded images are **automatically integrated**:
- Local similarity search includes new images immediately (after restart)
- CLIP embeddings are generated on-the-fly
- Ranking system uses expanded database
- PDF mood boards feature curated images

To see new images in search:
1. Download and select images via Data Collection page
2. Restart the Flask app: `python frontend.py`
3. Backend rebuilds database with new images
4. Search results now include your curated collection

---

## 📚 API Reference

### **POST /scrape-pinterest**

**Request:**
```json
{
  "event_type": "wedding",
  "budget_range": "5001-8000",
  "color_theme": "pastel pink",
  "max_results": 25
}
```

**Response:**
```json
{
  "success": true,
  "total_scraped": 87,
  "total_ranked": 45,
  "diverse_results": 25,
  "results": [...],
  "queries_used": [...]
}
```

### **POST /download-selected-images**

**Request:**
```json
{
  "selected_results": [...],
  "event_type": "wedding",
  "budget_range": "5001-8000"
}
```

**Response:**
```json
{
  "success": true,
  "downloaded": 12,
  "failed": 1,
  "target_directory": "downloaded_images/Welcome_board_decor_(5001-8000)/Wedding/user_selected",
  "downloaded_files": [...],
  "failed_downloads": [...]
}
```

---

## 🎓 Tips for Success

1. **Use specific color themes**: "pastel pink mint lavender" > "colorful"
2. **Set realistic expectations**: ~70% of scraped images will be relevant
3. **Manual curation is key**: AI ranking helps, but human judgment matters
4. **Iterate and refine**: Run multiple scrapes with varied queries
5. **Monitor database balance**: Aim for 20-30 images per category

---

## 🤝 Support

For issues or questions:
- Check troubleshooting section above
- Review Apify documentation: https://docs.apify.com/
- Verify CLIP model installation: `python -c "import open_clip; print('OK')"`

---

**Happy Data Collecting! 🎨📊**



