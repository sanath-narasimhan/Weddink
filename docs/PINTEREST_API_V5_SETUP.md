# 🎯 Pinterest API v5 Setup Guide

## ✅ Official Pinterest API (FREE - 1,000 requests/month)

Based on: [Pinterest API v5 Documentation](https://developers.pinterest.com/docs/api/v5/introduction)

---

## 🚀 Quick Setup (5 Minutes)

### **Step 1: Create Pinterest App**

1. Go to: **https://developers.pinterest.com/apps/**
2. Click "**Create app**"
3. Fill in details:
   ```
   App name: WEDDink Search
   Description: Wedding welcome board image curation tool
   App website: https://localhost:5000
   ```
4. Accept Terms of Service
5. Click "**Create**"

### **Step 2: Generate Access Token**

1. In your app dashboard, go to "**OAuth & scopes**" tab
2. Under "**Scopes**", select:
   - ✅ `pins:read` - Required for searching pins
   - ✅ `boards:read` - Optional (for board info)
   - ✅ `user_accounts:read` - Optional (for user info)
3. Click "**Generate token**"
4. Copy the access token (starts with `pina_`)

**Example token format:**
```
pina_ABCD1234EFGH5678IJKL9012MNOP3456QRST7890
```

### **Step 3: Set Environment Variable**

```bash
export PINTEREST_API_TOKEN='pina_your_actual_token_here'
```

**To make it permanent**, add to your shell config:

```bash
# For bash
echo 'export PINTEREST_API_TOKEN="pina_your_token"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export PINTEREST_API_TOKEN="pina_your_token"' >> ~/.zshrc
source ~/.zshrc
```

### **Step 4: Test the API**

```bash
python3 pinterest_api_v5_scraper.py
```

**Expected output:**
```
✅ Token valid!
   Username: your_username
   Account Type: BUSINESS (or PERSONAL)
✅ Search successful!
   Total results: 10
```

### **Step 5: Restart Your App**

```bash
python3 frontend.py
```

Now open: **http://localhost:5000/data-collection**

---

## 📊 API Features & Limits

### **Free Tier (No Credit Card Required):**
- ✅ **1,000 API calls per month**
- ✅ Up to **250 pins per search**
- ✅ Full access to search API
- ✅ Image URLs and metadata
- ✅ Save counts and creator info

### **What You Can Do:**
- 1,000 searches/month = **33 searches per day**
- 250 pins per search = **up to 250,000 pins/month**
- More than enough for database building!

### **Rate Limits:**
- 10 requests per second
- 1,000 requests per day (free tier)
- Resets daily at midnight UTC

---

## 🔍 API Endpoints Used

### **1. Search Pins** (`GET /v5/search/pins`)

**Parameters:**
- `query` - Search query string (required)
- `page_size` - Results per page (1-250, default 25)
- `bookmark` - Pagination cursor (optional)

**Response:**
```json
{
  "items": [
    {
      "id": "pin_id",
      "title": "Pin title",
      "description": "Pin description",
      "media": {
        "images": {
          "originals": {"url": "https://..."}
        }
      },
      "pin_metrics": {"saves": 142}
    }
  ],
  "bookmark": "next_page_cursor"
}
```

### **2. Get User Info** (`GET /v5/user_account`)

Used to verify token validity:
```json
{
  "username": "your_username",
  "profile_image": "https://...",
  "account_type": "BUSINESS"
}
```

---

## 🎨 Integration with Your App

### **Automatic Integration:**

Your app is **already configured** to use Pinterest API v5!

1. Set `PINTEREST_API_TOKEN`
2. Restart `python3 frontend.py`
3. Pinterest search automatically uses API v5

### **Fallback Chain:**

```
Pinterest API v5 → Apify (if configured) → Google only
     ↓                   ↓                      ↓
  Primary            Backup                Last resort
  (Free)            (Paid)                 (Always works)
```

---

## 🧪 Testing

### **Quick Test:**
```bash
# Set token
export PINTEREST_API_TOKEN='pina_your_token'

# Test API
python3 pinterest_api_v5_scraper.py
```

### **Full System Test:**
```bash
# Start app
python3 frontend.py

# In browser:
# → http://localhost:5000/data-collection
# → Check both Google and Pinterest
# → Search
# → Should see Pinterest results!
```

---

## ❓ Troubleshooting

### **Error: "Invalid API token"**

**Causes:**
- Token expired
- Token copied incorrectly
- Missing `pins:read` scope

**Solutions:**
1. Regenerate token in Pinterest app dashboard
2. Make sure token starts with `pina_`
3. No spaces or quotes in token
4. Check scopes include `pins:read`

### **Error: "Rate limit exceeded"**

**Cause:** Exceeded 1,000 requests/month or 10 req/sec

**Solutions:**
- Wait for daily/monthly reset
- Reduce search frequency
- Upgrade to paid tier (if needed)

### **Error: "No results found"**

**Causes:**
- Query has no matching pins
- Restrictive filters

**Solutions:**
- Try broader search terms
- Remove filters
- Check query spelling

### **Token Not Persisting**

**Check if set:**
```bash
echo $PINTEREST_API_TOKEN
```

**If empty, add to shell config:**
```bash
echo 'export PINTEREST_API_TOKEN="pina_your_token"' >> ~/.bashrc
source ~/.bashrc
```

---

## 📈 Expected Results

### **Typical Search:**
```
Query: "wedding welcome board pastel"

Google Search:
  ✓ 25 results in 5 seconds

Pinterest API v5:
  ✓ 100 results in 8 seconds
  ✓ Method: pinterest_api_v5
  ✓ Avg similarity: 74.2%

Total: 125 results with similarity scores
```

---

## 💡 Pro Tips

### **Optimize Your Searches:**

1. **Specific keywords work best:**
   - Good: "acrylic wedding welcome board gold"
   - Bad: "board"

2. **Use color terms:**
   - "pastel pink lavender welcome board"
   - "bold red gold wedding sign"

3. **Include style descriptors:**
   - "minimalist", "luxury", "rustic", "modern"

### **Monitor Your Usage:**

Check usage in Pinterest Developer Dashboard:
- Go to: https://developers.pinterest.com/apps/
- Select your app
- View "Analytics" tab
- Monitor API calls remaining

---

## 🆚 Comparison

| Feature | Pinterest API v5 | Apify (Paid) | Google Only |
|---------|-----------------|--------------|-------------|
| **Cost** | FREE | $10-50/mo | FREE |
| **Setup** | 5 min | 2 min | 0 min |
| **Results** | Up to 250 | Up to 100 | Up to 25 |
| **Monthly limit** | 1,000 searches | Unlimited | Unlimited |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Official** | ✅ Yes | ✅ Yes | ✅ Yes |

---

## 🎉 Summary

### **What You Get:**

✅ **FREE** Pinterest API access  
✅ **1,000 searches/month** (33/day)  
✅ Up to **250 results** per search  
✅ **Official API** - no TOS violations  
✅ **High reliability** and quality  
✅ Combined with Google: **275 total results!**

### **Setup Checklist:**

- [ ] Created Pinterest app
- [ ] Generated access token
- [ ] Set `PINTEREST_API_TOKEN` env var
- [ ] Tested with `python3 pinterest_api_v5_scraper.py`
- [ ] Restarted app: `python3 frontend.py`
- [ ] Verified Pinterest results appear in UI

---

## 📞 Support

### **Official Documentation:**
- API Reference: https://developers.pinterest.com/docs/api/v5/
- Developer Forum: https://developers.pinterest.com/community/
- App Dashboard: https://developers.pinterest.com/apps/

### **Local Testing:**
```bash
# Test API connection
python3 pinterest_api_v5_scraper.py

# Check environment variable
echo $PINTEREST_API_TOKEN

# View app setup guide
cat PINTEREST_API_V5_SETUP.md
```

---

**Ready to use! Set your token and start searching!** 🚀






