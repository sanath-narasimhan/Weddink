#!/usr/bin/env python3
"""
Backend Welcome Board Search Function
Takes event_type, budget, color_theme and returns relevant welcome board images
"""

import os
import json
import numpy as np
from PIL import Image
import torch
import open_clip
from typing import List, Dict, Optional
import glob
from pathlib import Path
import requests
import re
from urllib.parse import quote_plus

try:
    from pdf_generator import generate_mood_board_pdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    log("PDF generation not available - reportlab not installed")

def log(msg: str):
    print(f"[backend] {msg}")

def _headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def get_pinterest_image_url(pin_id: str) -> Optional[str]:
    """Extract actual image URL from Pinterest pin using widgets API."""
    try:
        url = f"https://widgets.pinterest.com/v3/pidgets/pins/info/?pin_ids={pin_id}"
        resp = requests.get(url, headers=_headers(), timeout=20)
        
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        
        # Pinterest API returns data as a list directly, not wrapped in a pins object
        pins = data.get("data", [])
        
        if not pins:
            return None
            
        pin = pins[0]
        images = pin.get("images", {})
        
        # Handle both dict and list formats
        if isinstance(images, dict):
            # Prefer larger image sizes (Pinterest uses format like "564x", "736x", etc.)
            preferred_sizes = ["orig", "1200x", "736x", "564x", "474x", "300x", "237x", "236x"]
            
            for size in preferred_sizes:
                if size in images and isinstance(images[size], dict):
                    image_url = images[size].get("url")
                    if image_url:
                        return image_url
        
        # Fallback: look for any image URL in the images object
        for key, value in images.items():
            if "image" in key.lower() and isinstance(value, str) and value.startswith("http"):
                return value
        
        return None
        
    except Exception as e:
        log(f"Error getting image URL for pin {pin_id}: {e}")
        return None

class WelcomeBoardBackend:
    def __init__(self, local_images_dir: str = "downloaded_images"):
        self.local_images_dir = local_images_dir
        self.model = None
        self.preprocess = None
        self.local_database = {}
        self._load_clip_model()
        self._build_local_database()
    
    def _load_clip_model(self):
        """Load CLIP model for image embeddings."""
        try:
            model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            model.eval()
            self.model = model
            self.preprocess = preprocess
            log("CLIP model loaded")
        except Exception as e:
            log(f"CLIP model failed: {e}")
            self.model = None
            self.preprocess = None
    
    def _extract_colors_from_hex(self, color_theme: str) -> List[str]:
        """Convert color theme string to color names using predefined palettes."""
        color_palettes = {
            'bold': ['red', 'orange', 'hot pink', 'electric blue', 'bright yellow', 'vibrant', 'neon'],
            'pastel': ['blush pink', 'mint', 'lavender', 'peach', 'baby blue', 'soft yellow', 'cream'],
            'royal': ['deep purple', 'gold', 'emerald', 'burgundy', 'navy', 'maroon', 'rich blue'],
            'neutral': ['white', 'beige', 'cream', 'ivory', 'champagne', 'taupe', 'gray', 'black'],
            'other': [color_theme.lower()] if color_theme else []
        }
        
        if not color_theme:
            return []
        
        theme_lower = color_theme.lower()
        
        # Check if theme matches a predefined palette
        for palette_name, colors in color_palettes.items():
            if palette_name in theme_lower or theme_lower in palette_name:
                return colors[:3]  # Return up to 3 colors from palette
        
        # Fallback: check for individual color names
        color_map = {
            '#ff0000': 'red', '#ff6b6b': 'red',
            '#00ff00': 'green', '#00b894': 'green',
            '#0000ff': 'blue', '#74b9ff': 'blue',
            '#ffff00': 'yellow', '#fdcb6e': 'yellow',
            '#ffa500': 'orange', '#e17055': 'orange',
            '#800080': 'purple', '#a29bfe': 'purple',
            '#ffffff': 'white', '#ddd': 'white',
            '#000000': 'black', '#2d3436': 'black',
            '#ff69b4': 'pink', '#fd79a8': 'pink'
        }
        
        colors = []
        if '#' in color_theme:
            hex_colors = re.findall(r'#[0-9a-fA-F]{6}', color_theme)
            for hex_color in hex_colors:
                if hex_color in color_map:
                    colors.append(color_map[hex_color])
        else:
            # Direct color names
            color_words = theme_lower.split()
            for word in color_words:
                if word in ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'white', 'black', 'pink', 'gold', 'silver']:
                    colors.append(word)
        
        return colors[:3] if colors else [theme_lower]
    
    def _build_local_database(self):
        """Build database of local images with embeddings."""
        if not os.path.exists(self.local_images_dir):
            log("No local images directory found")
            return
        
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(glob.glob(os.path.join(self.local_images_dir, '**', ext), recursive=True))
        
        log(f"Building database from {len(image_files)} local images")
        
        for image_path in image_files:
            # Extract metadata from path
            path_parts = Path(image_path).parts
            price_category = None
            event_type = None
            
            for part in path_parts:
                if '3000-5000' in part:
                    price_category = '₹3000-₹5000'
                elif '5001-8000' in part:
                    price_category = '₹5001-₹8000'
                elif '8001-15000' in part:
                    price_category = '₹8001-₹15000'
                
                if part.lower() in ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']:
                    event_type = part.lower()
            
            # Get embedding
            embedding = self._get_image_embedding(image_path)
            if embedding is not None:
                self.local_database[image_path] = {
                    'embedding': embedding,
                    'price_category': price_category,
                    'event_type': event_type,
                    'filename': os.path.basename(image_path)
                }
        
        log(f"Local database built with {len(self.local_database)} images")
    
    def _get_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Get CLIP embedding for an image."""
        if not self.model or not self.preprocess:
            return None
        
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.preprocess(image).unsqueeze(0)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                return image_features.numpy().flatten()
        except Exception as e:
            return None
    
    def _find_local_similar(self, query_embedding: np.ndarray, event_type: str, 
                           budget_range: str, top_k: int = 8) -> List[Dict]:
        """Find similar images from local database."""
        similarities = []
        
        for image_path, data in self.local_database.items():
            # Skip if it's the same image we're searching from
            if query_embedding is not None and np.array_equal(query_embedding, data['embedding']):
                continue
                
            # For local similarity, be less restrictive - show similar designs across event types
            # Only filter by budget if specified
            if budget_range:
                # Convert budget range format for comparison (remove currency symbols)
                data_price = data['price_category'] or ""
                if "3000-5000" in budget_range and "3000-5000" not in data_price.replace("₹", "").replace("Rs", ""):
                    continue
                elif "5001-8000" in budget_range and "5001-8000" not in data_price.replace("₹", "").replace("Rs", ""):
                    continue
                elif "8001-15000" in budget_range and "8001-15000" not in data_price.replace("₹", "").replace("Rs", ""):
                    continue
            
            # Calculate visual similarity
            visual_similarity = np.dot(query_embedding, data['embedding']) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(data['embedding'])
            )
            
            # Calculate weighted score: event type match (40%) + budget match (30%) + visual similarity (30%)
            weighted_score = 0.0
            
            # Event type match (40% weight)
            if data['event_type'] == event_type:
                weighted_score += 0.4
            
            # Budget match (30% weight)
            if budget_range and data['price_category']:
                data_price = data['price_category'].replace("₹", "").replace("Rs", "")
                if budget_range.replace("₹", "").replace("Rs", "") in data_price:
                    weighted_score += 0.3
            
            # Visual similarity (30% weight)
            weighted_score += visual_similarity * 0.3
            
            similarities.append({
                'image_path': image_path,
                'similarity': float(weighted_score),  # Use weighted score
                'visual_similarity': float(visual_similarity),  # Keep original for reference
                'price_category': data['price_category'],
                'event_type': data['event_type'],
                'filename': data['filename'],
                'source': 'local'
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _web_search_google_enhanced(self, query: str, max_results: int, sample_embedding: Optional[np.ndarray], event_type: str) -> List[Dict]:
        """Enhanced Google search with image similarity matching."""
        try:
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
            headers = _headers()
            resp = requests.get(search_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                return []
            
            html = resp.text
            results = []
            
            # Extract image URLs - updated patterns to capture actual URLs
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
            for pattern in img_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if match and match not in seen_urls and match.startswith('http'):
                        # Enhanced filtering - exclude drawings, renderings, and non-welcome-board content
                        skip_terms = [
                            '.svg', 'icon', 'branding', 'gstatic.com/bar', 
                            'googleusercontent.com/bar', 'logo', 'data:',
                            'bing.com/rp', 'ssl.gstatic.com/gb', 'invitation',
                            'card', 'cake', 'cake-topper', 'favor', 'gift',
                            'table-setting', 'centerpiece', 'bouquet', 'dress',
                            'makeup', 'hair', 'jewelry', 'shoes', 'accessories',
                            'food', 'menu', 'drink', 'beverage', 'catering',
                            'venue', 'hall', 'mandap', 'stage', 'backdrop',
                            'photography', 'photo', 'camera', 'album',
                            # New terms to exclude drawings/renderings
                            'sketch', 'drawing', 'render', 'rendering', 'illustration', 
                            'vector', 'clipart', 'graphic', 'design', 'template', 
                            'mockup', 'cartoon', 'anime', 'art', 'painting',
                            # Exclude off-topic engagement content
                            'ring', 'jewelry', 'employee', 'business', 'corporate',
                            'workplace', 'hr', 'management', 'team', 'company'
                        ]
                        
                        # Prefer welcome board specific terms and realistic photos
                        welcome_terms = [
                            'welcome', 'sign', 'board', 'display', 'entrance',
                            'ceremony', 'entry', 'reception', 'gate', 'door',
                            'photo', 'real', 'actual', 'diy', 'wedding', 'event', 'decor'
                        ]
                        
                        # Check if URL contains welcome board terms (prefer these)
                        url_lower = match.lower()
                        has_welcome_term = any(term in url_lower for term in welcome_terms)
                        
                        if not any(skip in match.lower() for skip in skip_terms) and any(img_ext in match.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            seen_urls.add(match)
                            
                            # Prioritize URLs with welcome board terms
                            priority = 1 if has_welcome_term else 0
                            
                            results.append({
                                'image_url': match,
                                'title': f'Google Images Result',
                                'source': 'google',
                                'url': match,
                                'priority': priority
                            })
                            if len(results) >= max_results * 2:  # Get more for similarity filtering
                                break
                if len(results) >= max_results * 2:
                    break
            
            # If we have a sample embedding, try to download and compare images (limit to top 10 for speed)
            if sample_embedding is not None and results:
                # Only process top 10 results for similarity to avoid timeout
                top_results = results[:10]
                results = self._filter_by_image_similarity(top_results, sample_embedding, max_results)
            
            # Sort by priority (welcome board terms first)
            results.sort(key=lambda x: x.get('priority', 0), reverse=True)
            return results[:max_results]
        except Exception as e:
            log(f"Enhanced Google search failed: {e}")
            return []
    
    def _filter_by_image_similarity(self, results: List[Dict], sample_embedding: np.ndarray, max_results: int) -> List[Dict]:
        """Filter results by image similarity to sample."""
        try:
            if self.model is None or self.preprocess is None:
                return results[:max_results]
            
            scored_results = []
            
            for result in results:
                try:
                    # Download and process image
                    image_url = result['image_url']
                    headers = _headers()
                    img_resp = requests.get(image_url, headers=headers, timeout=5)
                    
                    if img_resp.status_code == 200:
                        # Load image
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(img_resp.content))
                        
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Resize to model input size
                        img = img.resize((224, 224))
                        
                        # Preprocess and get embedding
                        img_tensor = self.preprocess(img).unsqueeze(0)
                        with torch.no_grad():
                            img_embedding = self.model.encode_image(img_tensor).numpy().flatten()
                        
                        # Calculate similarity
                        similarity = np.dot(sample_embedding, img_embedding) / (
                            np.linalg.norm(sample_embedding) * np.linalg.norm(img_embedding)
                        )
                        
                        result['image_similarity'] = float(similarity)
                        scored_results.append(result)
                        
                        if len(scored_results) >= 5:  # Limit to 5 for speed
                            break
                            
                except Exception as e:
                    # Skip images that can't be processed
                    continue
            
            # Sort by image similarity
            scored_results.sort(key=lambda x: x.get('image_similarity', 0), reverse=True)
            return scored_results[:max_results]
            
        except Exception as e:
            log(f"Image similarity filtering failed: {e}")
            return results[:max_results]
    
    def _web_search_google(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Google Images with enhanced filtering."""
        try:
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
            headers = _headers()
            resp = requests.get(search_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                return []
            
            html = resp.text
            results = []
            
            # Extract image URLs - updated patterns to capture actual URLs
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
            for pattern in img_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if match and match not in seen_urls and match.startswith('http'):
                        # Enhanced filtering - exclude drawings, renderings, and non-welcome-board content
                        skip_terms = [
                            '.svg', 'icon', 'branding', 'gstatic.com/bar', 
                            'googleusercontent.com/bar', 'logo', 'data:',
                            'bing.com/rp', 'ssl.gstatic.com/gb', 'invitation',
                            'card', 'cake', 'cake-topper', 'favor', 'gift',
                            'table-setting', 'centerpiece', 'bouquet', 'dress',
                            'makeup', 'hair', 'jewelry', 'shoes', 'accessories',
                            'food', 'menu', 'drink', 'beverage', 'catering',
                            'venue', 'hall', 'mandap', 'stage', 'backdrop',
                            'photography', 'photo', 'camera', 'album',
                            # New terms to exclude drawings/renderings
                            'sketch', 'drawing', 'render', 'rendering', 'illustration', 
                            'vector', 'clipart', 'graphic', 'design', 'template', 
                            'mockup', 'cartoon', 'anime', 'art', 'painting'
                        ]
                        
                        # Prefer welcome board specific terms and realistic photos
                        welcome_terms = [
                            'welcome', 'sign', 'board', 'display', 'entrance',
                            'ceremony', 'entry', 'reception', 'gate', 'door',
                            'photo', 'real', 'actual', 'diy', 'wedding', 'event', 'decor'
                        ]
                        
                        # Check if URL contains welcome board terms (prefer these)
                        url_lower = match.lower()
                        has_welcome_term = any(term in url_lower for term in welcome_terms)
                        
                        if not any(skip in match.lower() for skip in skip_terms) and any(img_ext in match.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            seen_urls.add(match)
                            
                            # Prioritize URLs with welcome board terms
                            priority = 1 if has_welcome_term else 0
                            
                            results.append({
                                'image_url': match,
                                'title': f'Google Images Result',
                                'source': 'google',
                                'url': match,
                                'priority': priority
                            })
                            if len(results) >= max_results:
                                break
                if len(results) >= max_results:
                    break
            
            # Sort by priority (welcome board terms first)
            results.sort(key=lambda x: x.get('priority', 0), reverse=True)
            return results
        except Exception as e:
            log(f"Google search failed: {e}")
            return []
    
    def _web_search_bing(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Bing Images with enhanced filtering."""
        try:
            search_url = f"https://www.bing.com/images/search?q={quote_plus(query)}"
            headers = _headers()
            resp = requests.get(search_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                return []
            
            html = resp.text
            results = []
            
            # Extract image URLs - improved patterns for Bing
            img_patterns = [
                r'https://[^\s"<>]+\.(?:jpg|jpeg|png|webp|gif)',
                r'data-src="([^"]+)"',
                r'src="([^"]+)"'
            ]
            seen_urls = set()
            
            for pattern in img_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if match and match not in seen_urls and match.startswith('http'):
                        # Clean up HTML entities and malformed URLs
                        clean_url = match.replace('&quot;', '"').replace('&amp;', '&')
                        
                        # Extract clean URL if it contains malformed JSON
                        if '","murl":"' in clean_url:
                            # Extract the actual image URL from the malformed JSON
                            url_parts = clean_url.split('","murl":"')
                            if len(url_parts) > 1:
                                clean_url = url_parts[1]
                        
                        # Enhanced filtering - exclude drawings, renderings, and non-welcome-board content
                        skip_terms = [
                            '.svg', 'icon', 'branding', 'bing.com/bar',
                            'bing.com/rp', 'ssl.gstatic.com', 'invitation',
                            'card', 'cake', 'cake-topper', 'favor', 'gift',
                            'table-setting', 'centerpiece', 'bouquet', 'dress',
                            'makeup', 'hair', 'jewelry', 'shoes', 'accessories',
                            'food', 'menu', 'drink', 'beverage', 'catering',
                            'venue', 'hall', 'mandap', 'stage', 'backdrop',
                            'photography', 'photo', 'camera', 'album',
                            # New terms to exclude drawings/renderings
                            'sketch', 'drawing', 'render', 'rendering', 'illustration', 
                            'vector', 'clipart', 'graphic', 'design', 'template', 
                            'mockup', 'cartoon', 'anime', 'art', 'painting'
                        ]
                        
                        # Prefer welcome board specific terms and realistic photos
                        welcome_terms = [
                            'welcome', 'sign', 'board', 'display', 'entrance',
                            'ceremony', 'entry', 'reception', 'gate', 'door',
                            'photo', 'real', 'actual', 'diy', 'wedding', 'event', 'decor'
                        ]
                        
                        # Check if URL contains welcome board terms
                        url_lower = clean_url.lower()
                        has_welcome_term = any(term in url_lower for term in welcome_terms)
                        
                        if not any(skip in clean_url.lower() for skip in skip_terms) and any(img_ext in clean_url.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            seen_urls.add(clean_url)
                            
                            # Prioritize URLs with welcome board terms
                            priority = 1 if has_welcome_term else 0
                            
                            results.append({
                                'image_url': clean_url,
                                'title': f'Bing Images Result',
                                'source': 'bing',
                                'url': clean_url,
                                'priority': priority
                            })
                            if len(results) >= max_results:
                                break
                if len(results) >= max_results:
                    break
            
            # Sort by priority (welcome board terms first)
            results.sort(key=lambda x: x.get('priority', 0), reverse=True)
            return results
        except Exception as e:
            log(f"Bing search failed: {e}")
            return []
    
    def _web_search_pinterest(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Pinterest for welcome board images with actual image URLs."""
        try:
            search_url = f"https://www.pinterest.com/search/pins/?q={quote_plus(query)}"
            headers = _headers()
            headers.update({'Referer': 'https://www.pinterest.com/'})
            resp = requests.get(search_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                return []
            
            html = resp.text
            results = []
            
            # Extract pin data - simpler approach
            pin_patterns = [
                r'"pin_id":"([^"]+)"',
                r'/pin/([^/]+)/',
                r'data-pin-id="([^"]+)"'
            ]
            
            seen_pins = set()
            
            for pattern in pin_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    # Clean up the pin ID
                    if match and len(match) > 10:
                        # Remove any extra characters and clean up
                        pin_id = match.split('"')[0].split('/')[0].split('?')[0].split('.')[0].replace('[id]', '')
                        
                        # Use pin IDs that look reasonable
                        if pin_id and len(pin_id) > 10 and not pin_id.endswith('.mjs'):
                            if pin_id not in seen_pins:
                                seen_pins.add(pin_id)
                                
                                # Try to extract actual image URL
                                image_url = get_pinterest_image_url(pin_id)
                                if image_url:
                                    # Apply filtering to exclude drawings/renderings
                                    skip_terms = [
                                        'sketch', 'drawing', 'render', 'rendering', 'illustration', 
                                        'vector', 'clipart', 'graphic', 'design', 'template', 
                                        'mockup', 'cartoon', 'anime', 'art', 'painting'
                                    ]
                                    
                                    # Check if URL contains exclusion terms
                                    url_lower = image_url.lower()
                                    if not any(skip in url_lower for skip in skip_terms):
                                        results.append({
                                            'image_url': image_url,
                                            'title': f'Pinterest Pin - {query}',
                                            'source': 'pinterest',
                                            'url': f"https://www.pinterest.com/pin/{pin_id}/",
                                            'pin_id': pin_id
                                        })
                                        
                                        if len(results) >= max_results:
                                            break
                if len(results) >= max_results:
                    break
            
            return results
        except Exception as e:
            log(f"Pinterest search failed: {e}")
            return []
    
    def _create_search_queries(self, event_type: str, budget_range: str, color_terms: List[str]) -> List[str]:
        """Create multiple search query variations with enhanced color matching."""
        queries = []
        
        # Base terms
        base_terms = [event_type.title(), "welcome board", "welcome sign"]
        
        # Budget-appropriate materials
        if "3000-5000" in budget_range:
            budget_terms = ["simple", "budget", "printed", "sunboard", "cardboard"]
        elif "5001-8000" in budget_range:
            budget_terms = ["mid-range", "layered", "acrylic", "wooden", "foam"]
        elif "8001-15000" in budget_range:
            budget_terms = ["luxury", "premium", "bespoke", "floral", "3D", "metal"]
        else:
            budget_terms = []
        
        # Enhanced color terms for better matching
        enhanced_color_terms = []
        if color_terms:
            for color in color_terms[:2]:  # Use first 2 colors
                enhanced_color_terms.append(color)
                # Add color variations and synonyms
                if color.lower() in ['red', 'orange']:
                    enhanced_color_terms.extend(['bright', 'vibrant', 'bold', 'rich'])
                elif color.lower() in ['pink', 'mint', 'lavender']:
                    enhanced_color_terms.extend(['soft', 'pastel', 'gentle', 'delicate'])
                elif color.lower() in ['purple', 'gold', 'emerald']:
                    enhanced_color_terms.extend(['royal', 'elegant', 'luxury', 'premium'])
                elif color.lower() in ['white', 'beige', 'cream']:
                    enhanced_color_terms.extend(['neutral', 'classic', 'elegant', 'minimal'])
        
        # Query 1: Color-focused with enhanced terms
        query1_parts = base_terms.copy()
        if enhanced_color_terms:
            query1_parts.extend(enhanced_color_terms[:3])  # Use more color terms
        query1_parts.extend(budget_terms)
        query1_parts.extend(["sign", "board", "display", "entrance", "ceremony"])
        queries.append(" ".join(query1_parts))
        
        # Query 2: Color theme emphasis
        query2_parts = ["welcome sign", event_type.title()]
        if enhanced_color_terms:
            query2_parts.extend(enhanced_color_terms[:3])
        query2_parts.extend(budget_terms)
        query2_parts.extend(["board", "display", "entrance", "ceremony", "decor"])
        queries.append(" ".join(query2_parts))
        
        # Query 3: Pinterest-style color search
        query3_parts = [event_type.title(), "welcome board"]
        if enhanced_color_terms:
            query3_parts.extend(enhanced_color_terms[:2])
        query3_parts.extend(["decor", "decoration", "theme", "color", "design"])
        queries.append(" ".join(query3_parts))
        
        # Query 4: Specific color combinations
        if len(color_terms) >= 2:
            query4_parts = [event_type.title(), "welcome sign", color_terms[0], color_terms[1]]
            query4_parts.extend(["board", "display", "ceremony", "wedding"])
            queries.append(" ".join(query4_parts))
        
        return queries
    
    def _score_and_rank_results(self, results: List[Dict], event_type: str) -> List[Dict]:
        """Score and rank results based on relevance."""
        wedding_vendor_domains = [
            'weddingwire', 'shaadisaga', 'wedmegood', 'weddingz', 'weddingbazaar',
            'mywedding', 'weddingplz', 'weddingwishlist', 'weddingwire.in'
        ]
        
        for result in results:
            score = 0
            url_lower = result.get('image_url', '').lower()
            
            # Wedding vendor domains (+3)
            if any(domain in url_lower for domain in wedding_vendor_domains):
                score += 3
            
            # Welcome board terms (+2)
            welcome_terms = ['welcome', 'board', 'sign', 'display', 'entrance']
            if any(term in url_lower for term in welcome_terms):
                score += 2
            
            # Event type match (+2)
            if event_type.lower() in url_lower:
                score += 2
            
            # Realistic photo indicators (+1)
            photo_terms = ['photo', 'diy', 'real', 'actual', 'wedding', 'event', 'decor']
            if any(term in url_lower for term in photo_terms):
                score += 1
            
            # Exclusion terms (-5)
            exclusion_terms = [
                'sketch', 'drawing', 'render', 'rendering', 'illustration', 
                'vector', 'clipart', 'graphic', 'design', 'template', 
                'mockup', 'cartoon', 'anime', 'art', 'painting'
            ]
            if any(term in url_lower for term in exclusion_terms):
                score -= 5
            
            result['relevance_score'] = score
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results
    
    def _score_and_rank_results_with_colors(self, results: List[Dict], event_type: str, color_terms: List[str]) -> List[Dict]:
        """Score and rank results with emphasis on color theme matching."""
        wedding_vendor_domains = [
            'weddingwire', 'shaadisaga', 'wedmegood', 'weddingz', 'weddingbazaar',
            'mywedding', 'weddingplz', 'weddingwishlist', 'weddingwire.in'
        ]
        
        for result in results:
            score = 0
            url_lower = result.get('image_url', '').lower()
            
            # Wedding vendor domains (+3)
            if any(domain in url_lower for domain in wedding_vendor_domains):
                score += 3
            
            # Welcome board terms (+2)
            welcome_terms = ['welcome', 'board', 'sign', 'display', 'entrance']
            if any(term in url_lower for term in welcome_terms):
                score += 2
            
            # Event type match (+2)
            if event_type.lower() in url_lower:
                score += 2
            
            # Color theme matching (+3 for exact color matches)
            if color_terms:
                for color in color_terms:
                    if color.lower() in url_lower:
                        score += 3
                        # Bonus for color combinations
                        if len(color_terms) > 1:
                            score += 1
            
            # Pinterest-specific color indicators (+2)
            pinterest_color_terms = ['decor', 'decoration', 'theme', 'color', 'design', 'style', 'palette']
            if any(term in url_lower for term in pinterest_color_terms):
                score += 2
            
            # Realistic photo indicators (+1)
            photo_terms = ['photo', 'diy', 'real', 'actual', 'wedding', 'event', 'decor']
            if any(term in url_lower for term in photo_terms):
                score += 1
            
            # Exclusion terms (-5)
            exclusion_terms = [
                'sketch', 'drawing', 'render', 'rendering', 'illustration', 
                'vector', 'clipart', 'graphic', 'design', 'template', 
                'mockup', 'cartoon', 'anime', 'art', 'painting'
            ]
            if any(term in url_lower for term in exclusion_terms):
                score -= 5
            
            result['relevance_score'] = score
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results
    
    def _validate_image_content(self, image_url: str) -> bool:
        """Lightweight image content validation."""
        try:
            # For now, just check URL patterns for realistic images
            url_lower = image_url.lower()
            
            # Exclude very small images (likely thumbnails)
            if any(size in url_lower for size in ['150x', '200x', 'thumb', 'small']):
                return False
            
            # Exclude very large images (likely high-res renders)
            if any(size in url_lower for size in ['4000x', '5000x', '6000x', '8k', '4k']):
                return False
            
            # Prefer landscape aspect ratios (welcome boards are typically wide)
            if any(ratio in url_lower for ratio in ['16x9', '4x3', '3x2']):
                return True
            
            # Default to True for other cases
            return True
            
        except Exception:
            return True
    
    def search_welcome_boards(self, event_type: str, budget_range: str, 
                            color_theme: str, max_results_per_source: int = 20) -> Dict:
        """
        Enhanced search function with multiple queries and result scoring.
        
        Args:
            event_type: engagement, haldi, mehendi, sangeet, wedding, reception
            budget_range: ₹3000-₹5000, ₹5001-₹8000, ₹8001-₹15000
            color_theme: color names or hex codes like "red", "#ff0000", "blue white"
            max_results_per_source: max results per search source (increased to 20)
            
        Returns:
            Dict with search results from local + web sources
        """
        
        log(f"Searching for {event_type} welcome boards in {budget_range} with {color_theme} theme")
        
        # Convert color theme to searchable terms
        color_terms = self._extract_colors_from_hex(color_theme)
        
        # Create multiple search queries
        search_queries = self._create_search_queries(event_type, budget_range, color_terms)
        log(f"Using {len(search_queries)} query variations")
        
        # Get a sample image for local similarity (if available)
        sample_embedding = None
        if self.local_database:
            # Find a sample image matching the criteria
            for image_path, data in self.local_database.items():
                if data['event_type'] == event_type:
                    # Convert budget range for comparison (remove currency symbols)
                    data_price = data['price_category'] or ""
                    if "3000-5000" in budget_range and "3000-5000" in data_price.replace("₹", "").replace("Rs", ""):
                        sample_embedding = data['embedding']
                        break
                    elif "5001-8000" in budget_range and "5001-8000" in data_price.replace("₹", "").replace("Rs", ""):
                        sample_embedding = data['embedding']
                        break
                    elif "8001-15000" in budget_range and "8001-15000" in data_price.replace("₹", "").replace("Rs", ""):
                        sample_embedding = data['embedding']
                        break
            
            # If no exact match, use any image from the same event type
            if sample_embedding is None:
                for image_path, data in self.local_database.items():
                    if data['event_type'] == event_type:
                        sample_embedding = data['embedding']
                        break
        
        # Search local database
        local_results = []
        if sample_embedding is not None:
            local_results = self._find_local_similar(sample_embedding, event_type, budget_range, 8)
        
        # Search web sources with multiple queries (Google and Pinterest only)
        all_google_results = []
        all_pinterest_results = []
        
        for query in search_queries:
            log(f"Searching with query: {query}")
            
            # Search Google with enhanced similarity matching
            google_results = self._web_search_google_enhanced(query, max_results_per_source, sample_embedding, event_type)
            pinterest_results = self._web_search_pinterest(query, max_results_per_source)
            
            all_google_results.extend(google_results)
            all_pinterest_results.extend(pinterest_results)
        
        # Deduplicate and score results
        google_results = self._deduplicate_results(all_google_results)
        pinterest_results = self._deduplicate_results(all_pinterest_results)
        
        # Score and rank results with color theme emphasis
        google_results = self._score_and_rank_results(google_results, event_type)
        pinterest_results = self._score_and_rank_results_with_colors(pinterest_results, event_type, color_terms)
        
        # Apply content validation
        google_results = [r for r in google_results if self._validate_image_content(r.get('image_url', ''))]
        pinterest_results = [r for r in pinterest_results if self._validate_image_content(r.get('image_url', ''))]
        
        # Limit to top results per source (boost Pinterest for color themes)
        google_results = google_results[:10]  # Slightly fewer Google results
        pinterest_results = pinterest_results[:10]  # More Pinterest results for color themes
        
        # Combine results
        total_results = {
            'query': search_queries[0],  # Primary query
            'queries_used': search_queries,
            'event_type': event_type,
            'budget_range': budget_range,
            'color_theme': color_theme,
            'color_terms_used': color_terms,
            'local_results': local_results,
            'google_results': google_results,
            'pinterest_results': pinterest_results,
            'total_count': len(local_results) + len(google_results) + len(pinterest_results),
            'success': True
        }
        
        log(f"Found {total_results['total_count']} total results after filtering and scoring")
        return total_results
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on image URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            image_url = result.get('image_url', '')
            if image_url and image_url not in seen_urls:
                seen_urls.add(image_url)
                unique_results.append(result)
        
        return unique_results

# Global backend instance
_backend_instance = None

def get_backend():
    """Get or create backend instance."""
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = WelcomeBoardBackend()
    return _backend_instance

def reset_backend():
    """Reset the backend instance to force reload of enhanced methods."""
    global _backend_instance
    _backend_instance = None

def search_welcome_boards(event_type: str, budget_range: str, color_theme: str) -> Dict:
    """
    Main backend function - call this to search for welcome boards.
    
    Args:
        event_type: engagement, haldi, mehendi, sangeet, wedding, reception
        budget_range: ₹3000-₹5000, ₹5001-₹8000, ₹8001-₹15000  
        color_theme: color names or hex codes like "red", "#ff0000", "blue white"
        
    Returns:
        Dict with search results
    """
    # Reset backend to ensure we get the latest enhanced methods
    reset_backend()
    backend = get_backend()
    return backend.search_welcome_boards(event_type, budget_range, color_theme)

def generate_mood_board_pdf(event_type: str, budget_range: str, color_theme: str, selected_images: List[Dict] = None) -> Dict:
    """
    Generate a PDF mood board from search results.
    
    Args:
        event_type: engagement, haldi, mehendi, sangeet, wedding, reception
        budget_range: ₹3000-₹5000, ₹5001-₹8000, ₹8001-₹15000  
        color_theme: color names or hex codes like "red", "#ff0000", "blue white"
        selected_images: Optional list of selected images to use directly
        
    Returns:
        Dict with PDF generation results
    """
    if not PDF_AVAILABLE:
        return {
            'success': False,
            'error': 'PDF generation not available - reportlab not installed',
            'pdf_path': None
        }
    
    if selected_images:
        # Use provided images directly
        search_results = {
            'event_type': event_type,
            'budget_range': budget_range,
            'color_theme': color_theme,
            'total_count': len(selected_images),
            'query': 'User Selection',
            'local_results': [img for img in selected_images if img.get('source') == 'local'],
            'google_results': [img for img in selected_images if img.get('source') == 'google'],
            'bing_results': [],
            'pinterest_results': [img for img in selected_images if img.get('source') == 'pinterest']
        }
        # If sources aren't set, put everything in local or google as fallback
        if not any([search_results['local_results'], search_results['google_results'], search_results['pinterest_results']]):
             search_results['local_results'] = selected_images

    else:
        # Get search results first
        search_results = search_welcome_boards(event_type, budget_range, color_theme)
    
    if search_results.get('total_count', 0) == 0:
        return {
            'success': False,
            'error': 'No search results found',
            'pdf_path': None
        }
    
    # Generate PDF using the imported function
    from pdf_generator import generate_mood_board_pdf as generate_pdf
    pdf_result = generate_pdf(event_type, budget_range, color_theme, search_results)
    
    # Combine search and PDF results
    result = {
        'search_results': search_results,
        'pdf_generation': pdf_result,
        'success': pdf_result.get('success', False),
        'filename': os.path.basename(pdf_result.get('pdf_path', '')) if pdf_result.get('pdf_path') else None
    }
    
    return result

def test_backend():
    """Test the backend function."""
    print("Testing Welcome Board Backend")
    print("=" * 50)
    
    test_cases = [
        ("engagement", "3000-5000", "red white"),
        ("haldi", "5001-8000", "#ffa500"),
        ("wedding", "8001-15000", "gold white")
    ]
    
    for event_type, budget, color in test_cases:
        print(f"\nTesting: {event_type} | {budget} | {color}")
        try:
            results = search_welcome_boards(event_type, budget, color)
            print(f"Success: {results['total_count']} results found")
            print(f"   Query: {results['query']}")
            print(f"   Local: {len(results['local_results'])}")
            print(f"   Google: {len(results['google_results'])}")
            print(f"   Bing: {len(results['bing_results'])}")
            print(f"   Pinterest: {len(results['pinterest_results'])}")
        except Exception as e:
            print(f"Failed: {e}")
    
    print("\nBackend test complete!")

if __name__ == "__main__":
    test_backend()
