<!-- 7418c36e-d9e7-4a8f-88a8-4ef4e3904ad2 cef21c95-632b-4005-ba2b-074541f854d1 -->
# Improve Welcome Board Image Search Quality

## Goal

Enhance the search functionality to return more accurate, realistic welcome board images while filtering out drawings, renderings, and non-welcome-board content.

## Changes

### 1. Pinterest Image Extraction (`backend_search.py`)

**Current Issue**: Pinterest returns only pin URLs, not actual image URLs

**Solution**:

- Import existing `get_pinterest_image_url` function from `quick_reverse_search.py` or `download_pinterest_images.py`
- Modify `_web_search_pinterest` to extract actual image URLs using Pinterest widgets API
- Add fallback to skip Pinterest results if image extraction fails (per user requirement)
```python
# In backend_search.py, add:
def get_pinterest_image_url(pin_id: str) -> Optional[str]:
    """Extract actual image URL from Pinterest pin using widgets API"""
    url = f"https://widgets.pinterest.com/v3/pidgets/pins/info/?pin_ids={pin_id}"
    # ... implementation from existing files

# In _web_search_pinterest, replace pin_url with actual image URL:
image_url = get_pinterest_image_url(pin_id)
if image_url:  # Only include if we can extract the image
    results.append({'image_url': image_url, ...})
```


### 2. Enhanced Keyword Filtering (`backend_search.py`)

**Lines**: 252-263, 300-379

**Changes**:

- Expand `skip_terms` list to exclude drawings/renderings:
  - Add: `'sketch'`, `'drawing'`, `'render'`, `'rendering'`, `'illustration'`, `'vector'`, `'clipart'`, `'graphic'`, `'design'`, `'template'`, `'mockup'`, `'cartoon'`, `'anime'`, `'art'`, `'painting'`
- Strengthen welcome board terms to prioritize realistic photos:
  - Add: `'photo'`, `'real'`, `'actual'`, `'diy'`, `'wedding'`, `'event'`, `'decor'`
- Apply consistent filtering across Google, Bing, and Pinterest

### 3. Increase Result Depth (`backend_search.py`)

**Lines**: 223, 300, 382, 438

**Changes**:

- Increase `max_results` from 5 to 20 per source
- Update `search_welcome_boards` to fetch 20 results per source
- Add post-filtering to return top 15 after quality filtering
- Keep final output at manageable size (8-10 per source after filtering)

### 4. Multiple Search Query Variations (`backend_search.py`)

**Lines**: 437-530

**Changes**:

- Create 2-3 query variations per request with different keyword orders:
  - Query 1: `"{event} welcome board {colors} {budget_keywords}"`
  - Query 2: `"welcome sign {event} {budget_keywords} {colors}"`
  - Query 3: `"{event} entrance sign board {colors} photo"`
- Combine and deduplicate results from all queries
- Prioritize results that appear in multiple queries

### 5. Result Scoring and Ranking (`backend_search.py`)

**New Function**: `_score_and_rank_results`

**Implementation**:

- Score each result based on:
  - URL contains wedding vendor domains (+3): weddingwire, shaadisaga, wedmegood, etc.
  - URL contains welcome board terms (+2): welcome, board, sign, display
  - URL contains event type (+2)
  - URL contains realistic photo indicators (+1): photo, diy, real
  - URL contains exclusion terms (-5): sketch, drawing, render, etc.
- Sort results by score before returning

### 6. Image Content Validation (`backend_search.py`)

**New Function**: `_validate_image_content`

**Implementation** (lightweight approach):

- Check image dimensions: realistic welcome boards are typically landscape (width > height)
- Exclude very small images (< 300px width)
- Exclude very large images (> 5MB) as they're often high-res renders
- Optional: Check image aspect ratio (prefer 3:2, 4:3, 16:9)

### 7. Update Frontend to Handle More Results (`templates/index.html`)

**Lines**: 520-530

**Changes**:

- Update grid layout to handle 8-10 results per source (instead of 5)
- Add loading state for longer search times
- Improve error handling for failed image loads

## Testing

- Test with each event type + budget + color combination
- Verify Pinterest images are actual photos (not just pin links)
- Confirm no drawings/renderings in results
- Validate that top results are realistic welcome boards
- Check that search completes within 30 seconds

## Expected Improvements

- Pinterest results will show actual images (or be excluded)
- Google/Bing results will be 2-3x more numerous with better filtering
- Drawings, renderings, and irrelevant content filtered out
- More relevant welcome board photos from wedding vendor sites
- Better ranking of realistic photos over generic stock images

### To-dos

- [ ] Add Pinterest image URL extraction using widgets API and filter out pins where extraction fails
- [ ] Expand skip_terms list to exclude drawings, renderings, illustrations, and add realistic photo indicators
- [ ] Increase max_results to 20 per source and implement post-filtering to return top 8-10
- [ ] Create 2-3 search query variations with different keyword orders and combine results
- [ ] Implement result scoring based on URL patterns, wedding vendor domains, and content indicators
- [ ] Add lightweight image content validation for dimensions and aspect ratio
- [ ] Test search quality across all event types and verify realistic photo results