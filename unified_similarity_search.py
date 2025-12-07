#!/usr/bin/env python3
"""
Unified Similarity Search
Searches both Google and Pinterest, then ranks all results by similarity to existing samples
"""

import os
import re
import requests
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from similarity_ranker import SimilarityRanker

# Pinterest API v5 (official, free tier available)
from pinterest_api_v5_scraper import PinterestAPIv5, create_search_keywords

# Flexible data loader for Excel/JSON/CSV files (configured in pinterest_data_loader.py)
from pinterest_data_loader import PinterestDataLoader

# Try Apify as backup
try:
    from apify_pinterest_scraper import ApifyPinterestScraper
    APIFY_AVAILABLE = True
except:
    APIFY_AVAILABLE = False

def log(msg: str):
    print(f"[unified] {msg}")

def _headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def search_google_images(query: str, max_results: int = 25) -> List[Dict]:
    """
    Search Google Images and return up to max_results.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 25)
        
    Returns:
        List of image results with URLs and metadata
    """
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
        headers = _headers()
        resp = requests.get(search_url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            log(f"Google search failed with status {resp.status_code}")
            return []
        
        html = resp.text
        results = []
        
        # Extract image URLs - multiple patterns to capture more results
        img_patterns = [
            r'https://[^\s"<>]+\.(?:jpg|jpeg|png|webp|gif)',
            r'"ou":"([^"]+)"',
            r'"ru":"([^"]+)"',
            r'data-src="([^"]+)"',
            r'src="([^"]+)"',
            r'"original":"([^"]+)"',
            r'"url":"([^"]+)"'
        ]
        
        seen_urls = set()
        
        # Enhanced filtering terms
        skip_terms = [
            '.svg', 'icon', 'branding', 'gstatic.com/bar', 
            'googleusercontent.com/bar', 'logo', 'data:',
            'bing.com/rp', 'ssl.gstatic.com/gb', 'invitation',
            'card', 'cake', 'cake-topper', 'favor', 'gift',
            'sketch', 'drawing', 'render', 'rendering', 'illustration', 
            'vector', 'clipart', 'graphic', 'template', 
            'mockup', 'cartoon', 'anime', 'art', 'painting'
        ]
        
        for pattern in img_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if match and match not in seen_urls and match.startswith('http'):
                    # Filter out unwanted content
                    if not any(skip in match.lower() for skip in skip_terms):
                        if any(img_ext in match.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            seen_urls.add(match)
                            
                            results.append({
                                'image_url': match,
                                'title': f'Google Images Result',
                                'source': 'google',
                                'url': match
                            })
                            
                            if len(results) >= max_results:
                                break
            
            if len(results) >= max_results:
                break
        
        log(f"Google search found {len(results)} images")
        return results[:max_results]
    
    except Exception as e:
        log(f"Google search failed: {e}")
        return []


class UnifiedSimilaritySearch:
    """
    Unified search system that combines Google and Pinterest results
    and ranks them all by similarity to existing samples.
    """
    
    def __init__(self, local_images_dir: str = "downloaded_images"):
        """Initialize with similarity ranker."""
        self.ranker = SimilarityRanker(local_images_dir=local_images_dir)
        
        # Use official Pinterest API v5 (free tier: 1000 requests/month)
        self.pinterest_api = PinterestAPIv5()
        
        # Flexible data loader for Excel/JSON/CSV (configured in pinterest_data_loader.py)
        self.data_loader = PinterestDataLoader()
        
        # Keep Apify as backup if available and configured
        if APIFY_AVAILABLE:
            try:
                self.apify_scraper = ApifyPinterestScraper()
            except:
                self.apify_scraper = None
        else:
            self.apify_scraper = None
    
    def search_and_rank(
        self,
        event_type: str,
        budget_range: str,
        color_theme: str,
        max_google_results: int = 25,
        max_pinterest_results: int = 100,
        include_google: bool = True,
        include_pinterest: bool = True
    ) -> Dict:
        """
        Search both Google and Pinterest, then rank all by similarity.
        
        Args:
            event_type: Event type (wedding, engagement, etc.)
            budget_range: Budget range (3000-5000, etc.)
            color_theme: Color theme (pastel, bold, etc.)
            max_google_results: Max Google results (default: 25)
            max_pinterest_results: Max Pinterest results (default: 100)
            include_google: Whether to include Google search (default: True)
            include_pinterest: Whether to include Pinterest search (default: True)
            
        Returns:
            Dict with ranked results from both sources
        """
        log(f"Starting unified search: {event_type} | {budget_range} | {color_theme}")
        
        # Create search queries
        base_query = f"{event_type} welcome board {color_theme}"
        pinterest_keywords = create_search_keywords(event_type, budget_range, color_theme)
        
        # Collect results from both sources
        google_results = []
        pinterest_results = []
        
        # Google Search
        if include_google:
            log(f"Searching Google (max {max_google_results} results)...")
            google_results = search_google_images(base_query, max_results=max_google_results)
            log(f"✓ Google: {len(google_results)} results")
        
        # Pinterest Search (with fallback chain)
        if include_pinterest:
            pinterest_success = False
            
            # Try 1: Apify (Real-time Scraping) - Highest Priority
            if self.apify_scraper and self.apify_scraper.client:
                log(f"Searching Pinterest via Apify (max {max_pinterest_results} results)...")
                try:
                    apify_result = self.apify_scraper.scrape_pinterest_search(
                        search_keyword=pinterest_keywords[0],
                        max_pins=max_pinterest_results
                    )
                    if apify_result['success'] and apify_result['results']:
                        pinterest_results = apify_result['results']
                        log(f"✓ Apify: {len(pinterest_results)} results")
                        pinterest_success = True
                    else:
                        log(f"✗ Apify failed or found no results: {apify_result.get('error')}")
                except Exception as e:
                    log(f"✗ Apify error: {e}")

            # Try 2: Pinterest API v5 (Official API)
            if not pinterest_success:
                log(f"Searching Pinterest API v5 (max {max_pinterest_results} results)...")
                pinterest_result = self.pinterest_api.search_pins(
                    query=pinterest_keywords[0],
                    page_size=min(max_pinterest_results, 250),
                    max_results=max_pinterest_results
                )
                
                if pinterest_result['success'] and pinterest_result['results']:
                    pinterest_results = pinterest_result['results']
                    log(f"✓ Pinterest API: {len(pinterest_results)} results")
                    pinterest_success = True
                else:
                    log(f"✗ Pinterest API failed: {pinterest_result.get('error')}")
            
            # Try 3: Load from configured data source (Static Fallback)
            if not pinterest_success:
                log("Loading from configured data source (Fallback)...")
                data_result = self.data_loader.load_data(
                    query=pinterest_keywords[0],
                    max_results=max_pinterest_results
                )
                
                if data_result['success']:
                    pinterest_results = data_result['results']
                    log(f"✓ Data loader: {len(pinterest_results)} results from {data_result.get('source_file', 'N/A')}")
                else:
                    log(f"✗ Data loader failed: {data_result.get('error')}")
        
        # Rank Google results by similarity
        google_ranked = []
        if google_results:
            log(f"Ranking {len(google_results)} Google results by similarity...")
            google_ranked = self.ranker.rank_scraped_results(
                google_results,
                event_type=event_type,
                budget_range=budget_range,
                top_k=max_google_results
            )
            log(f"✓ Ranked {len(google_ranked)} Google results")
        
        # Rank Pinterest results by similarity
        pinterest_ranked = []
        if pinterest_results:
            log(f"Ranking {len(pinterest_results)} Pinterest results by similarity...")
            pinterest_ranked = self.ranker.rank_scraped_results(
                pinterest_results,
                event_type=event_type,
                budget_range=budget_range,
                top_k=max_pinterest_results
            )
            log(f"✓ Ranked {len(pinterest_ranked)} Pinterest results")
        
        # Calculate statistics
        google_avg_similarity = (
            sum(r['similarity_score'] for r in google_ranked) / len(google_ranked)
            if google_ranked else 0
        )
        
        pinterest_avg_similarity = (
            sum(r['similarity_score'] for r in pinterest_ranked) / len(pinterest_ranked)
            if pinterest_ranked else 0
        )
        
        return {
            'success': True,
            'event_type': event_type,
            'budget_range': budget_range,
            'color_theme': color_theme,
            'google': {
                'total_results': len(google_ranked),
                'avg_similarity': float(google_avg_similarity),
                'top_similarity': float(google_ranked[0]['similarity_score']) if google_ranked else 0,
                'results': google_ranked
            },
            'pinterest': {
                'total_results': len(pinterest_ranked),
                'avg_similarity': float(pinterest_avg_similarity),
                'top_similarity': float(pinterest_ranked[0]['similarity_score']) if pinterest_ranked else 0,
                'results': pinterest_ranked
            },
            'combined_total': len(google_ranked) + len(pinterest_ranked)
        }


def test_unified_search():
    """Test unified search system."""
    print("=" * 70)
    print("Unified Similarity Search Test")
    print("=" * 70)
    
    searcher = UnifiedSimilaritySearch()
    
    # Check if ranker has samples
    if not searcher.ranker.sample_embeddings:
        print("\n❌ No sample embeddings found")
        print("Make sure you have images in 'downloaded_images' directory")
        return
    
    print(f"\n✓ Loaded {len(searcher.ranker.sample_embeddings)} sample embeddings")
    
    # Test search
    print("\n🔍 Testing unified search...")
    print("Parameters: wedding | 5001-8000 | pastel")
    print("Note: This will take 1-3 minutes...")
    
    result = searcher.search_and_rank(
        event_type="wedding",
        budget_range="5001-8000",
        color_theme="pastel",
        max_google_results=10,  # Smaller for testing
        max_pinterest_results=10,  # Smaller for testing
        include_google=True,
        include_pinterest=bool(os.environ.get('APIFY_API_TOKEN'))  # Only if token available
    )
    
    if result['success']:
        print("\n✅ Search completed successfully!")
        
        # Google results
        print(f"\n📊 Google Results:")
        print(f"   Total: {result['google']['total_results']}")
        print(f"   Avg Similarity: {result['google']['avg_similarity']:.1%}")
        print(f"   Top Similarity: {result['google']['top_similarity']:.1%}")
        
        if result['google']['results']:
            print(f"\n   Top 3 Google results:")
            for i, r in enumerate(result['google']['results'][:3], 1):
                print(f"   {i}. [{r['similarity_score']:.1%}] {r.get('title', 'Untitled')[:50]}")
        
        # Pinterest results
        print(f"\n📊 Pinterest Results:")
        print(f"   Total: {result['pinterest']['total_results']}")
        print(f"   Avg Similarity: {result['pinterest']['avg_similarity']:.1%}")
        print(f"   Top Similarity: {result['pinterest']['top_similarity']:.1%}")
        
        if result['pinterest']['results']:
            print(f"\n   Top 3 Pinterest results:")
            for i, r in enumerate(result['pinterest']['results'][:3], 1):
                print(f"   {i}. [{r['similarity_score']:.1%}] {r.get('title', 'Untitled')[:50]}")
        
        print(f"\n✓ Combined Total: {result['combined_total']} results")
    else:
        print("❌ Search failed")


if __name__ == "__main__":
    test_unified_search()


