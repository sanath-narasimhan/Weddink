#!/usr/bin/env python3
"""
PDF Generator for Mood Boards
Creates professional PDF presentations of welcome board search results
"""

import os
import requests
import io
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import List, Dict
import tempfile
import time
from datetime import datetime

def log(msg: str):
    try:
        print(f"[pdf] {msg}")
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        print(f"[pdf] {msg.encode('ascii', 'ignore').decode('ascii')}")

class MoodBoardPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=28,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=18,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#34495e'),
            fontName='Helvetica'
        ))
        
        # Section title style
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        # Detail style
        self.styles.add(ParagraphStyle(
            name='Detail',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#34495e'),
            fontName='Helvetica'
        ))
        
        # Caption style
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#95a5a6'),
            fontName='Helvetica'
        ))
    
    def _download_image(self, image_url: str, max_size: int = 512) -> bytes:
        """Download and resize an image for PDF embedding."""
        try:
            if image_url.startswith('http'):
                # Skip Pinterest URLs as they don't return direct images
                if 'pinterest.com' in image_url:
                    return None
                
                # Download external image
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(image_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # Check if it's actually an image
                content_type = response.headers.get('content-type', '').lower()
                if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'jpg', 'png', 'webp']):
                    return None
                
                image_data = response.content
            else:
                # Local image
                with open(image_url, 'rb') as f:
                    image_data = f.read()
            
            # Process image with PIL
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
            
        except Exception as e:
            log(f"Failed to process image {image_url}: {e}")
            return None
    
    def _create_image_grid(self, results: Dict, max_images_per_page: int = 6) -> List:
        """Create image grid for PDF pages."""
        elements = []
        
        # Collect all images
        all_images = []
        for source, images in results.items():
            if source in ['local_results', 'google_results', 'bing_results', 'pinterest_results']:
                for img in images:
                    if img.get('image_url'):
                        all_images.append({
                            'url': img['image_url'],
                            'source': source.replace('_results', '').title(),
                            'title': img.get('title', ''),
                            'similarity': img.get('similarity', 0),
                            'price_category': img.get('price_category', '')
                        })
        
        # Sort by similarity (if available) and source preference
        def sort_key(img):
            source_order = {'Local': 0, 'Google': 1, 'Bing': 2, 'Pinterest': 3}
            similarity = img.get('similarity', 0)
            source = img.get('source', 'Other')
            return (source_order.get(source, 99), -similarity)
        
        all_images.sort(key=sort_key)
        
        # Create pages with image grids
        for i in range(0, len(all_images), max_images_per_page):
            page_images = all_images[i:i + max_images_per_page]
            
            # Create table for image grid (2 columns x 3 rows max)
            table_data = []
            for row in range(0, len(page_images), 2):
                row_data = []
                for col in range(2):
                    img_idx = row + col
                    if img_idx < len(page_images):
                        img = page_images[img_idx]
                        
                        # Download and process image
                        image_data = self._download_image(img['url'])
                        if image_data:
                            # Create image element with larger size for better quality
                            img_element = RLImage(io.BytesIO(image_data), width=3*inch, height=2.4*inch)
                            
                            # Create caption
                            caption_parts = [img['source']]
                            if img.get('price_category'):
                                # Clean currency symbols for PDF compatibility
                                price = img['price_category'].replace('₹', 'Rs').replace('Rs', 'Rs')
                                caption_parts.append(price)
                            if img.get('similarity', 0) > 0:
                                caption_parts.append(f"Similarity: {img['similarity']:.1%}")
                            
                            caption = Paragraph("<br/>".join(caption_parts), self.styles['Caption'])
                            
                            # Combine image and caption
                            cell_content = [img_element, Spacer(1, 0.1*inch), caption]
                            row_data.append(cell_content)
                        elif img['source'] == 'pinterest' and img.get('url'):
                            # For Pinterest, show a link instead of image
                            pinterest_link = img['url']
                            placeholder = Paragraph(
                                f"<b>Pinterest Image</b><br/>View on Pinterest:<br/><i>{pinterest_link}</i>", 
                                self.styles['Caption']
                            )
                            row_data.append(placeholder)
                        else:
                            # Placeholder for failed images
                            placeholder = Paragraph(f"<i>Image unavailable</i><br/>{img['source']}", self.styles['Caption'])
                            row_data.append(placeholder)
                    else:
                        row_data.append("")
                
                table_data.append(row_data)
            
            if table_data:
                # Create table with enhanced styling
                table = Table(table_data, colWidths=[3.5*inch, 3.5*inch])
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 0.5*inch))
        
        return elements
    
    def _get_theme_colors(self, color_theme: str) -> Dict:
        """Get color scheme based on theme."""
        theme_colors = {
            'bold': {'primary': '#e74c3c', 'secondary': '#f39c12', 'accent': '#e67e22'},
            'pastel': {'primary': '#f8b5c1', 'secondary': '#a8e6cf', 'accent': '#ffd3a5'},
            'royal': {'primary': '#8e44ad', 'secondary': '#f1c40f', 'accent': '#2c3e50'},
            'neutral': {'primary': '#95a5a6', 'secondary': '#ecf0f1', 'accent': '#34495e'},
            'other': {'primary': '#3498db', 'secondary': '#2ecc71', 'accent': '#9b59b6'}
        }
        
        theme_lower = color_theme.lower()
        for theme_name, colors in theme_colors.items():
            if theme_name in theme_lower or theme_lower in theme_name:
                return colors
        
        return theme_colors['other']  # Default fallback

    def generate_mood_board(self, event_type: str, budget_range: str, 
                          color_theme: str, results: Dict, output_path: str) -> Dict:
        """
        Generate a mood board PDF.
        
        Args:
            event_type: Type of event (wedding, engagement, etc.)
            budget_range: Budget range (₹3000-₹5000, etc.)
            color_theme: Color theme (bold, pastel, etc.)
            results: Search results dictionary
            output_path: Output PDF file path
            
        Returns:
            Dict with generation status and metadata
        """
        try:
            log(f"Generating mood board PDF: {output_path}")
            
            # Get theme colors
            theme_colors = self._get_theme_colors(color_theme)
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                  rightMargin=60, leftMargin=60,
                                  topMargin=60, bottomMargin=60)
            
            # Build content
            story = []
            
            # Cover page with enhanced design
            story.append(Spacer(1, 0.8*inch))
            
            # Main title with theme color
            title_style = ParagraphStyle(
                'CoverTitle',
                parent=self.styles['CustomTitle'],
                textColor=colors.HexColor(theme_colors['primary'])
            )
            story.append(Paragraph(f"{event_type.title()} Welcome Board", title_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Subtitle
            story.append(Paragraph("Personalized Mood Board Collection", self.styles['CustomSubtitle']))
            
            story.append(Spacer(1, 0.6*inch))
            
            # Event details in a styled box
            details_data = [
                ['Event Type', event_type.title()],
                ['Budget Range', budget_range],
                ['Color Theme', color_theme.title()]
            ]
            
            details_table = Table(details_data, colWidths=[1.5*inch, 2*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(theme_colors['secondary'])),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
            ]))
            
            story.append(details_table)
            
            story.append(Spacer(1, 0.8*inch))
            
            # Generated info
            timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            story.append(Paragraph(f"<i>Generated by WEDDink on {timestamp}</i>", self.styles['Footer']))
            
            # Page break
            story.append(Spacer(1, 1*inch))
            
            # Collection title
            collection_style = ParagraphStyle(
                'CollectionTitle',
                parent=self.styles['CustomTitle'],
                textColor=colors.HexColor(theme_colors['accent'])
            )
            story.append(Paragraph("Welcome Board Collection", collection_style))
            story.append(Spacer(1, 0.4*inch))
            
            # Image grid
            image_elements = self._create_image_grid(results)
            story.extend(image_elements)
            
            # Footer on each page
            footer = Paragraph("Generated by WEDDink - Your Event Mood Board Assistant", self.styles['Footer'])
            
            # Build PDF
            doc.build(story)
            
            # Count successful images
            total_images = 0
            for source, images in results.items():
                if source.endswith('_results'):
                    total_images += len(images)
            
            log(f"PDF generated successfully with {total_images} images")
            
            return {
                'success': True,
                'pdf_path': output_path,
                'total_images': total_images,
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
            }
            
        except Exception as e:
            log(f"PDF generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'pdf_path': None
            }

def generate_mood_board_pdf(event_type: str, budget_range: str, 
                          color_theme: str, results: Dict) -> Dict:
    """
    Generate a mood board PDF file.
    
    Args:
        event_type: Type of event
        budget_range: Budget range
        color_theme: Color theme
        results: Search results from backend
        
    Returns:
        Dict with PDF generation results
    """
    # Create output directory
    output_dir = "generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mood_board_{event_type}_{budget_range.replace('₹', '').replace('-', '_')}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = MoodBoardPDFGenerator()
    result = generator.generate_mood_board(event_type, budget_range, color_theme, results, output_path)
    
    return result

if __name__ == "__main__":
    # Test the PDF generator
    test_results = {
        'local_results': [
            {'image_url': 'downloaded_images/Welcome_board_decor_(3000-5000)/Wedding/provided_sample/provided_sample_11329436558610714_sample_10.jpg', 'title': 'Test Image', 'similarity': 0.85, 'price_category': '₹3000-₹5000'}
        ],
        'google_results': [],
        'bing_results': [],
        'pinterest_results': []
    }
    
    result = generate_mood_board_pdf('wedding', '₹3000-₹5000', 'bold', test_results)
    print(f"Test result: {result}")
