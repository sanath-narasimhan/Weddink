# 🔄 Unified Search Guide - Google + Pinterest with Similarity Scores

## 📋 Overview

The **Unified Search System** combines Google Images (25 results) and Pinterest (100 results via Apify) into a single interface, ranking **all results by similarity** to your existing sample database using CLIP AI.

---

## 🎯 Key Features

✅ **Google Search**: Exactly 25 results with similarity scoring  
✅ **Pinterest Search**: Up to 100 results via Apify API  
✅ **CLIP Similarity**: All results ranked against existing samples  
✅ **Side-by-Side Comparison**: View stats for both sources  
✅ **Unified Selection**: Select from both sources simultaneously  
✅ **Batch Download**: Download selected images from either source  

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs the new `apify-client` library.

### **2. Set Apify API Token**

```bash
export APIFY_API_TOKEN='your_apify_token_here'
```

Get your token from: https://console.apify.com/account/integrations

### **3. Start Application**

```bash
python frontend.py
```

### **4. Access Unified Search**

Navigate to: **http://localhost:5000/data-collection**

---

## 🎨 How It Works

### **Search Flow**

```
User Input → Google Search (25) + Pinterest Search (100) → 
CLIP Similarity Ranking → Display Both Sources → 
User Selection → Batch Download
```

### **Step-by-Step**

1. **Configure Search**
   - Event type (engagement, wedding, etc.)
   - Budget range (₹3000-5000, etc.)
   - Color theme (pastel, bold, etc.)
   - Choose Google and/or Pinterest (checkboxes)

2. **Execute Search**
   - Google: Scrapes up to 25 images
   - Pinterest: Uses Apify API for up to 100 pins
   - Both sources processed in parallel

3. **AI Similarity Ranking**
   - Downloads each result image
   - Generates CLIP embedding
   - Compares to ALL existing samples
   - Calculates similarity score (0-100%)
   - Identifies best matching sample

4. **View Comparison Stats**
   - Google: Total results, avg similarity, top similarity
   - Pinterest: Total results, avg similarity, top similarity
   - Compare which source has better matches

5. **Browse Results**
   - **All Tab**: Combined results from both sources
   - **Google Tab**: Only Google results
   - **Pinterest Tab**: Only Pinterest results
   - Each card shows similarity badge and source badge

6. **Select & Download**
   - Check boxes for relevant images
   - Select All / Deselect All controls
   - Download selected (saves to appropriate folders)

---

## 📊 UI Components

### **Source Comparison Stats**

```
┌─────────────────────────────┬─────────────────────────────┐
│ 📊 Google Results           │ 📌 Pinterest Results        │
├─────────────────────────────┼─────────────────────────────┤
│ Total Results: 25           │ Total Results: 87           │
│ Avg Similarity: 67.3%       │ Avg Similarity: 72.8%       │
│ Top Similarity: 89.2%       │ Top Similarity: 91.5%       │
└─────────────────────────────┴─────────────────────────────┘
```

**Interpretation**:
- Higher avg similarity = better overall quality
- Top similarity shows best match found
- Compare to see which source works better for your query

### **Tabbed Results View**

- **All Results**: Combined view with source badges
- **Google**: Filtered to Google only
- **Pinterest**: Filtered to Pinterest only

Each card displays:
- Image thumbnail
- **Similarity badge** (green) - percentage match
- **Source badge** (blue) - google or pinterest
- Checkbox for selection
- Best match info (event + budget)
- Pinterest: saves count

### **Selection Controls**

- **Selected count** (green text): "12 selected"
- **Select All**: Checks all visible results
- **Deselect All**: Unchecks all
- **Download Selected** (pink button): Batch download

---

## 🔧 API Reference

### **POST /unified-search**

**Request:**
```json
{
  "event_type": "wedding",
  "budget_range": "5001-8000",
  "color_theme": "pastel pink",
  "max_google_results": 25,
  "max_pinterest_results": 100,
  "include_google": true,
  "include_pinterest": true
}
```

**Response:**
```json
{
  "success": true,
  "event_type": "wedding",
  "budget_range": "5001-8000",
  "color_theme": "pastel pink",
  "google": {
    "total_results": 25,
    "avg_similarity": 0.673,
    "top_similarity": 0.892,
    "results": [
      {
        "image_url": "https://...",
        "title": "Google Images Result",
        "source": "google",
        "similarity_score": 0.892,
        "best_match": {
          "sample_event": "wedding",
          "sample_budget": "5001-8000",
          "similarity": 0.892
        }
      }
    ]
  },
  "pinterest": {
    "total_results": 87,
    "avg_similarity": 0.728,
    "top_similarity": 0.915,
    "results": [
      {
        "pin_id": "123456789",
        "pin_url": "https://pinterest.com/pin/123456789/",
        "image_url": "https://i.pinimg.com/...",
        "title": "Beautiful Wedding Welcome Board",
        "saves": 142,
        "source": "pinterest_apify",
        "similarity_score": 0.915,
        "best_match": {
          "sample_event": "wedding",
          "sample_budget": "5001-8000",
          "similarity": 0.915
        }
      }
    ]
  },
  "combined_total": 112
}
```

---

## 💡 Usage Tips

### **When to Use Google**

✅ Quick results (no API limits)  
✅ Diverse sources  
✅ Real wedding photos  
✅ DIY and budget options  

### **When to Use Pinterest**

✅ Higher quality curation  
✅ More saves = proven popularity  
✅ Better color matching  
✅ Professional designs  
✅ More results (100 vs 25)  

### **Best Practice: Use Both!**

1. Enable both sources
2. Compare avg similarity in stats
3. Browse all results
4. Select best from both sources
5. Download 10-15 total images

### **Interpreting Similarity Scores**

| Score | Interpretation | Action |
|-------|----------------|--------|
| **90-100%** | Excellent match | Definitely select |
| **75-89%** | Very good match | Review and likely select |
| **60-74%** | Good match | Review carefully |
| **40-59%** | Moderate match | Consider if unique |
| **< 40%** | Poor match | Usually skip |

---

## 🎓 Example Workflow

### **Scenario: Find Pastel Wedding Welcome Boards**

**Step 1: Configure**
```
Event: Wedding
Budget: ₹5001-8000
Color: pastel pink mint
Google: ✓ (25 results)
Pinterest: ✓ (100 results)
```

**Step 2: Execute Search**
- Click "Search & Rank by Similarity"
- Wait 1-3 minutes

**Step 3: Review Stats**
```
Google Results:
  Total: 25
  Avg Similarity: 68.2%
  Top Similarity: 87.5%

Pinterest Results:
  Total: 94
  Avg Similarity: 74.3%
  Top Similarity: 92.1%
```

**Observation**: Pinterest has higher avg similarity and more results

**Step 4: Browse Results**
- Switch to "Pinterest" tab first (better scores)
- Look for results >75% similarity
- Check if colors match (pastel pink/mint)
- Verify it's a welcome board (not invitation/cake)

**Step 5: Select**
- Select top 10 Pinterest results (>80% similarity)
- Switch to "Google" tab
- Select top 5 Google results (>75% similarity)
- Total: 15 selected

**Step 6: Download**
- Click "Download Selected"
- Wait for completion
- Verify: 15 images downloaded successfully

**Step 7: Verify**
- Check `downloaded_images/Welcome_board_decor_(5001-8000)/Wedding/user_selected/`
- Review downloaded images
- Check metadata JSON files
- Restart app to see new images in main search

**Result**: Category now has 2 (original) + 15 (new) = 17 total samples!

---

## 📈 Performance & Costs

### **Search Times**

| Component | Time |
|-----------|------|
| Google search | 5-10 seconds |
| Pinterest search (100 pins) | 30-90 seconds |
| Similarity ranking (25 Google) | 15-30 seconds |
| Similarity ranking (100 Pinterest) | 60-120 seconds |
| **Total unified search** | **2-4 minutes** |

### **Apify Costs**

- **Free tier**: 5-10 searches/month
- **Cost per search**: ~$0.02-0.05
- **100 pins**: ~$0.03
- **Monthly budget**: $5-10 for 100-200 searches

### **Optimization**

Reduce search time:
```javascript
// In data_collection.html, modify:
max_pinterest_results: 50  // Instead of 100
```

Faster ranking:
```python
# In unified_similarity_search.py
top_k=25  // Rank only top 25 instead of all
```

---

## 🐛 Troubleshooting

### **Pinterest Search Returns 0 Results**

**Cause**: Apify token not set or invalid

**Solution**:
```bash
# Check token
echo $APIFY_API_TOKEN

# Set token
export APIFY_API_TOKEN='your_token_here'

# Restart Flask
python frontend.py
```

### **Low Similarity Scores (<50%)**

**Cause**: 
- Not enough samples in database
- Query doesn't match samples
- Different event type

**Solution**:
- Add more samples to your category
- Try different color themes
- Check event type matches your samples

### **Google Search Fails**

**Cause**: Rate limiting or network issues

**Solution**:
- Wait 1-2 minutes
- Try again
- Disable Google temporarily (use Pinterest only)

### **Download Fails**

**Cause**: Image URL expired or network error

**Solution**:
- Failed downloads are logged in response
- Try downloading smaller batches (5-10 at a time)
- Some Pinterest URLs expire quickly - download soon after search

---

## 🔄 Migration from Old System

If you were using the old `scrape-pinterest` endpoint:

**Old**:
```javascript
fetch('/scrape-pinterest', {
  event_type: 'wedding',
  max_results: 25
})
```

**New**:
```javascript
fetch('/unified-search', {
  event_type: 'wedding',
  max_google_results: 25,
  max_pinterest_results: 100,
  include_google: true,
  include_pinterest: true
})
```

**Benefits of New System**:
- ✅ Google + Pinterest in one search
- ✅ Direct comparison of similarity scores
- ✅ Exactly 25 Google results (not approximate)
- ✅ Better Apify integration with `apify-client`
- ✅ Side-by-side source statistics

---

## 📝 Best Practices

### **Database Growth Strategy**

1. **Week 1**: Add 10-15 samples per event type
2. **Week 2**: Focus on under-represented budgets
3. **Week 3**: Diversify color themes
4. **Week 4**: Fill gaps based on main search performance

### **Quality Control**

- ✅ Select similarity >70% for consistency
- ✅ Manual review before downloading
- ✅ Verify it's actually a welcome board
- ✅ Check image quality (not blurry/pixelated)
- ✅ Avoid duplicates (visual check)

### **Search Optimization**

- 🎨 **Specific colors**: "pastel pink mint lavender" > "colorful"
- 💰 **Budget materials**: Let system auto-suggest based on budget
- 📝 **Short themes**: "bold gold" > "bold vibrant striking gold elegant"
- 🔄 **Iterate**: Try variations if results are poor

---

## 🎉 Summary

You now have a **powerful unified search system** that:

✅ Searches **Google** (25 results) + **Pinterest** (100 results)  
✅ Ranks **ALL results** by CLIP similarity to existing samples  
✅ Shows **comparison statistics** between sources  
✅ Provides **tabbed interface** for easy browsing  
✅ Enables **batch selection and download**  
✅ **Automatically integrates** new images into database  

**Next Steps**:
1. Set Apify token
2. Run your first unified search
3. Compare Google vs Pinterest stats
4. Select and download top matches
5. Restart app to see new samples in action!

---

**Happy Curating! 🎨📊**



