#!/usr/bin/env python3
"""
Simple Flask Frontend for Welcome Board Search
"""

from flask import Flask, render_template, request, jsonify, send_file, abort
from backend_search import search_welcome_boards

try:
    from pdf_generator import generate_mood_board_pdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
import json
import os
import requests
from urllib.parse import unquote

app = Flask(__name__)

@app.route('/')
def index():
    """Main page with search form."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests."""
    try:
        data = request.get_json()
        
        event_type = data.get('event_type', '').lower()
        budget_range = data.get('budget_range', '')
        color_theme = data.get('color_theme', '')
        
        # Validate inputs
        valid_events = ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']
        valid_budgets = ['3000-5000', '5001-8000', '8001-15000']
        
        if event_type not in valid_events:
            return jsonify({'error': f'Invalid event type. Must be one of: {", ".join(valid_events)}'}), 400
        
        if budget_range not in valid_budgets:
            return jsonify({'error': f'Invalid budget range. Must be one of: {", ".join(valid_budgets)}'}), 400
        
        if not color_theme.strip():
            return jsonify({'error': 'Color theme is required'}), 400
        
        # Perform search
        results = search_welcome_boards(event_type, budget_range, color_theme)
        
        # Format results for frontend
        formatted_results = {
            'success': True,
            'query': results['query'],
            'total_count': results['total_count'],
            'event_type': results['event_type'],
            'budget_range': results['budget_range'],
            'color_theme': results['color_theme'],
            'color_terms_used': results['color_terms_used'],
            'results': {
                'local': results['local_results'],
                'google': results['google_results'],
                'bing': results['bing_results'],
                'pinterest': results['pinterest_results']
            }
        }
        
        return jsonify(formatted_results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """Handle PDF generation requests."""
    try:
        if not PDF_AVAILABLE:
            return jsonify({'error': 'PDF generation not available - reportlab not installed'}), 400
            
        data = request.get_json()
        
        event_type = data.get('event_type', '').lower()
        budget_range = data.get('budget_range', '')
        color_theme = data.get('color_theme', '')
        
        # Validate inputs
        valid_events = ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']
        valid_budgets = ['3000-5000', '5001-8000', '8001-15000']
        
        if event_type not in valid_events:
            return jsonify({'error': f'Invalid event type. Must be one of: {", ".join(valid_events)}'}), 400
        
        if budget_range not in valid_budgets:
            return jsonify({'error': f'Invalid budget range. Must be one of: {", ".join(valid_budgets)}'}), 400
        
        if not color_theme.strip():
            return jsonify({'error': 'Color theme is required'}), 400
        
        # Generate PDF
        from backend_search import generate_mood_board_pdf
        result = generate_mood_board_pdf(event_type, budget_range, color_theme)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-pdf/<filename>')
def download_pdf(filename):
    """Serve PDF files for download."""
    try:
        # Security check - only allow PDF files from generated_pdfs directory
        if not filename.endswith('.pdf') or '..' in filename or '/' in filename:
            abort(403)
        
        pdf_path = os.path.join('generated_pdfs', filename)
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            abort(404)
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        abort(404)

@app.route('/local-image')
def local_image():
    """Serve local images."""
    try:
        image_path = unquote(request.args.get('path', ''))
        
        # Security check - only allow images from downloaded_images directory
        if not image_path.startswith('downloaded_images'):
            abort(403)
        
        # Check if file exists
        if not os.path.exists(image_path):
            abort(404)
        
        # Check if it's an image file
        if not image_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            abort(403)
        
        return send_file(image_path, mimetype='image/jpeg')
        
    except Exception as e:
        abort(404)

@app.route('/proxy-image')
def proxy_image():
    """Proxy external images to avoid CORS issues."""
    try:
        import requests
        from flask import Response
        
        image_url = request.args.get('url', '')
        if not image_url.startswith('http'):
            abort(400)
        
        # Download the image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper headers
        return Response(
            response.content,
            mimetype=response.headers.get('content-type', 'image/jpeg'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=3600'
            }
        )
        
    except Exception as e:
        abort(404)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Welcome Board Search API is running'})

@app.route('/data-collection')
def data_collection():
    """Data collection management page."""
    return render_template('data_collection.html')

@app.route('/scrape-pinterest', methods=['POST'])
def scrape_pinterest():
    """Scrape Pinterest using Apify and rank results."""
    try:
        from apify_pinterest_scraper import ApifyPinterestScraper, create_search_keywords
        from similarity_ranker import SimilarityRanker
        
        data = request.get_json()
        
        event_type = data.get('event_type', '').lower()
        budget_range = data.get('budget_range', '')
        color_theme = data.get('color_theme', '')
        max_results = data.get('max_results', 10)
        
        # Validate inputs
        valid_events = ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']
        if event_type not in valid_events:
            return jsonify({'error': f'Invalid event type'}), 400
        
        # Create search keywords
        keywords = create_search_keywords(event_type, budget_range, color_theme)
        
        # Scrape Pinterest (use first keyword)
        scraper = ApifyPinterestScraper()
        scrape_result = scraper.scrape_pinterest_search(
            search_keyword=keywords[0],
            max_pins=max_results
        )
        
        if not scrape_result['success'] or not scrape_result['results']:
            return jsonify({
                'error': 'Failed to scrape Pinterest or no results found',
                'details': scrape_result
            }), 500
        
        # Rank by similarity
        ranker = SimilarityRanker()
        ranked_results = ranker.rank_scraped_results(
            scrape_result['results'],
            event_type=event_type,
            budget_range=budget_range,
            top_k=50
        )
        
        # Get diverse results
        diverse_results = ranker.get_diverse_top_results(ranked_results, top_k=25)
        
        return jsonify({
            'success': True,
            'total_scraped': scrape_result['total_results'],
            'total_ranked': len(ranked_results),
            'diverse_results': len(diverse_results),
            'results': diverse_results,
            'keyword_used': keywords[0]
        })
        
    except ImportError as e:
        return jsonify({
            'error': 'Required modules not available. Install dependencies or set APIFY_API_TOKEN',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/unified-search', methods=['POST'])
def unified_search():
    """Search both Google and Pinterest with similarity ranking."""
    try:
        from unified_similarity_search import UnifiedSimilaritySearch
        
        data = request.get_json()
        
        event_type = data.get('event_type', '').lower()
        budget_range = data.get('budget_range', '')
        color_theme = data.get('color_theme', '')
        max_google_results = data.get('max_google_results', 25)
        max_pinterest_results = data.get('max_pinterest_results', 10)
        include_google = data.get('include_google', True)
        include_pinterest = data.get('include_pinterest', True)
        
        # Validate inputs
        valid_events = ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']
        if event_type not in valid_events:
            return jsonify({'error': f'Invalid event type'}), 400
        
        # Perform unified search
        searcher = UnifiedSimilaritySearch()
        result = searcher.search_and_rank(
            event_type=event_type,
            budget_range=budget_range,
            color_theme=color_theme,
            max_google_results=max_google_results,
            max_pinterest_results=max_pinterest_results,
            include_google=include_google,
            include_pinterest=include_pinterest
        )
        
        # Load downloaded images and filter them out
        tracking_file = 'data/downloaded_images.json'
        downloaded_ids = set()
        if os.path.exists(tracking_file):
            try:
                with open(tracking_file, 'r') as f:
                    downloaded_ids = set(json.load(f))
            except:
                pass
        
        # Filter out downloaded images from results
        if downloaded_ids:
            if 'google' in result and 'results' in result['google']:
                result['google']['results'] = [
                    r for r in result['google']['results'] 
                    if r.get('pin_id') not in downloaded_ids
                ]
                result['google']['total_results'] = len(result['google']['results'])
            
            if 'pinterest' in result and 'results' in result['pinterest']:
                original_count = len(result['pinterest']['results'])
                result['pinterest']['results'] = [
                    r for r in result['pinterest']['results'] 
                    if r.get('pin_id') not in downloaded_ids
                ]
                filtered_count = original_count - len(result['pinterest']['results'])
                result['pinterest']['total_results'] = len(result['pinterest']['results'])
                
                # Add info about filtered results
                if filtered_count > 0:
                    result['filtered_downloaded'] = filtered_count
        
        return jsonify(result)
        
    except ImportError as e:
        return jsonify({
            'error': 'Required modules not available. Install dependencies',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-selected-images', methods=['POST'])
def download_selected_images():
    """Download user-selected images to local database."""
    try:
        import shutil
        from datetime import datetime
        
        data = request.get_json(force=True)
        
        if data is None:
            return jsonify({'error': 'Request body is empty'}), 400
        
        selected_results = data.get('selected_results', [])
        # Filter out None values (can happen with checkbox indices)
        selected_results = [r for r in selected_results if r is not None]
        
        event_type = data.get('event_type', '').lower()
        budget_range = data.get('budget_range', '')
        
        if not selected_results:
            return jsonify({'error': 'No images selected'}), 400
        
        # Determine price category folder
        if '3000-5000' in budget_range:
            price_folder = 'Welcome_board_decor_(3000-5000)'
        elif '5001-8000' in budget_range:
            price_folder = 'Welcome_board_decor_(5001-8000)'
        elif '8001-15000' in budget_range:
            price_folder = 'Welcome_board_decor_(8001-15000)'
        else:
            price_folder = 'Welcome_board_decor_(other)'
        
        # Create target directory
        target_dir = os.path.join(
            'downloaded_images',
            price_folder,
            event_type.capitalize(),
            'user_selected'
        )
        os.makedirs(target_dir, exist_ok=True)
        
        # Download images
        downloaded = []
        failed = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for idx, result in enumerate(selected_results):
            try:
                image_url = result.get('image_url')
                pin_id = result.get('pin_id', f'unknown_{idx}')
                
                if not image_url:
                    continue
                
                # Download image
                response = requests.get(image_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = 'jpg'
                elif 'png' in content_type:
                    ext = 'png'
                elif 'webp' in content_type:
                    ext = 'webp'
                else:
                    ext = 'jpg'  # default
                
                # Save image
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'user_selected_{pin_id}_{timestamp}.{ext}'
                filepath = os.path.join(target_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Save metadata
                metadata = {
                    'pin_id': result.get('pin_id'),
                    'pin_url': result.get('pin_url'),
                    'title': result.get('title'),
                    'description': result.get('description'),
                    'similarity_score': result.get('similarity_score'),
                    'downloaded_at': datetime.now().isoformat(),
                    'event_type': event_type,
                    'budget_range': budget_range
                }
                
                metadata_path = filepath.replace(f'.{ext}', '.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                downloaded.append({
                    'filename': filename,
                    'path': filepath,
                    'pin_id': pin_id
                })
                
            except Exception as e:
                failed.append({
                    'pin_id': result.get('pin_id', 'unknown'),
                    'error': str(e)
                })
        
        # Track downloaded pin_ids to exclude from future searches
        if downloaded:
            tracking_file = 'data/downloaded_images.json'
            os.makedirs('data', exist_ok=True)
            
            # Load existing tracking
            downloaded_ids = set()
            if os.path.exists(tracking_file):
                try:
                    with open(tracking_file, 'r') as f:
                        downloaded_ids = set(json.load(f))
                except:
                    pass
            
            # Add new downloads
            for item in downloaded:
                if item['pin_id']:
                    downloaded_ids.add(item['pin_id'])
            
            # Save updated tracking
            with open(tracking_file, 'w') as f:
                json.dump(list(downloaded_ids), f, indent=2)
        
        return jsonify({
            'success': True,
            'downloaded': len(downloaded),
            'failed': len(failed),
            'target_directory': target_dir,
            'downloaded_files': downloaded,
            'failed_downloads': failed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/database-stats')
def database_stats():
    """Get statistics about the local image database."""
    try:
        import glob
        
        base_dir = 'downloaded_images'
        if not os.path.exists(base_dir):
            return jsonify({
                'success': True,
                'total_images': 0,
                'by_category': {}
            })
        
        stats = {
            'total_images': 0,
            'by_price_category': {},
            'by_event_type': {},
            'by_source': {}
        }
        
        # Count images
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(glob.glob(os.path.join(base_dir, '**', ext), recursive=True))
        
        stats['total_images'] = len(image_files)
        
        # Categorize
        for img_path in image_files:
            parts = img_path.split(os.sep)
            
            # Price category
            for part in parts:
                if '3000-5000' in part:
                    stats['by_price_category']['3000-5000'] = stats['by_price_category'].get('3000-5000', 0) + 1
                elif '5001-8000' in part:
                    stats['by_price_category']['5001-8000'] = stats['by_price_category'].get('5001-8000', 0) + 1
                elif '8001-15000' in part:
                    stats['by_price_category']['8001-15000'] = stats['by_price_category'].get('8001-15000', 0) + 1
            
            # Event type
            for part in parts:
                if part.lower() in ['engagement', 'haldi', 'mehendi', 'sangeet', 'wedding', 'reception']:
                    event = part.lower()
                    stats['by_event_type'][event] = stats['by_event_type'].get(event, 0) + 1
            
            # Source (provided_sample vs user_selected)
            if 'provided_sample' in img_path:
                stats['by_source']['provided_sample'] = stats['by_source'].get('provided_sample', 0) + 1
            elif 'user_selected' in img_path:
                stats['by_source']['user_selected'] = stats['by_source'].get('user_selected', 0) + 1
            else:
                stats['by_source']['other'] = stats['by_source'].get('other', 0) + 1
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("Starting Welcome Board Search Frontend...")
    print("Open your browser to: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
