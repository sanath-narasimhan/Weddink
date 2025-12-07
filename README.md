## WEDDink - Welcome Board Search & Mood Board Generator

AI-powered welcome board discovery platform for Indian wedding events. Combines CLIP-based visual search with multi-source web scraping and interactive data collection.

### 🎯 Key Features

- **Multi-Source Search**: Google Images, Bing, Pinterest
- **AI-Powered Ranking**: CLIP embeddings for semantic similarity
- **Budget-Aware**: ₹3000-5000, ₹5001-8000, ₹8001-15000
- **Event Types**: Engagement, Haldi, Mehendi, Sangeet, Wedding, Reception
- **Color Theme Matching**: Enhanced Pinterest search with color emphasis
- **PDF Mood Boards**: Professional client-ready presentations
- **🆕 Interactive Data Collection**: Scrape, rank, and curate Pinterest images

### 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start Application**
```bash
python frontend.py
```

3. **Access**
- Main Search: http://localhost:5000
- Data Collection: http://localhost:5000/data-collection

### 📚 Documentation

- **Main Search**: See usage in web interface
- **[Data Collection System](README_DATA_COLLECTION.md)**: Complete guide for scraping and curating Pinterest images

### 🆕 Data Collection (NEW!)

Expand your welcome board database by:
1. Scraping Pinterest via [Apify](https://console.apify.com/actors/NmOWmFiz40AgzJNxT/input) (25+ results per query)
2. Ranking by CLIP similarity to existing samples
3. Selecting relevant images interactively
4. Downloading to organized database structure

**Setup**: Set `APIFY_API_TOKEN` environment variable  
**Read More**: [README_DATA_COLLECTION.md](README_DATA_COLLECTION.md)

### 🎨 Tech Stack

- **Backend**: Flask, Python 3.9+
- **AI/ML**: PyTorch, OpenAI CLIP, open-clip-torch
- **Web Scraping**: Requests, Selenium, Apify API
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow

### Notes

- Requires internet access. Respect Pinterest's Terms of Service.
- CLIP model downloads automatically on first run (~350MB)
- Sample database included (36 images across all categories)


