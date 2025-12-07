#!/usr/bin/env python3
"""
Pinterest Data Loader - Flexible loader for Excel/JSON/CSV data sources
Easy to switch between different data files via config
"""

import os
import json
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

def log(msg: str):
    print(f"[data_loader] {msg}")

# ============================================================================
# CONFIGURATION - CHANGE THIS TO SWITCH DATA SOURCES
# ============================================================================

DATA_SOURCE_CONFIG = {
    # Primary data source (change this to switch files)
    'primary_source': 'data/Ampify Pintrest Scrapper search results.xlsx',
    
    # Alternative sources (uncomment to use)
    # 'primary_source': 'offline_pinterest_results/wedding_welcome_board.json',
    # 'primary_source': 'data/pinterest_results.csv',
    
    # File type detection (auto-detected, but can override)
    'file_type': 'auto',  # 'auto', 'excel', 'json', 'csv'
    
    # Column mapping for Excel/CSV files
    'column_mapping': {
        'image_url': 'image_url',
        'description': 'description',
        'board_name': 'board/name',
        'username': 'board/owner/username',
        'pin_id': None,  # Will extract from URL if not present
        'title': 'description',  # Use description as title if no title column
        'saves': None,  # Not in this dataset
    }
}

# ============================================================================

class PinterestDataLoader:
    """
    Flexible Pinterest data loader supporting multiple file formats.
    Easy to switch data sources via configuration.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize data loader.
        
        Args:
            config: Configuration dict (uses DATA_SOURCE_CONFIG if None)
        """
        self.config = config or DATA_SOURCE_CONFIG
        self.data_source = self.config['primary_source']
        self.file_type = self._detect_file_type()
        
        log(f"Initialized with data source: {self.data_source}")
        log(f"Detected file type: {self.file_type}")
    
    def _detect_file_type(self) -> str:
        """Detect file type from extension."""
        if self.config['file_type'] != 'auto':
            return self.config['file_type']
        
        ext = os.path.splitext(self.data_source)[1].lower()
        
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.json':
            return 'json'
        elif ext == '.csv':
            return 'csv'
        else:
            log(f"Warning: Unknown file type {ext}, defaulting to JSON")
            return 'json'
    
    def load_data(self, query: Optional[str] = None, max_results: int = 100) -> Dict:
        """
        Load Pinterest data from configured source.
        
        Args:
            query: Search query (for filtering, optional)
            max_results: Maximum results to return
            
        Returns:
            Dict with standardized results
        """
        try:
            if not os.path.exists(self.data_source):
                return {
                    'success': False,
                    'error': f'Data source not found: {self.data_source}',
                    'results': []
                }
            
            # Load based on file type
            if self.file_type == 'excel':
                results = self._load_excel(max_results)
            elif self.file_type == 'json':
                results = self._load_json(max_results)
            elif self.file_type == 'csv':
                results = self._load_csv(max_results)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {self.file_type}',
                    'results': []
                }
            
            # Filter by query if provided
            if query and results:
                results = self._filter_by_query(results, query)
            
            log(f"✓ Loaded {len(results)} results from {self.data_source}")
            
            return {
                'success': True,
                'total_results': len(results),
                'results': results,
                'source_file': self.data_source,
                'file_type': self.file_type,
                'method': 'data_loader'
            }
            
        except Exception as e:
            log(f"Error loading data: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def _load_excel(self, max_results: int) -> List[Dict]:
        """Load data from Excel file."""
        log(f"Reading Excel file: {self.data_source}")
        df = pd.read_excel(self.data_source, nrows=max_results)
        
        results = []
        for idx, row in df.iterrows():
            formatted = self._format_row(row)
            if formatted:
                results.append(formatted)
        
        return results
    
    def _load_csv(self, max_results: int) -> List[Dict]:
        """Load data from CSV file."""
        log(f"Reading CSV file: {self.data_source}")
        df = pd.read_csv(self.data_source, nrows=max_results)
        
        results = []
        for idx, row in df.iterrows():
            formatted = self._format_row(row)
            if formatted:
                results.append(formatted)
        
        return results
    
    def _load_json(self, max_results: int) -> List[Dict]:
        """Load data from JSON file."""
        log(f"Reading JSON file: {self.data_source}")
        
        with open(self.data_source, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('results', data.get('items', data.get('data', [])))
        else:
            return []
        
        results = []
        for item in items[:max_results]:
            formatted = self._format_dict(item)
            if formatted:
                results.append(formatted)
        
        return results
    
    def _format_row(self, row: pd.Series) -> Optional[Dict]:
        """Format pandas row to standard structure."""
        try:
            col_map = self.config['column_mapping']
            
            # Get image URL (required)
            image_url = self._get_value(row, col_map['image_url'])
            if not image_url or pd.isna(image_url):
                return None
            
            # Extract pin ID from URL
            pin_id = self._extract_pin_id(image_url)
            
            # Get other fields
            description = self._get_value(row, col_map['description']) or ''
            title = self._get_value(row, col_map['title']) or description[:100]
            username = self._get_value(row, col_map['username']) or ''
            board_name = self._get_value(row, col_map['board_name']) or ''
            
            # Clean up NaN values
            if pd.isna(description):
                description = ''
            if pd.isna(title):
                title = 'Pinterest Pin'
            if pd.isna(username):
                username = ''
            
            return {
                'pin_id': pin_id,
                'pin_url': f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else '',
                'image_url': str(image_url),
                'title': str(title)[:200],  # Limit length
                'description': str(description)[:500],
                'creator': str(username),
                'board_name': str(board_name),
                'saves': 0,  # Not in dataset
                'source': 'data_loader_excel'
            }
            
        except Exception as e:
            log(f"Error formatting row: {e}")
            return None
    
    def _format_dict(self, item: Dict) -> Optional[Dict]:
        """Format dict to standard structure."""
        try:
            # Try to get image URL from various possible keys
            image_url = (
                item.get('image_url') or 
                item.get('image') or 
                item.get('imageUrl') or
                item.get('media', {}).get('images', {}).get('originals', {}).get('url', '')
            )
            
            if not image_url:
                return None
            
            pin_id = item.get('pin_id') or item.get('id') or self._extract_pin_id(image_url)
            
            return {
                'pin_id': pin_id,
                'pin_url': item.get('pin_url') or f"https://www.pinterest.com/pin/{pin_id}/",
                'image_url': image_url,
                'title': item.get('title') or item.get('description', '')[:100],
                'description': item.get('description', ''),
                'creator': item.get('creator') or item.get('username', ''),
                'saves': item.get('saves', 0),
                'source': 'data_loader_json'
            }
            
        except Exception as e:
            log(f"Error formatting dict: {e}")
            return None
    
    def _get_value(self, row: pd.Series, column: Optional[str]) -> any:
        """Safely get value from pandas row."""
        if column is None or column not in row.index:
            return None
        return row[column]
    
    def _extract_pin_id(self, url: str) -> str:
        """Extract pin ID from image URL or pin URL."""
        if not url:
            return ''
        
        # Try to extract from URL path
        import re
        
        # Pattern 1: Pinterest pin URL
        match = re.search(r'/pin/(\d+)', url)
        if match:
            return match.group(1)
        
        # Pattern 2: Image URL with hash (use hash as ID)
        match = re.search(r'/([a-f0-9]{32,})', url)
        if match:
            return match.group(1)[:15]  # Use first 15 chars of hash
        
        # Pattern 3: Extract filename
        match = re.search(r'/([^/]+)\.(jpg|jpeg|png|webp)', url)
        if match:
            return match.group(1)[:15]
        
        return ''
    
    def _filter_by_query(self, results: List[Dict], query: str) -> List[Dict]:
        """Filter results by query match."""
        query_words = set(query.lower().split())
        
        filtered = []
        for result in results:
            # Check if query words appear in title or description
            text = (result.get('title', '') + ' ' + result.get('description', '')).lower()
            
            matches = sum(1 for word in query_words if word in text)
            if matches >= len(query_words) * 0.5:  # At least 50% match
                filtered.append(result)
        
        return filtered


# Convenience function for easy import
def load_pinterest_data(query: Optional[str] = None, max_results: int = 100) -> Dict:
    """
    Load Pinterest data using configured source.
    
    Args:
        query: Optional search query for filtering
        max_results: Maximum results to return
        
    Returns:
        Dict with results
    """
    loader = PinterestDataLoader()
    return loader.load_data(query, max_results)


def test_loader():
    """Test the data loader."""
    print("=" * 70)
    print("PINTEREST DATA LOADER TEST")
    print("=" * 70)
    
    loader = PinterestDataLoader()
    
    print(f"\n📁 Data source: {loader.data_source}")
    print(f"📋 File type: {loader.file_type}")
    
    # Test load
    print("\n🔍 Loading data (first 10 results)...")
    result = loader.load_data(max_results=10)
    
    if result['success']:
        print(f"\n✅ Success!")
        print(f"   Total results: {result['total_results']}")
        print(f"   Source: {result['source_file']}")
        
        if result['results']:
            print(f"\n📌 Sample result:")
            sample = result['results'][0]
            print(f"   Pin ID: {sample['pin_id']}")
            print(f"   Title: {sample['title'][:60]}...")
            print(f"   Image URL: {sample['image_url'][:60]}...")
            print(f"   Creator: {sample['creator']}")
            print(f"   Board: {sample.get('board_name', 'N/A')}")
    else:
        print(f"\n❌ Failed: {result['error']}")
    
    # Test query filtering
    print("\n\n🔍 Testing query filter: 'wedding'...")
    result = loader.load_data(query='wedding', max_results=10)
    
    if result['success']:
        print(f"✅ Filtered to {result['total_results']} results matching 'wedding'")
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print("\nTo switch data sources, edit pinterest_data_loader.py:")
    print("  DATA_SOURCE_CONFIG['primary_source'] = 'your_file.xlsx'")
    print("=" * 70)


if __name__ == "__main__":
    test_loader()






