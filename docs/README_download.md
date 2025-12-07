# Pinterest Image Downloader

Downloads Pinterest images from a Google Sheet CSV file and organizes them by price category and event type.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Your CSV should have this format:
   - Price categories as headers (e.g., "Welcome board decor (3000-5000)")
   - Column 1: Row number
   - Column 2: Pinterest URL (pin.it links)
   - Column 4: Event type (e.g., "Engagement", "Wedding", "Reception")

## Usage

```bash
python download_pinterest_images.py your_sheet.csv [output_folder]
```

Example:
```bash
python download_pinterest_images.py "data/Weddink 0.1 - Welcome board decor.csv" downloaded_images
```

## Output Structure

```
downloaded_images/
├── Welcome board decor (3000-5000)/
│   ├── Engagement/
│   │   └── provided_sample/
│   │       └── provided_sample_123456789_sample_2.jpg
│   ├── Wedding/
│   │   └── provided_sample/
│   │       └── provided_sample_987654321_sample_9.jpg
│   └── Reception/
│       └── provided_sample/
│           └── provided_sample_456789123_sample_11.jpg
├── Welcome board decor (5001-8000)/
│   └── ...
└── download_results.json
```

## Features

- **Automatic pin ID extraction** from various Pinterest URL formats (including pin.it short links)
- **High-quality image downloads** using Pinterest's widgets API
- **Organized folder structure** by price category, event type, and source
- **Source labeling** - distinguishes provided samples from future downloads
- **Duplicate detection** - skips already downloaded images
- **Progress tracking** with detailed logging
- **Error handling** with comprehensive error reporting
- **Results summary** saved to JSON file

## Notes

- Images are saved as JPG format
- Filenames include pin ID and title (if available)
- Invalid filename characters are replaced with underscores
- The script respects Pinterest's rate limits with reasonable delays
