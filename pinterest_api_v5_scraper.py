#!/usr/bin/env python3
"""
Pinterest API v5 Integration
Official implementation based on https://developers.pinterest.com/docs/api/v5/
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime

def log(msg: str):
    print(f"[pinterest_api] {msg}")

class PinterestAPIv5:
    """
    Pinterest API v5 client for searching pins.
    Based on: https://developers.pinterest.com/docs/api/v5/introduction
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Pinterest API client.
        
        Args:
            access_token: Pinterest API access token (or set PINTEREST_API_TOKEN env var)
        """
        self.access_token = access_token or os.environ.get('PINTEREST_API_TOKEN')
        
        if not self.access_token:
            log("WARNING: No Pinterest API token found. Set PINTEREST_API_TOKEN env var.")
            log("Get token from: https://developers.pinterest.com/apps/")
        
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def search_pins(
        self, 
        query: str,
        page_size: int = 25,
        max_results: int = 100
    ) -> Dict:
        """
        Search for pins using Pinterest API v5.
        
        Endpoint: GET /search/pins
        Docs: https://developers.pinterest.com/docs/api/v5/pins-get/
        
        Args:
            query: Search query string
            page_size: Results per page (max 250)
            max_results: Total max results to fetch
            
        Returns:
            Dict with search results
        """
        if not self.access_token:
            return {
                'success': False,
                'error': 'No API token provided',
                'results': []
            }
        
        try:
            endpoint = f"{self.base_url}/search/pins"
            
            # Limit page_size to API maximum
            page_size = min(page_size, 250)
            
            params = {
                'query': query,
                'page_size': page_size
            }
            
            log(f"Searching Pinterest API v5 for: '{query}' (page_size: {page_size})")
            
            all_results = []
            bookmark = None
            
            # Fetch pages until we have enough results or run out of pages
            while len(all_results) < max_results:
                # Add bookmark for pagination
                if bookmark:
                    params['bookmark'] = bookmark
                
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                # Check for API errors
                if response.status_code == 401:
                    return {
                        'success': False,
                        'error': 'Invalid API token. Check your PINTEREST_API_TOKEN.',
                        'results': []
                    }
                elif response.status_code == 429:
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded. Try again later.',
                        'results': []
                    }
                elif response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'API error: HTTP {response.status_code}',
                        'details': response.text[:200],
                        'results': []
                    }
                
                data = response.json()
                
                # Extract items from response
                items = data.get('items', [])
                if not items:
                    log("No more results available")
                    break
                
                # Format results
                for item in items:
                    if len(all_results) >= max_results:
                        break
                    
                    formatted_item = self._format_pin(item)
                    if formatted_item:
                        all_results.append(formatted_item)
                
                # Check for next page
                bookmark = data.get('bookmark')
                if not bookmark:
                    log("No more pages available")
                    break
                
                log(f"Fetched {len(all_results)} results so far...")
            
            log(f"✓ Successfully fetched {len(all_results)} pins")
            
            return {
                'success': True,
                'total_results': len(all_results),
                'results': all_results,
                'query': query,
                'scraped_at': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            log(f"API request failed: {e}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'results': []
            }
        except Exception as e:
            log(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def _format_pin(self, item: Dict) -> Optional[Dict]:
        """
        Format Pinterest API response into our standard format.
        
        API response structure:
        {
            "id": "pin_id",
            "title": "Pin title",
            "description": "Pin description",
            "link": "source_url",
            "media": {
                "images": {
                    "originals": {"url": "image_url", "width": 1000, "height": 1500}
                }
            },
            "board_id": "board_id",
            "created_at": "2024-01-01T00:00:00",
            "note": "pin_description",
            "pin_metrics": {
                "saves": 142
            }
        }
        """
        try:
            pin_id = item.get('id', '')
            if not pin_id:
                return None
            
            # Extract image URL from media object
            image_url = ''
            media = item.get('media', {})
            
            # Try different image sources
            if isinstance(media, dict):
                images = media.get('images', {})
                
                # Try in order of preference: originals, 1200x, 736x, 564x
                for size in ['originals', '1200x', '736x', '564x']:
                    if size in images and isinstance(images[size], dict):
                        image_url = images[size].get('url', '')
                        if image_url:
                            break
            
            # Fallback: check if there's a direct image_url field
            if not image_url:
                image_url = item.get('image_url', '')
            
            if not image_url:
                log(f"No image URL found for pin {pin_id}")
                return None
            
            # Extract other fields
            title = item.get('title') or item.get('note', '')
            description = item.get('description') or item.get('note', '')
            
            # Pin metrics
            pin_metrics = item.get('pin_metrics', {})
            saves = pin_metrics.get('saves', 0) if isinstance(pin_metrics, dict) else 0
            
            # Creator info
            creator_info = item.get('creator', {})
            creator_username = ''
            if isinstance(creator_info, dict):
                creator_username = creator_info.get('username', '')
            
            return {
                'pin_id': pin_id,
                'pin_url': f"https://www.pinterest.com/pin/{pin_id}/",
                'image_url': image_url,
                'title': title,
                'description': description,
                'creator': creator_username,
                'saves': saves,
                'source': 'pinterest_api_v5'
            }
            
        except Exception as e:
            log(f"Error formatting pin: {e}")
            return None
    
    def get_user_info(self) -> Dict:
        """
        Get authenticated user information.
        Useful for verifying API token.
        
        Endpoint: GET /user_account
        """
        if not self.access_token:
            return {'success': False, 'error': 'No API token'}
        
        try:
            endpoint = f"{self.base_url}/user_account"
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'username': data.get('username', ''),
                    'profile_image': data.get('profile_image', ''),
                    'account_type': data.get('account_type', '')
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'details': response.text[:200]
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}


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


def test_api():
    """Test Pinterest API v5 connection and search."""
    print("=" * 70)
    print("PINTEREST API v5 TEST")
    print("=" * 70)
    
    # Check for token
    token = os.environ.get('PINTEREST_API_TOKEN')
    if not token:
        print("\n❌ ERROR: PINTEREST_API_TOKEN not set")
        print("\nSetup instructions:")
        print("1. Go to: https://developers.pinterest.com/apps/")
        print("2. Create an app (or use existing)")
        print("3. Generate access token")
        print("4. Set environment variable:")
        print("   export PINTEREST_API_TOKEN='pina_your_token_here'")
        return
    
    print(f"\n✅ API Token found: {token[:12]}...")
    
    # Initialize client
    client = PinterestAPIv5(token)
    
    # Test 1: Verify token
    print("\n📋 Test 1: Verifying API token...")
    user_info = client.get_user_info()
    
    if user_info['success']:
        print(f"✅ Token valid!")
        print(f"   Username: {user_info.get('username', 'N/A')}")
        print(f"   Account Type: {user_info.get('account_type', 'N/A')}")
    else:
        print(f"❌ Token verification failed: {user_info.get('error')}")
        print("\nCheck:")
        print("1. Token is correct (starts with 'pina_')")
        print("2. Token has not expired")
        print("3. App has necessary scopes")
        return
    
    # Test 2: Search
    print("\n🔍 Test 2: Searching for pins...")
    print("Query: 'wedding welcome board'")
    print("Fetching up to 10 results...")
    
    result = client.search_pins(
        query="wedding welcome board",
        page_size=10,
        max_results=10
    )
    
    if result['success']:
        print(f"\n✅ Search successful!")
        print(f"   Total results: {result['total_results']}")
        
        if result['results']:
            print(f"\n📌 Sample result:")
            sample = result['results'][0]
            print(f"   Pin ID: {sample['pin_id']}")
            print(f"   Title: {sample['title'][:60]}...")
            print(f"   Image URL: {sample['image_url'][:60]}...")
            print(f"   Saves: {sample['saves']}")
            print(f"   Pin URL: {sample['pin_url']}")
    else:
        print(f"\n❌ Search failed: {result.get('error')}")
        if 'details' in result:
            print(f"   Details: {result['details']}")
    
    print("\n" + "=" * 70)
    print("✅ Test complete! Your Pinterest API v5 is ready to use.")
    print("\nTo use in your app:")
    print("1. Make sure PINTEREST_API_TOKEN is set")
    print("2. Restart: python3 frontend.py")
    print("3. Check Pinterest in the UI - it will now use API v5!")
    print("=" * 70)


if __name__ == "__main__":
    test_api()






