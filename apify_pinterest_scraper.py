#!/usr/bin/env python3
"""
Apify Pinterest Scraper Integration (Updated)
Uses apify-client library for Pinterest search scraping
"""

import os
from typing import List, Dict, Optional
from datetime import datetime

def log(msg: str):
    print(f"[apify] {msg}")

class ApifyPinterestScraper:
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Apify scraper using apify-client library.
        
        Args:
            api_token: Apify API token (or set APIFY_API_TOKEN env var)
        """
        self.api_token = api_token or os.environ.get('APIFY_API_TOKEN')
        if not self.api_token:
            log("WARNING: No Apify API token provided. Set APIFY_API_TOKEN env var or pass token to constructor")
        
        self.actor_id = "NmOWmFiz40AgzJNxT"
        self.client = None
        
        # Initialize client if token is available
        if self.api_token:
            try:
                from apify_client import ApifyClient
                self.client = ApifyClient(self.api_token)
                log("ApifyClient initialized successfully")
            except ImportError:
                log("ERROR: apify-client not installed. Run: pip install apify-client")
                self.client = None
    
    def _clean_url(self, url: str) -> str:
        """Clean URL by decoding unicode escapes."""
        if not url:
            return ''
        try:
            # Decode URL encoding first: %5Cu003d -> \u003d
            import urllib.parse
            decoded = urllib.parse.unquote(url)
            
            # Check if there are unicode escapes like \u003d
            # We need to check for backslash (chr(92)) followed by 'u'
            if '\\u' in decoded or chr(92) + 'u' in decoded:
                # Use codecs to safely decode unicode escapes
                import codecs
                # Replace \uXXXX with actual unicode characters
                return codecs.decode(decoded, 'unicode-escape')
            return decoded
        except Exception as e:
            log(f"Error cleaning URL {url}: {e}")
            return url
    
    def scrape_pinterest_search(
        self, 
        search_keyword: str,
        max_pins: int = 10,
        sort_order: str = "relevance",
        use_proxy: bool = False
    ) -> Dict:
        """
        Scrape Pinterest search results using Apify.
        
        Args:
            search_keyword: Pinterest search keyword/query
            max_pins: Maximum number of pins to scrape (default 100)
            sort_order: Sort order - "relevance" or "recent" (default: relevance)
            use_proxy: Whether to use Apify proxy (default: False)
            
        Returns:
            Dict with scraping results and metadata
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Apify client not initialized. Check API token and apify-client installation.',
                'results': []
            }
        
        log(f"Starting Apify scrape for keyword: '{search_keyword}' (max {max_pins} pins)")
        
        # Prepare input for Apify actor (using the format from user's example)
        run_input = {
            "urls": [search_keyword],  # Search keywords as URLs list
            "keyword": search_keyword,
            "max_pins": max_pins,
            "sort_order": sort_order,
            "max_comments": 0,  # We don't need comments for now
            "proxy_configuration": {"useApifyProxy": use_proxy}
        }
        
        try:
            log("Running Apify actor...")
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            log(f"Actor run completed with status: {run.get('status')}")
            
            # Fetch results from the run's dataset
            results = []
            dataset_id = run.get("defaultDatasetId")
            
            if dataset_id:
                log("Fetching results from dataset...")
                for item in self.client.dataset(dataset_id).iterate_items():
                    # Format the result
                    # Apify returns image_url with underscore, not imageUrl
                    image_url = item.get('image_url') or item.get('imageUrl') or item.get('imageURL') or item.get('image') or ''
                    
                    # Title is often a nested object with 'format' key
                    title_data = item.get('title', '')
                    if isinstance(title_data, dict):
                        title = title_data.get('format', '')
                    else:
                        title = str(title_data) if title_data else ''
                    
                    formatted_result = {
                        'pin_id': item.get('id') or item.get('node_id', ''),
                        'pin_url': item.get('url') or item.get('link', ''),
                        'image_url': self._clean_url(image_url),
                        'title': title,
                        'description': item.get('description', ''),
                        'creator': item.get('creator', {}).get('name', '') if isinstance(item.get('creator'), dict) else '',
                        'saves': item.get('saves', 0),
                        'comments_count': item.get('comments_count', 0),
                        'source': 'pinterest_apify'
                    }
                    results.append(formatted_result)
            
            log(f"Successfully scraped {len(results)} pins")
            
            return {
                'success': True,
                'keyword': search_keyword,
                'total_results': len(results),
                'results': results,
                'scraped_at': datetime.now().isoformat(),
                'run_id': run.get('id', '')
            }
            
        except Exception as e:
            log(f"Scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def scrape_multiple_keywords(
        self,
        keywords: List[str],
        max_pins_per_keyword: int = 100
    ) -> Dict:
        """
        Scrape multiple Pinterest keywords and combine results.
        
        Args:
            keywords: List of search keywords
            max_pins_per_keyword: Max pins per keyword
            
        Returns:
            Combined results from all keywords
        """
        all_results = []
        failed_keywords = []
        
        for keyword in keywords:
            result = self.scrape_pinterest_search(keyword, max_pins=max_pins_per_keyword)
            
            if result['success']:
                all_results.extend(result['results'])
            else:
                failed_keywords.append({
                    'keyword': keyword,
                    'error': result.get('error', 'Unknown error')
                })
        
        # Deduplicate by pin_id
        seen_pins = set()
        unique_results = []
        for item in all_results:
            pin_id = item.get('pin_id', '')
            if pin_id and pin_id not in seen_pins:
                seen_pins.add(pin_id)
                unique_results.append(item)
        
        return {
            'success': True,
            'total_keywords': len(keywords),
            'successful_keywords': len(keywords) - len(failed_keywords),
            'failed_keywords': failed_keywords,
            'total_results': len(unique_results),
            'results': unique_results,
            'scraped_at': datetime.now().isoformat()
        }


def create_search_keywords(event_type: str, budget_range: str, color_theme: str) -> List[str]:
    """
    Create optimized Pinterest search keywords.
    
    Args:
        event_type: Type of event (engagement, wedding, etc.)
        budget_range: Budget range string
        color_theme: Color theme
        
    Returns:
        List of search keywords
    """
    keywords = []
    
    # Base keywords
    keywords.append(f"{event_type} welcome board {color_theme}")
    keywords.append(f"{event_type} welcome sign decor")
    keywords.append(f"welcome board {event_type} entrance")
    
    # Budget-specific keywords
    if "3000-5000" in budget_range:
        keywords.append(f"simple {event_type} welcome board diy")
        keywords.append(f"budget {event_type} welcome sign")
    elif "5001-8000" in budget_range:
        keywords.append(f"acrylic {event_type} welcome board")
        keywords.append(f"wooden {event_type} welcome sign")
    elif "8001-15000" in budget_range:
        keywords.append(f"luxury {event_type} welcome board")
        keywords.append(f"premium {event_type} welcome decor")
    
    return keywords


def test_scraper():
    """Test the Apify scraper with apify-client."""
    print("=" * 60)
    print("Apify Pinterest Scraper Test (apify-client)")
    print("=" * 60)
    
    # Check for API token
    api_token = os.environ.get('APIFY_API_TOKEN')
    if not api_token:
        print("\nERROR: APIFY_API_TOKEN environment variable not set")
        print("\nTo use this scraper:")
        print("1. Get your API token from: https://console.apify.com/account/integrations")
        print("2. Set it as environment variable:")
        print("   export APIFY_API_TOKEN='your_token_here'")
        print("\nOr pass it directly to the constructor:")
        print("   scraper = ApifyPinterestScraper(api_token='your_token_here')")
        return
    
    try:
        from apify_client import ApifyClient
    except ImportError:
        print("\nERROR: apify-client not installed")
        print("Install it with: pip install apify-client")
        return
    
    scraper = ApifyPinterestScraper()
    
    # Test single keyword
    print("\nTest 1: Single keyword scrape")
    result = scraper.scrape_pinterest_search(
        search_keyword="wedding welcome board",
        max_pins=10
    )
    
    if result['success']:
        print(f"Success! Found {result['total_results']} pins")
        if result['results']:
            print(f"\nSample result:")
            sample = result['results'][0]
            print(f"  Title: {sample['title']}")
            print(f"  Pin URL: {sample['pin_url']}")
            print(f"  Image URL: {sample['image_url'][:80]}...")
            print(f"  Saves: {sample['saves']}")
    else:
        print(f"Failed: {result['error']}")
    
    # Test multiple keywords
    print("\nTest 2: Multiple keyword scrape")
    keywords = create_search_keywords("wedding", "5001-8000", "pastel")
    print(f"Keywords: {keywords[:2]}...")  # Show first 2
    
    multi_result = scraper.scrape_multiple_keywords(keywords[:2], max_pins_per_keyword=5)
    
    if multi_result['success']:
        print(f"Success! Total unique pins: {multi_result['total_results']}")
        print(f"   Keywords processed: {multi_result['successful_keywords']}/{multi_result['total_keywords']}")
    else:
        print(f"Failed")


if __name__ == "__main__":
    test_scraper()
