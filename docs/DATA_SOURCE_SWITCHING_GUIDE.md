# Pinterest Data Source Switching Guide

## Overview

The system now uses a **flexible data loader** that can read Pinterest results from multiple file formats:
- **Excel** (.xlsx, .xls)
- **JSON** (.json)
- **CSV** (.csv)

This makes it easy to switch between different data sources without changing any code!

---

## 🎯 Quick Start: Switching Data Sources

### Current Configuration
**Default source:** `data/Ampify Pintrest Scrapper search results.xlsx` (150 Pinterest pins)

### How to Switch

Edit the file: **`pinterest_data_loader.py`**

Find this section at the top:

```python
DATA_SOURCE_CONFIG = {
    # Primary data source (change this to switch files)
    'primary_source': 'data/Ampify Pintrest Scrapper search results.xlsx',
    
    # ... rest of config ...
}
```

**Change the `primary_source` to your file:**

```python
# Example 1: Use a different Excel file
'primary_source': 'data/new_pinterest_results.xlsx',

# Example 2: Use a JSON file
'primary_source': 'offline_pinterest_results/wedding_boards.json',

# Example 3: Use a CSV file
'primary_source': 'data/pinterest_export.csv',
```

That's it! The system will automatically detect the file type and load the data.

---

## 📁 Supported File Formats

### 1. Excel Files (.xlsx, .xls)

**Required columns:**
- `image_url` - Pinterest image URL (required)
- `description` - Pin description
- `board/name` - Board name
- `board/owner/username` - Creator username

**Example Excel structure:**
```
| image_url                           | description          | board/name | board/owner/username |
|-------------------------------------|---------------------|------------|---------------------|
| https://i.pinimg.com/originals/... | Wedding welcome sign | Products   | etsy                |
| https://i.pinimg.com/originals/... | Elegant board decor  | Bodas      | bianmazzei          |
```

**Current file:** `data/Ampify Pintrest Scrapper search results.xlsx` (150 rows)

### 2. JSON Files (.json)

**Supported structures:**

**Option A: Array of items**
```json
[
  {
    "image_url": "https://...",
    "title": "Wedding Welcome Board",
    "description": "...",
    "creator": "username",
    "pin_id": "123456789"
  }
]
```

**Option B: Object with results**
```json
{
  "results": [
    { "image_url": "...", "title": "..." }
  ]
}
```

### 3. CSV Files (.csv)

**Required columns:**
- `image_url` (required)
- `description` (optional)
- `title` (optional)
- `creator` (optional)

**Example:**
```csv
image_url,title,description,creator
https://i.pinimg.com/...,Wedding Board,Beautiful design,username1
https://i.pinimg.com/...,Engagement Board,Elegant decor,username2
```

---

## 🔧 Column Mapping Configuration

If your Excel/CSV file has different column names, update the column mapping:

```python
DATA_SOURCE_CONFIG = {
    'primary_source': 'data/your_file.xlsx',
    
    'column_mapping': {
        'image_url': 'image_url',           # Change to your column name
        'description': 'description',        # Change to your column name
        'board_name': 'board/name',         # Change to your column name
        'username': 'board/owner/username', # Change to your column name
        'pin_id': None,                     # Auto-extracted from URL
        'title': 'description',             # Use description as title
        'saves': None,                      # Not in dataset
    }
}
```

**Example: Custom column names**
```python
'column_mapping': {
    'image_url': 'ImageURL',        # Your file uses "ImageURL"
    'description': 'PinDescription', # Your file uses "PinDescription"
    'board_name': 'BoardName',      # Your file uses "BoardName"
    'username': 'Username',         # Your file uses "Username"
    # ... rest stays the same
}
```

---

## 🧪 Testing Your Data Source

After changing the data source, test it:

```bash
# Test the data loader
python3 pinterest_data_loader.py

# Test with unified search
python3 test_excel_integration.py
```

**Expected output:**
```
[data_loader] Initialized with data source: data/your_file.xlsx
[data_loader] Detected file type: excel
[data_loader] ✓ Loaded 10 results from data/your_file.xlsx
✅ Success!
```

---

## 📊 Multiple Data Sources

You can easily switch between multiple pre-configured sources:

```python
DATA_SOURCE_CONFIG = {
    # Active source (uncomment the one you want to use)
    
    # Option 1: Apify Excel export
    'primary_source': 'data/Ampify Pintrest Scrapper search results.xlsx',
    
    # Option 2: Offline JSON backup
    # 'primary_source': 'offline_pinterest_results/wedding_boards.json',
    
    # Option 3: API export CSV
    # 'primary_source': 'data/pinterest_api_export.csv',
    
    # Option 4: Custom collection
    # 'primary_source': 'data/custom_collection.xlsx',
}
```

Just **comment out** the current source and **uncomment** the one you want to use!

---

## 🔄 Fallback Chain

The system uses a smart fallback chain for Pinterest results:

1. **Pinterest API v5** (official, requires token) ⬇️
2. **Data Loader** (Excel/JSON/CSV - configured source) ⬇️
3. **Apify** (backup, requires paid subscription)

This means:
- If Pinterest API fails → loads from your configured file
- If file load fails → tries Apify (if configured)
- Always shows results from the first successful source

---

## 💡 Use Cases

### Use Case 1: Apify Export (Current Setup)
You have 150 pins from Apify's Pinterest scraper export.

```python
'primary_source': 'data/Ampify Pintrest Scrapper search results.xlsx'
```

✅ Already configured!

### Use Case 2: Multiple Scraped Files
You've scraped Pinterest multiple times with different queries.

```python
# Switch between them as needed:
'primary_source': 'data/wedding_boards_scrape_1.xlsx'  # 200 pins
# 'primary_source': 'data/wedding_boards_scrape_2.xlsx'  # 300 pins
# 'primary_source': 'data/all_events_scrape.xlsx'       # 500 pins
```

### Use Case 3: API Export
You got approval for Pinterest API and exported results.

```python
'primary_source': 'data/pinterest_api_export.json'
```

### Use Case 4: Manual Curation
You manually curated a collection in Excel.

```python
'primary_source': 'data/curated_welcome_boards.xlsx'
```

---

## 📝 Best Practices

1. **Keep original files:** Always keep backups of your data files
2. **Use descriptive names:** Name files with query/date: `wedding_elegant_20251029.xlsx`
3. **Test first:** Always test with `python3 pinterest_data_loader.py` after changing sources
4. **Check column names:** Verify your file has the required columns
5. **Limit file size:** For Excel files, keep under 10,000 rows for performance

---

## ⚙️ Advanced Configuration

### Auto-detect vs Manual Type

**Auto-detect (default):**
```python
'file_type': 'auto',  # Detects from file extension
```

**Manual override:**
```python
'file_type': 'excel',  # Force Excel parsing
# 'file_type': 'json',   # Force JSON parsing
# 'file_type': 'csv',    # Force CSV parsing
```

### Query Filtering

Results are automatically filtered by the search query. To adjust sensitivity:

Edit `pinterest_data_loader.py`, find `_filter_by_query()`:

```python
# Current: 50% word match required
if matches >= len(query_words) * 0.5:  # At least 50% match

# More strict: 80% match required
if matches >= len(query_words) * 0.8:  # At least 80% match

# Less strict: 30% match required
if matches >= len(query_words) * 0.3:  # At least 30% match
```

---

## 🚀 Frontend Integration

The data source change is **automatically reflected** in the frontend!

No changes needed to:
- `frontend.py`
- `templates/data_collection.html`
- `unified_similarity_search.py`

Just change the data source in `pinterest_data_loader.py` and restart the Flask server:

```bash
python3 frontend.py
```

Then visit: http://localhost:5000/data-collection

Pinterest results will now come from your configured file! 🎉

---

## 🐛 Troubleshooting

### Problem: "Data source not found"
**Solution:** Check the file path. Use absolute path or ensure the file is in the correct location:
```python
'primary_source': '/home/sanaat/Desktop/WEDDink/data/your_file.xlsx'
```

### Problem: "No results loaded"
**Solution:** 
1. Check if file has data: `python3 -c "import pandas as pd; print(len(pd.read_excel('data/your_file.xlsx')))"`
2. Verify column names match the mapping
3. Check if images URLs are valid

### Problem: "KeyError: image_url"
**Solution:** Update column mapping to match your file's column names

### Problem: Results don't match query
**Solution:** Adjust query filtering sensitivity (see Advanced Configuration)

---

## 📊 Current Statistics

**Active Data Source:** `data/Ampify Pintrest Scrapper search results.xlsx`
- **Total pins:** 150
- **File type:** Excel (.xlsx)
- **Columns:** image_url, description, board/name, board/owner/username, + 119 metadata fields
- **Filter query:** Searches in title and description

**Sample results from test:**
- Query: "wedding elegant"
- Filtered results: 7 pins
- Top similarity: 0.730
- Avg similarity: 0.663

---

## ✅ Summary

**To switch data sources:**

1. Edit `pinterest_data_loader.py`
2. Change `DATA_SOURCE_CONFIG['primary_source']` to your file
3. Test with `python3 pinterest_data_loader.py`
4. Restart Flask server (if running)

**That's it!** The system will automatically:
- Detect file type
- Load and format data
- Rank by similarity
- Display in the UI

🎉 **Easy switching, no code changes needed!**






