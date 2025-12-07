#!/usr/bin/env python3
"""
Similarity Ranker for Pinterest Scraping Results
Ranks scraped Pinterest images by similarity to existing sample database
"""

import os
import json
import numpy as np
from PIL import Image
import torch
import open_clip
from typing import List, Dict, Optional
import requests
from io import BytesIO
import tempfile

def log(msg: str):
    print(f"[ranker] {msg}")

class SimilarityRanker:
    def __init__(self, local_images_dir: str = "downloaded_images"):
        """
        Initialize similarity ranker with existing sample database.
        
        Args:
            local_images_dir: Directory containing existing sample images
        """
        self.local_images_dir = local_images_dir
        self.model = None
        self.preprocess = None
        self.sample_embeddings = {}
        
        self._load_clip_model()
        self._load_sample_embeddings()
    
    def _load_clip_model(self):
        """Load CLIP model for image embeddings."""
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32', 
                pretrained='openai'
            )
            model.eval()
            self.model = model
            self.preprocess = preprocess
            log("CLIP model loaded successfully")
        except Exception as e:
            log(f"Failed to load CLIP model: {e}")
            self.model = None
            self.preprocess = None
    
    def _get_image_embedding(self, image_source) -> Optional[np.ndarray]:
        """
        Get CLIP embedding for an image.
        
        Args:
            image_source: Can be file path (str), URL (str), or PIL Image
            
        Returns:
            Numpy array of image embedding
        """
        if not self.model or not self.preprocess:
            return None
        
        try:
            # Load image based on source type
            if isinstance(image_source, str):
                if image_source.startswith('http'):
                    # Download from URL
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(image_source, headers=headers, timeout=10)
                    if response.status_code != 200:
                        log(f"Download failed for {image_source}: {response.status_code}")
                        return None
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content)).convert('RGB')
                else:
                    # Load from file
                    image = Image.open(image_source).convert('RGB')
            else:
                # Assume it's already a PIL Image
                image = image_source.convert('RGB')
            
            # Preprocess and get embedding
            image_tensor = self.preprocess(image).unsqueeze(0)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                return image_features.numpy().flatten()
        
        except Exception as e:
            log(f"Failed to get embedding: {e}")
            return None
    
    def _load_sample_embeddings(self):
        """Load embeddings for all existing sample images."""
        if not os.path.exists(self.local_images_dir):
            log(f"Sample directory not found: {self.local_images_dir}")
            return
        
        log("Loading embeddings for existing samples...")
        
        # Find all sample images
        import glob
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(
                glob.glob(os.path.join(self.local_images_dir, '**', ext), recursive=True)
            )
        
        log(f"Found {len(image_files)} sample images")
        
        # Generate embeddings
        for image_path in image_files:
            embedding = self._get_image_embedding(image_path)
            if embedding is not None:
                # Extract metadata from path
                path_parts = image_path.split(os.sep)
                
                price_category = None
                event_type = None
                
                for part in path_parts:
                    if '3000-5000' in part:
                        price_category = '3000-5000'
                    elif '5001-8000' in part:
                        price_category = '5001-8000'
                    elif '8001-15000' in part:
                        price_category = '8001-15000'
                    
                    if part.lower() in ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']:
                        event_type = part.lower()
                
                self.sample_embeddings[image_path] = {
                    'embedding': embedding,
                    'price_category': price_category,
                    'event_type': event_type,
                    'filename': os.path.basename(image_path)
                }
        
        log(f"Loaded {len(self.sample_embeddings)} sample embeddings")
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        ))
    
    def rank_scraped_results(
        self,
        scraped_results: List[Dict],
        event_type: Optional[str] = None,
        budget_range: Optional[str] = None,
        top_k: int = 50
    ) -> List[Dict]:
        """
        Rank scraped Pinterest results by similarity to existing samples.
        
        Args:
            scraped_results: List of scraped Pinterest pins with image_url
            event_type: Optional event type filter
            budget_range: Optional budget range filter
            top_k: Return top K results
            
        Returns:
            Ranked list of results with similarity scores
        """
        if not self.sample_embeddings:
            log("No sample embeddings available")
            return scraped_results[:top_k]
        
        log(f"Ranking {len(scraped_results)} scraped results...")
        
        ranked_results = []
        
        for idx, result in enumerate(scraped_results):
            image_url = result.get('image_url', '')
            if not image_url:
                continue
            
            # Get embedding for scraped image
            scraped_embedding = self._get_image_embedding(image_url)
            if scraped_embedding is None:
                log(f"Skipping result {idx+1}/{len(scraped_results)} - failed to get embedding")
                continue
            
            # Calculate similarities to all samples
            similarities = []
            
            for sample_path, sample_data in self.sample_embeddings.items():
                # Apply filters if specified
                if event_type and sample_data['event_type'] != event_type.lower():
                    continue
                
                if budget_range:
                    if budget_range not in (sample_data['price_category'] or ''):
                        continue
                
                # Calculate similarity
                similarity = self.calculate_similarity(
                    scraped_embedding,
                    sample_data['embedding']
                )
                
                similarities.append({
                    'similarity': similarity,
                    'sample_path': sample_path,
                    'sample_event': sample_data['event_type'],
                    'sample_budget': sample_data['price_category']
                })
            
            if similarities:
                # Get best match and average similarity
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                best_match = similarities[0]
                avg_similarity = np.mean([s['similarity'] for s in similarities[:5]])
                
                # Add ranking info to result
                ranked_result = result.copy()
                ranked_result['similarity_score'] = float(best_match['similarity'])
                ranked_result['avg_similarity'] = float(avg_similarity)
                ranked_result['best_match'] = {
                    'sample_path': best_match['sample_path'],
                    'sample_event': best_match['sample_event'],
                    'sample_budget': best_match['sample_budget'],
                    'similarity': float(best_match['similarity'])
                }
                ranked_result['ranking_index'] = idx
                
                ranked_results.append(ranked_result)
            
            log(f"Processed {idx+1}/{len(scraped_results)} results")
        
        # Sort by similarity score
        ranked_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        if ranked_results:
            log(f"Ranking complete. Top result similarity: {ranked_results[0]['similarity_score']:.3f}")
            return ranked_results[:top_k]
        else:
            log("Ranking failed (all downloads failed). Returning original results as fallback.")
            # Failsafe: Return original results with 0 similarity so they are still displayed
            fallback_results = []
            for res in scraped_results[:top_k]:
                r = res.copy()
                r['similarity_score'] = 0.0
                r['avg_similarity'] = 0.0
                # Add dummy best_match to prevent frontend errors
                r['best_match'] = {
                    'sample_path': 'N/A',
                    'sample_event': 'N/A',
                    'sample_budget': 'N/A',
                    'similarity': 0.0
                }
                fallback_results.append(r)
            return fallback_results
    
    def get_diverse_top_results(
        self,
        ranked_results: List[Dict],
        top_k: int = 25,
        diversity_threshold: float = 0.15
    ) -> List[Dict]:
        """
        Get top K diverse results (avoid very similar images).
        
        Args:
            ranked_results: Already ranked results
            top_k: Number of results to return
            diversity_threshold: Min difference in similarity for diversity
            
        Returns:
            List of diverse top results
        """
        if not ranked_results:
            return []
        
        diverse_results = [ranked_results[0]]  # Always include top result
        
        for result in ranked_results[1:]:
            # Check if this result is sufficiently different from selected ones
            is_diverse = True
            
            for selected in diverse_results:
                similarity_diff = abs(
                    result['similarity_score'] - selected['similarity_score']
                )
                
                if similarity_diff < diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_results.append(result)
            
            if len(diverse_results) >= top_k:
                break
        
        log(f"Selected {len(diverse_results)} diverse results from {len(ranked_results)} total")
        
        return diverse_results
    
    def save_ranked_results(self, ranked_results: List[Dict], output_path: str):
        """Save ranked results to JSON file."""
        try:
            # Prepare data for JSON serialization
            save_data = {
                'total_results': len(ranked_results),
                'ranked_at': str(np.datetime64('now')),
                'results': ranked_results
            }
            
            with open(output_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            log(f"Saved ranked results to {output_path}")
            return True
        
        except Exception as e:
            log(f"Failed to save results: {e}")
            return False


def test_ranker():
    """Test the similarity ranker."""
    print("=" * 60)
    print("Similarity Ranker Test")
    print("=" * 60)
    
    ranker = SimilarityRanker()
    
    # Check if we have sample embeddings
    if not ranker.sample_embeddings:
        print("\n❌ No sample embeddings found")
        print("Make sure you have images in the 'downloaded_images' directory")
        return
    
    print(f"\n✅ Loaded {len(ranker.sample_embeddings)} sample embeddings")
    
    # Create mock scraped results for testing
    mock_results = [
        {
            'pin_id': 'test1',
            'pin_url': 'https://pinterest.com/pin/test1',
            'image_url': 'https://i.pinimg.com/564x/example1.jpg',
            'title': 'Test Pin 1',
            'source': 'apify_pinterest'
        }
    ]
    
    print("\n📊 Testing with mock data...")
    print("(To test with real data, use scraped Pinterest results)")
    
    # For a real test, you would use actual scraped results:
    # from apify_pinterest_scraper import ApifyPinterestScraper
    # scraper = ApifyPinterestScraper()
    # result = scraper.scrape_pinterest_search("wedding welcome board", max_results=10)
    # ranked = ranker.rank_scraped_results(result['results'])


if __name__ == "__main__":
    test_ranker()



