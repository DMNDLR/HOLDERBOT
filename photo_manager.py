#!/usr/bin/env python3
"""
📷 HASH-BASED PHOTO MANAGEMENT SYSTEM
=====================================
Robust system for handling photo storage, retrieval, and analysis based on 
holder hashes/IDs with proper error handling and fallback mechanisms.

Features:
- Hash-based photo identification and caching
- Multiple fallback URL patterns
- Local photo caching and management
- Photo validation and error recovery
- Batch photo downloading and processing
- Photo metadata tracking
"""

import os
import hashlib
import time
import requests
from typing import Dict, List, Optional, Tuple
import json
import logging
from PIL import Image
from pathlib import Path
import shutil
from urllib.parse import urlparse
from io import BytesIO

class PhotoManager:
    """Manages photo storage, retrieval, and caching with hash-based identification"""
    
    def __init__(self, cache_dir: str = "photo_cache", base_urls: List[str] = None):
        self.cache_dir = Path(cache_dir)
        self.setup_logging()
        self.setup_cache_directory()
        
        # Default photo URL patterns
        if base_urls is None:
            self.base_urls = [
                "https://devbackend.smartmap.sk/storage/pezinok/holders-photos",
                "https://backend.smartmap.sk/storage/pezinok/holders-photos",
                "https://smartmap.sk/storage/holders-photos"
            ]
        else:
            self.base_urls = base_urls
            
        # Photo format preferences
        self.photo_formats = ['.png', '.jpg', '.jpeg', '.webp']
        
        # Cache metadata
        self.cache_metadata_file = self.cache_dir / "cache_metadata.json"
        self.load_cache_metadata()
        
    def setup_logging(self):
        """Setup logging for photo operations"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("PhotoManager")
        
    def setup_cache_directory(self):
        """Create cache directory structure"""
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "photos").mkdir(exist_ok=True)
        (self.cache_dir / "thumbnails").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
        
    def load_cache_metadata(self):
        """Load cache metadata"""
        try:
            if self.cache_metadata_file.exists():
                with open(self.cache_metadata_file, 'r', encoding='utf-8') as f:
                    self.cache_metadata = json.load(f)
            else:
                self.cache_metadata = {}
        except Exception as e:
            self.logger.error(f"❌ Failed to load cache metadata: {e}")
            self.cache_metadata = {}
            
    def save_cache_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.cache_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Failed to save cache metadata: {e}")
            
    def generate_photo_hash(self, holder_id: str, photo_url: str = None) -> str:
        """Generate consistent hash for photo identification"""
        if photo_url:
            hash_input = f"{holder_id}_{photo_url}"
        else:
            hash_input = holder_id
        return hashlib.md5(hash_input.encode()).hexdigest()
        
    def get_photo_urls(self, holder_id: str) -> List[str]:
        """Generate all possible photo URLs for a holder ID"""
        urls = []
        
        for base_url in self.base_urls:
            for format_ext in self.photo_formats:
                url = f"{base_url}/{holder_id}{format_ext}"
                urls.append(url)
                
        return urls
        
    def download_photo(self, holder_id: str, force_refresh: bool = False) -> Optional[str]:
        """Download photo for holder ID with fallback mechanisms"""
        photo_hash = self.generate_photo_hash(holder_id)
        cached_path = self.cache_dir / "photos" / f"{photo_hash}.jpg"
        
        # Check if already cached and not forcing refresh
        if not force_refresh and cached_path.exists():
            if self.is_photo_valid(cached_path):
                self.logger.info(f"📷 Using cached photo for holder {holder_id}")
                return str(cached_path)
            else:
                # Remove invalid cached photo
                cached_path.unlink(missing_ok=True)
                
        # Try to download from various URLs
        urls = self.get_photo_urls(holder_id)
        
        for url in urls:
            try:
                self.logger.info(f"🔄 Attempting to download: {url}")
                
                response = requests.get(url, timeout=10, stream=True)
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                    self.logger.warning(f"⚠️ Invalid content type: {content_type}")
                    continue
                    
                # Download and save
                with open(cached_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                # Validate downloaded image
                if self.is_photo_valid(cached_path):
                    # Update cache metadata
                    self.cache_metadata[holder_id] = {
                        'photo_hash': photo_hash,
                        'source_url': url,
                        'download_timestamp': time.time(),
                        'file_size': cached_path.stat().st_size,
                        'local_path': str(cached_path)
                    }
                    self.save_cache_metadata()
                    
                    self.logger.info(f"✅ Downloaded photo for holder {holder_id}")
                    return str(cached_path)
                else:
                    # Remove invalid download
                    cached_path.unlink(missing_ok=True)
                    self.logger.warning(f"⚠️ Downloaded invalid image from {url}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"⚠️ Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"❌ Unexpected error downloading from {url}: {e}")
                continue
                
        self.logger.error(f"❌ Could not download photo for holder {holder_id}")
        return None
        
    def is_photo_valid(self, photo_path: Path) -> bool:
        """Validate if photo file is valid and usable"""
        try:
            if not photo_path.exists() or photo_path.stat().st_size < 1024:
                return False
                
            # Try to open with PIL
            with Image.open(photo_path) as img:
                # Basic validation
                if img.width < 50 or img.height < 50:
                    return False
                    
                # Try to load image data
                img.verify()
                
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Photo validation failed for {photo_path}: {e}")
            return False
            
    def get_photo_metadata(self, holder_id: str) -> Dict:
        """Get metadata for a photo"""
        return self.cache_metadata.get(holder_id, {})
        
    def create_thumbnail(self, photo_path: str, size: Tuple[int, int] = (256, 256)) -> Optional[str]:
        """Create thumbnail for photo"""
        try:
            photo_path = Path(photo_path)
            photo_hash = photo_path.stem
            thumbnail_path = self.cache_dir / "thumbnails" / f"{photo_hash}_thumb.jpg"
            
            if thumbnail_path.exists():
                return str(thumbnail_path)
                
            with Image.open(photo_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                img.save(thumbnail_path, 'JPEG', quality=85)
                
            self.logger.info(f"✅ Created thumbnail for {photo_path.name}")
            return str(thumbnail_path)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create thumbnail: {e}")
            return None
            
    def batch_download_photos(self, holder_ids: List[str], max_concurrent: int = 5) -> Dict[str, str]:
        """Download multiple photos in batch"""
        results = {}
        
        self.logger.info(f"📦 Batch downloading {len(holder_ids)} photos")
        
        for i, holder_id in enumerate(holder_ids):
            self.logger.info(f"📷 Downloading {i+1}/{len(holder_ids)}: {holder_id}")
            
            photo_path = self.download_photo(holder_id)
            results[holder_id] = photo_path
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
            
            if (i + 1) % 10 == 0:
                self.logger.info(f"📊 Progress: {i+1}/{len(holder_ids)} photos processed")
                
        success_count = sum(1 for path in results.values() if path)
        self.logger.info(f"✅ Batch download complete: {success_count}/{len(holder_ids)} successful")
        
        return results
        
    def clean_cache(self, days_old: int = 30) -> int:
        """Clean old cached photos"""
        cleaned_count = 0
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        try:
            for photo_file in (self.cache_dir / "photos").glob("*.jpg"):
                if photo_file.stat().st_mtime < cutoff_time:
                    photo_file.unlink(missing_ok=True)
                    cleaned_count += 1
                    
            # Clean thumbnails
            for thumb_file in (self.cache_dir / "thumbnails").glob("*_thumb.jpg"):
                if thumb_file.stat().st_mtime < cutoff_time:
                    thumb_file.unlink(missing_ok=True)
                    
            # Update metadata
            updated_metadata = {}
            for holder_id, metadata in self.cache_metadata.items():
                if metadata.get('download_timestamp', 0) >= cutoff_time:
                    updated_metadata[holder_id] = metadata
                    
            self.cache_metadata = updated_metadata
            self.save_cache_metadata()
            
            self.logger.info(f"🧹 Cleaned {cleaned_count} old cached photos")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"❌ Failed to clean cache: {e}")
            return 0
            
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            photos_dir = self.cache_dir / "photos"
            thumbnails_dir = self.cache_dir / "thumbnails"
            
            photo_count = len(list(photos_dir.glob("*.jpg")))
            thumbnail_count = len(list(thumbnails_dir.glob("*_thumb.jpg")))
            
            # Calculate total size
            total_size = 0
            for file_path in photos_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    
            for file_path in thumbnails_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    
            return {
                'photo_count': photo_count,
                'thumbnail_count': thumbnail_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'metadata_entries': len(self.cache_metadata),
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get cache stats: {e}")
            return {}
            
    def export_photo_urls(self, holder_ids: List[str]) -> Dict[str, List[str]]:
        """Export all possible photo URLs for given holder IDs"""
        export_data = {}
        
        for holder_id in holder_ids:
            export_data[holder_id] = self.get_photo_urls(holder_id)
            
        export_file = f"photo_urls_export_{int(time.time())}.json"
        
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"✅ Exported photo URLs to {export_file}")
            return export_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export photo URLs: {e}")
            return export_data

if __name__ == "__main__":
    # Example usage and testing
    pm = PhotoManager()
    
    # Test downloading a photo
    photo_path = pm.download_photo("12345")
    if photo_path:
        print(f"✅ Downloaded photo: {photo_path}")
        
        # Create thumbnail
        thumbnail_path = pm.create_thumbnail(photo_path)
        if thumbnail_path:
            print(f"✅ Created thumbnail: {thumbnail_path}")
            
    # Show cache stats
    stats = pm.get_cache_stats()
    print(f"📊 Cache stats: {stats}")
    
    # Test batch download
    test_ids = ["12345", "67890", "11111"]
    batch_results = pm.batch_download_photos(test_ids)
    print(f"📦 Batch results: {batch_results}")
