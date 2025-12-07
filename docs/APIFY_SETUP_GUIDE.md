# 🔑 Apify API Token Setup Guide

## ✅ Current Status

- ✅ **apify-client library**: INSTALLED
- ❌ **APIFY_API_TOKEN**: NOT SET (this is why Pinterest returns 0 results)

---

## 🚀 Quick Setup (3 Steps)

### **Step 1: Get Your API Token**

1. Go to: **https://console.apify.com/account/integrations**
2. Log in (or create free account if needed)
3. Copy your **Personal API token**

Example token format: `apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### **Step 2: Set the Token**

Choose **ONE** method:

#### **Option A: Quick Test (Temporary)**
```bash
export APIFY_API_TOKEN='apify_api_your_token_here'
```
*Note: This only works for current terminal session*

#### **Option B: Permanent Setup (Recommended)**
```bash
# Add to your shell config
echo 'export APIFY_API_TOKEN="apify_api_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

---

### **Step 3: Verify Setup**

```bash
# Test the setup
python3 test_apify_setup.py
```

**Expected output:**
```
✅ PASSED: API token found
✅ PASSED: apify-client library is installed
✅ PASSED: Scraper initialized successfully
✅ All checks passed! Pinterest scraping should work.
```

---

## 🧪 Test Pinterest Search

After setting your token, test with a small search:

```bash
python3 -c "
from apify_pinterest_scraper import ApifyPinterestScraper

scraper = ApifyPinterestScraper()
result = scraper.scrape_pinterest_search('wedding welcome board', max_pins=5)

print(f'Success: {result[\"success\"]}')
print(f'Results: {result[\"total_results\"]}')
if result['results']:
    print(f'First result: {result[\"results\"][0][\"title\"]}')
"
```

**Expected output:**
```
Success: True
Results: 5
First result: Beautiful Wedding Welcome Board
```

---

## 🔄 Restart Your App

After setting the token:

```bash
# Restart Flask
python3 frontend.py
```

Then open: **http://localhost:5000/data-collection**

---

## 📊 What This Fixes

With the token set, you'll now get:
- ✅ Pinterest results (up to 100 pins)
- ✅ Similarity scores for Pinterest images
- ✅ Side-by-side comparison: Google (25) vs Pinterest (100)
- ✅ Full download and curation capabilities

---

## ❓ Troubleshooting

### **"Invalid API token" error**

1. Check token format (should start with `apify_api_`)
2. No spaces or quotes in token
3. Token not expired (check Apify console)

### **"Rate limit exceeded" error**

Free tier limits:
- 5-10 searches per month
- Wait 24 hours or upgrade account

### **Token not persisting**

If token disappears after closing terminal:
```bash
# Check if it's in your shell config
grep APIFY_API_TOKEN ~/.bashrc

# If not found, add it:
echo 'export APIFY_API_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `./setup_apify.sh` | Show setup instructions |
| `python3 test_apify_setup.py` | Verify setup |
| `echo $APIFY_API_TOKEN` | Check if token is set |
| `python3 frontend.py` | Start app |

---

## 💡 Why You Need This

Without the API token:
- ❌ Pinterest returns **0 results**
- ❌ Unified search only shows Google results
- ❌ No Pinterest similarity scoring

With the API token:
- ✅ Pinterest returns **up to 100 results**
- ✅ Full similarity scoring
- ✅ Better quality curation
- ✅ More comprehensive searches

---

## 📞 Need Help?

1. **Check status**: `python3 test_apify_setup.py`
2. **View guide**: `cat APIFY_SETUP_GUIDE.md`
3. **Setup help**: `./setup_apify.sh`

---

**Ready? Set your token and run: `python3 test_apify_setup.py`** 🚀


