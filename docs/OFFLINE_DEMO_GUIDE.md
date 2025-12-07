# 🎬 Offline Demo Mode - Use Saved Apify Results

## 📋 Problem

- Pinterest API needs approval (pending)
- Apify requires payment
- Need to demo the system now

## ✅ Solution: Offline Mode

Use **pre-downloaded Apify search results** saved as JSON files while waiting for Pinterest API approval.

---

## 🚀 Quick Setup (2 Minutes)

### **Step 1: Run any Apify Pinterest search** (one-time)

Option A: Use Apify Console
1. Go to: https://console.apify.com/actors/NmOWmFiz40AgzJNxT
2. Run a search (may use free trial if available)
3. Download results as JSON

Option B: If you have existing Apify results
- Use results from previous test runs
- Export from Apify dashboard

### **Step 2: Save results to offline directory**

```bash
# Create directory
mkdir -p offline_pinterest_results

# Save your Apify JSON results
# Example filename: wedding_welcome_board.json
```

### **Step 3: Format the JSON**

Your JSON should be in one of these formats:

**Format 1: Direct array**
```json
[
  {
    "id": "123456789",
    "url": "https://pinterest.com/pin/123456789/",
    "image": "https://i.pinimg.com/originals/...",
    "title": "Beautiful Welcome Board",
    "saves": 142
  }
]
```

**Format 2: Wrapped object**
```json
{
  "results": [
    {
      "pin_id": "123456789",
      "image_url": "https://i.pinimg.com/...",
      "title": "Welcome Board"
    }
  ]
}
```

The system automatically handles both formats!

### **Step 4: Test it**

```bash
python3 offline_pinterest_loader.py
```

**Expected output:**
```
✅ Success!
   Results: 25
   Source: offline_pinterest_results/wedding_welcome_board.json
```

### **Step 5: Use in your app**

```bash
python3 frontend.py
```

The app **automatically uses offline results** if Pinterest API fails!

---

## 📁 File Naming Convention

Save files with query-based names:

```
offline_pinterest_results/
├── wedding_welcome_board.json
├── engagement_welcome_board_pastel.json
├── haldi_welcome_sign_yellow.json
├── mehendi_welcome_board_green.json
└── reception_entrance_sign.json
```

The system matches queries to filenames automatically!

---

## 🎨 How It Works

### **Automatic Fallback Chain:**

```
1. Try Pinterest API v5 (if token set)
       ↓ (fails if pending approval)
2. Try Offline JSON files (demo mode)
       ↓ (fails if no file found)
3. Try Apify (if paid subscription)
       ↓ (fails if not configured)
4. Fall back to Google only
```

### **Smart Query Matching:**

Query: `"wedding welcome board pastel"`

Searches for (in order):
1. `wedding_welcome_board_pastel.json` (exact match)
2. `wedding_welcome_board.json` (partial match)
3. Any file with 2+ matching words

---

## 🧪 Testing

### **Test 1: Verify offline loader**
```bash
python3 offline_pinterest_loader.py
```

### **Test 2: Create sample file**
```python
from offline_pinterest_loader import create_sample_offline_file
create_sample_offline_file()
```

### **Test 3: Full system test**
```bash
# 1. Start app
python3 frontend.py

# 2. In browser
# → http://localhost:5000/data-collection
# → Search for "wedding welcome board"
# → Should see offline results!
```

---

## 💡 Creating Offline Files from Apify

### **Method 1: Copy from Apify Console**

1. Run search in Apify console
2. Go to "Storage" → "Datasets"
3. Click your dataset
4. Download as JSON
5. Save to `offline_pinterest_results/`

### **Method 2: Use Apify API (if you have credits)**

```python
from apify_pinterest_scraper import ApifyPinterestScraper
from offline_pinterest_loader import OfflinePinterestLoader

# Run Apify search (uses your credits)
scraper = ApifyPinterestScraper()
result = scraper.scrape_pinterest_search("wedding welcome board", max_pins=50)

# Save for offline use
if result['success']:
    loader = OfflinePinterestLoader()
    loader.save_results("wedding welcome board", result['results'])
    print("✅ Saved for offline use!")
```

### **Method 3: Export existing results**

If you've already run Apify searches:
1. Find the dataset ID in Apify console
2. Export as JSON
3. Rename and save to offline directory

---

## 📊 Demo Workflow

### **Prepare Demo (One-time)**

```bash
# 1. Get some Apify results (even from free trial)
# Download 3-4 searches for different queries

# 2. Save to offline directory
mkdir -p offline_pinterest_results
cp ~/Downloads/apify_results.json offline_pinterest_results/wedding_welcome_board.json

# 3. Test
python3 offline_pinterest_loader.py
```

### **Run Demo**

```bash
# Start app
python3 frontend.py

# Open browser
# → http://localhost:5000/data-collection
# → Search
# → Works even without Pinterest API!
```

### **What Users See:**

```
Google Results:
  ✓ 25 results
  ✓ Avg Similarity: 67.3%

Pinterest Results:
  ✓ 50 results (from offline file)
  ✓ Avg Similarity: 74.8%
  ✓ Source: offline_pinterest

Total: 75 results with similarity scores!
```

Users get **full functionality** even without Pinterest API! 🎉

---

## 📋 Example Offline File

**File: `offline_pinterest_results/wedding_welcome_board.json`**

```json
{
  "query": "wedding welcome board",
  "saved_at": "2025-10-29T10:30:00",
  "total_results": 50,
  "results": [
    {
      "pin_id": "123456789",
      "pin_url": "https://www.pinterest.com/pin/123456789/",
      "image_url": "https://i.pinimg.com/originals/ab/cd/ef/abcdef.jpg",
      "title": "Elegant Wedding Welcome Board with Gold Calligraphy",
      "description": "Beautiful acrylic welcome sign for wedding entrance",
      "creator": "weddingdecor",
      "saves": 142
    },
    {
      "pin_id": "987654321",
      "pin_url": "https://www.pinterest.com/pin/987654321/",
      "image_url": "https://i.pinimg.com/originals/12/34/56/123456.jpg",
      "title": "Rustic Wooden Welcome Sign",
      "description": "DIY welcome board with floral arrangements",
      "creator": "rusticweddings",
      "saves": 89
    }
  ]
}
```

---

## 🎯 Benefits

### **For Demo/Development:**
✅ Works immediately (no API approval needed)  
✅ No API costs  
✅ Reproducible results  
✅ Full similarity scoring  
✅ All UI features work  

### **For Production (later):**
✅ Seamless transition to live Pinterest API  
✅ No code changes needed  
✅ Offline files as backup/cache  
✅ Faster for repeated queries  

---

## 🔄 Transition Plan

### **Phase 1: Now (API Pending)**
```
Use: Offline JSON files
Status: Demo mode, full functionality
```

### **Phase 2: API Approved**
```
1. Get Pinterest API approval
2. Set PINTEREST_API_TOKEN
3. Restart app
4. Automatically uses live API
5. Falls back to offline if needed
```

### **Phase 3: Production**
```
1. Live Pinterest API (primary)
2. Offline files (cache for common queries)
3. Apify (optional, if budget allows)
```

---

## ❓ FAQ

### **Q: How many results should I save offline?**
**A:** 50-100 per query is good for demo. Covers most use cases.

### **Q: Can I use multiple offline files?**
**A:** YES! Create one file per query/theme:
- `wedding_welcome_board.json`
- `engagement_welcome_board_pastel.json`
- etc.

### **Q: What if I don't have Apify results?**
**A:** Use the sample creator:
```python
from offline_pinterest_loader import create_sample_offline_file
create_sample_offline_file()
```

### **Q: Will this work with Pinterest API later?**
**A:** YES! The system automatically uses live API when available, offline as fallback.

### **Q: Can I mix offline and live results?**
**A:** Not simultaneously, but the fallback chain ensures best available source is used.

---

## 🎉 Summary

### **Problem:**
- ❌ Pinterest API pending approval
- ❌ Apify requires payment
- ❌ Can't demo Pinterest search

### **Solution:**
- ✅ Use saved Apify results as JSON
- ✅ System automatically loads offline files
- ✅ Full functionality without API
- ✅ Seamless transition when API approved

### **Setup:**
1. Save Apify results to `offline_pinterest_results/`
2. Name files based on queries
3. Restart app
4. **Works immediately!**

---

## 🚀 Quick Start Commands

```bash
# Test offline loader
python3 offline_pinterest_loader.py

# Create sample file
python3 -c "from offline_pinterest_loader import create_sample_offline_file; create_sample_offline_file()"

# Start app (uses offline mode automatically)
python3 frontend.py
```

---

**Demo-ready now, production-ready when API approved!** 🎬






