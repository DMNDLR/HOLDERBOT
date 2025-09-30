"""
Image Analysis Module for Traffic Sign Bot
Analyzes traffic sign photos to extract attributes
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from typing import Dict, List, Optional, Tuple
from loguru import logger
import json

from config.config import Config, TrafficSignAttributes


class TrafficSignAnalyzer:
    """Analyzes traffic sign images to extract attributes"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Traffic Sign Analyzer initialized")
        
        # Slovak traffic sign detection prompt
        self.slovak_prompt = """
Your task is to analyze an image of a traffic sign carrier (nosič dopravnej značky) and extract 3 key attributes by selecting from the given Slovak dropdown values. Do not translate the Slovak words — just select the correct Slovak label from the list based on what you see.

You must return exactly these three fields:

1. `Vlastník` – ownership category:
   - "mesto" (city)
   - "obec" (village/municipality)
   - "iný" (other)

2. `Materiál` – material of the carrier:
   - "kov" (metal)
   - "betón" (concrete)
   - "drevo" (wood)
   - "plast" (plastic)
   - "stavba, múr" (wall/building structure)
   - "iný" (other)

3. `Základný typ` – basic type of carrier (pick the most fitting from this extended Slovak list):
   - "stĺp značky samostatný" (single sign pole)
   - "stĺp značky dvojitý" (double sign pole)
   - "stĺp značky trojitý"
   - "stĺp značky štvoritý"
   - "stĺp verejného osvetlenia" (public lighting pole)
   - "stĺp elektrického vedenia" (electricity pole)
   - "stĺp telekomunikačného vedenia"
   - "stĺp svetelného signalizačného zariadenia"
   - "dopravné zariadenie" (traffic device)
   - "portálová konštrukcia" (portal structure)
   - "mostná konštrukcia" (bridge structure)
   - "zvodidlo, zábradlie" (guardrail, handrail)
   - "Zastávka MHD" (public transport stop)
   - "plot" (fence)
   - "budova" (building)
   - "brána, dvere" (gate, door)
   - "závora" (barrier)
   - "Stĺpik tabule označenia ulice"
   - "Stĺpik smerových tabúľ ulíc alebo objektov"
   - "Vodiace dosky Klemmfix"
   - "Stojan pre dočasné dopravné značenie"
   - "Smerovacie zariadenie Z4"
   - "iný" (other)

❗Important:
- Output the original Slovak label, not its English meaning.
- Use visual clues like material type, structural type, number of poles, lighting elements, surroundings (e.g. fence, building), etc.
- Do not fill in the `ulica` (street name) field – it is determined from map data.

Return a dictionary like this:

{
  "Vlastník": "mesto",
  "Materiál": "kov",
  "Základný typ": "stĺp značky samostatný"
}
"""
        
        # Color ranges for different materials (in HSV)
        self.color_ranges = {
            'aluminum': {'lower': (0, 0, 180), 'upper': (180, 30, 255)},
            'steel': {'lower': (0, 0, 80), 'upper': (180, 50, 150)},
            'reflective': {'lower': (0, 0, 200), 'upper': (180, 20, 255)},
            'rust': {'lower': (0, 100, 50), 'upper': (25, 255, 200)}
        }
    
    def analyze_image(self, image_path: str) -> Dict[str, str]:
        """
        Main method to analyze a traffic sign image
        Returns a dictionary of detected attributes
        """
        try:
            self.logger.info(f"Analyzing image: {image_path}")
            
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return {}
            
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Could not load image: {image_path}")
                return {}
            
            # Analyze different aspects
            material = self._detect_material(image)
            condition = self._assess_condition(image)
            size_estimate = self._estimate_size(image)
            stand_type = self._detect_stand_type(image)
            
            # Compile results
            results = {
                'material': material,
                'condition': condition,
                'size': size_estimate,
                'stand_type': stand_type,
                'installation_method': 'bolted',  # Default assumption
            }
            
            # Log results
            self.logger.info(f"Analysis results: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing image: {str(e)}")
            return {}
    
    def _detect_material(self, image: np.ndarray) -> str:
        """Detect traffic sign material based on visual characteristics"""
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calculate brightness and reflectivity
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            # Check for reflective properties (high brightness, low saturation)
            if brightness > 180:
                return 'reflective_sheeting'
            
            # Check for metallic properties
            if brightness > 120 and brightness < 180:
                # Check for rust or corrosion
                rust_mask = cv2.inRange(hsv, 
                                      np.array(self.color_ranges['rust']['lower']), 
                                      np.array(self.color_ranges['rust']['upper']))
                rust_percentage = (np.sum(rust_mask > 0) / rust_mask.size) * 100
                
                if rust_percentage > 5:
                    return 'steel'  # Steel with rust
                else:
                    return 'aluminum'  # Clean aluminum
            
            # Lower brightness might indicate plastic or composite
            elif brightness < 120:
                return 'plastic'
            
            return 'aluminum'  # Default
            
        except Exception as e:
            self.logger.error(f"Error detecting material: {str(e)}")
            return 'aluminum'  # Default fallback
    
    def _assess_condition(self, image: np.ndarray) -> str:
        """Assess the condition of the traffic sign"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate image quality metrics
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()  # Sharpness
            brightness = np.mean(gray)
            
            # Detect edges to find damage or wear
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Check for damage indicators
            # High edge density might indicate damage or wear
            if edge_density > 0.1:
                return 'damaged'
            elif edge_density > 0.05:
                return 'fair'
            
            # Check brightness for fading
            if brightness < 80:
                return 'poor'
            elif brightness < 120:
                return 'fair'
            
            # Check sharpness
            if laplacian_var < 50:
                return 'poor'
            elif laplacian_var < 100:
                return 'good'
            
            return 'excellent'
            
        except Exception as e:
            self.logger.error(f"Error assessing condition: {str(e)}")
            return 'good'  # Default
    
    def _estimate_size(self, image: np.ndarray) -> str:
        """Estimate the size category of the traffic sign"""
        try:
            # This is a simplified approach - in practice, you'd need reference objects
            height, width = image.shape[:2]
            aspect_ratio = width / height
            
            # Based on common traffic sign proportions
            if abs(aspect_ratio - 1.0) < 0.2:  # Nearly square
                if width > 1000:  # Large image suggests large sign
                    return '900x900mm'
                elif width > 700:
                    return '750x750mm'
                else:
                    return '600x600mm'
            
            elif aspect_ratio > 1.5:  # Rectangular
                return '900x600mm'
            elif aspect_ratio < 0.7:  # Tall rectangle
                return '600x900mm'
            
            return '600x600mm'  # Default
            
        except Exception as e:
            self.logger.error(f"Error estimating size: {str(e)}")
            return '600x600mm'
    
    def _detect_stand_type(self, image: np.ndarray) -> str:
        """Detect the type of stand/post"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Find vertical lines (posts)
            edges = cv2.Canny(gray, 50, 150)
            
            # Use HoughLinesP to detect lines
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=100, maxLineGap=10)
            
            if lines is not None:
                vertical_lines = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    
                    # Check if line is vertical (±15 degrees)
                    if abs(angle - 90) < 15 or abs(angle + 90) < 15:
                        vertical_lines.append(line)
                
                # Analyze the characteristics of vertical lines
                if len(vertical_lines) > 2:
                    return 'u_channel_post'  # Multiple vertical edges
                elif len(vertical_lines) == 2:
                    return 'square_tube_post'  # Two main edges
                else:
                    return 'round_post'  # Single or curved edge
            
            return 'metal_post'  # Default
            
        except Exception as e:
            self.logger.error(f"Error detecting stand type: {str(e)}")
            return 'metal_post'
    
    def enhance_image(self, image_path: str, output_path: str = None) -> str:
        """Enhance image quality for better analysis"""
        try:
            # Open image with PIL for enhancement
            pil_image = Image.open(image_path)
            
            # Enhance contrast
            contrast_enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = contrast_enhancer.enhance(1.2)
            
            # Enhance brightness
            brightness_enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = brightness_enhancer.enhance(1.1)
            
            # Enhance sharpness
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.1)
            
            # Save enhanced image
            if not output_path:
                name, ext = os.path.splitext(image_path)
                output_path = f"{name}_enhanced{ext}"
            
            enhanced.save(output_path)
            self.logger.info(f"Enhanced image saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error enhancing image: {str(e)}")
            return image_path  # Return original if enhancement fails
    
    def batch_analyze(self, image_folder: str) -> Dict[str, Dict[str, str]]:
        """Analyze multiple images in a folder"""
        try:
            results = {}
            
            if not os.path.exists(image_folder):
                self.logger.error(f"Image folder not found: {image_folder}")
                return results
            
            # Get all image files
            supported_formats = tuple(f".{fmt.lower()}" for fmt in Config.SUPPORTED_FORMATS)
            
            image_files = [
                f for f in os.listdir(image_folder) 
                if f.lower().endswith(supported_formats)
            ]
            
            self.logger.info(f"Found {len(image_files)} images to analyze")
            
            for image_file in image_files:
                image_path = os.path.join(image_folder, image_file)
                self.logger.info(f"Analyzing: {image_file}")
                
                analysis_result = self.analyze_image(image_path)
                results[image_file] = analysis_result
            
            # Save results to JSON
            results_file = os.path.join(image_folder, "analysis_results.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Batch analysis completed. Results saved to: {results_file}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch analysis: {str(e)}")
            return {}
    
    def validate_image(self, image_path: str) -> bool:
        """Validate if image is suitable for analysis"""
        try:
            if not os.path.exists(image_path):
                return False
            
            # Check file size
            file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            if file_size_mb > Config.MAX_IMAGE_SIZE_MB:
                self.logger.warning(f"Image too large: {file_size_mb:.1f}MB")
                return False
            
            # Check if file can be loaded
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            # Check minimum dimensions
            height, width = image.shape[:2]
            if width < 100 or height < 100:
                self.logger.warning(f"Image too small: {width}x{height}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating image: {str(e)}")
            return False
    
    def analyze_slovak_traffic_sign(self, image_path: str) -> Dict[str, str]:
        """Analyze traffic sign using Slovak detection criteria"""
        try:
            self.logger.info(f"Analyzing Slovak traffic sign: {image_path}")
            
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return {}
            
            # Load image for analysis
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Could not load image: {image_path}")
                return {}
            
            # Analyze using computer vision methods
            detected_material = self._detect_material_slovak(image)
            detected_type = self._detect_type_slovak(image)
            detected_owner = self._detect_owner_slovak(image)
            
            results = {
                "Vlastník": detected_owner,
                "Materiál": detected_material,
                "Základný typ": detected_type
            }
            
            self.logger.info(f"Slovak analysis results: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing Slovak traffic sign: {str(e)}")
            return {
                "Vlastník": "mesto",
                "Materiál": "kov",
                "Základný typ": "stĺp značky samostatný"
            }
    
    def _detect_material_slovak(self, image: np.ndarray) -> str:
        """Detect material and return Slovak term"""
        try:
            # Use existing material detection logic
            english_material = self._detect_material(image)
            
            # Map English terms to Slovak terms
            material_mapping = {
                'aluminum': 'kov',
                'steel': 'kov',
                'plastic': 'plast',
                'reflective_sheeting': 'kov',  # Usually metal with reflective coating
                'concrete': 'betón',
                'wood': 'drevo'
            }
            
            return material_mapping.get(english_material, 'kov')  # Default to metal
            
        except Exception as e:
            self.logger.error(f"Error detecting Slovak material: {str(e)}")
            return 'kov'
    
    def _detect_type_slovak(self, image: np.ndarray) -> str:
        """Detect type and return Slovak term"""
        try:
            # Analyze image characteristics to determine type
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Look for lighting elements (bright spots)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            bright_pixels = np.sum(thresh == 255) / thresh.size
            
            # Look for multiple signs (horizontal elements)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
            
            horizontal_lines = 0
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    if abs(angle) < 15:  # Nearly horizontal
                        horizontal_lines += 1
            
            # Detect lighting poles by bright spots
            if bright_pixels > 0.1:
                return 'stĺp verejného osvetlenia'
            
            # Detect multiple signs
            elif horizontal_lines > 3:
                return 'stĺp značky dvojitý'
            
            # Default to single sign pole
            else:
                return 'stĺp značky samostatný'
                
        except Exception as e:
            self.logger.error(f"Error detecting Slovak type: {str(e)}")
            return 'stĺp značky samostatný'
    
    def _detect_owner_slovak(self, image: np.ndarray) -> str:
        """Detect ownership category - defaults to city (mesto)"""
        try:
            # For now, default to "mesto" as most signs are city-owned
            # This could be enhanced with location-based detection
            # or analysis of sign design/branding
            return 'mesto'
            
        except Exception as e:
            self.logger.error(f"Error detecting Slovak owner: {str(e)}")
            return 'mesto'
    
    def get_slovak_prompt(self) -> str:
        """Return the Slovak traffic sign detection prompt"""
        return self.slovak_prompt
    
    def get_analysis_confidence(self, results: Dict[str, str]) -> Dict[str, float]:
        """Return confidence scores for analysis results"""
        # This is a simplified confidence scoring
        # In practice, you'd use machine learning models
        
        confidence = {}
        
        # Material confidence based on typical detection accuracy
        material_confidence = {
            'aluminum': 0.8,
            'steel': 0.7,
            'plastic': 0.6,
            'composite': 0.5,
            'reflective_sheeting': 0.9
        }
        
        confidence['material'] = material_confidence.get(results.get('material', ''), 0.5)
        confidence['condition'] = 0.7  # Moderate confidence for condition assessment
        confidence['size'] = 0.6       # Lower confidence without reference objects
        confidence['stand_type'] = 0.6 # Moderate confidence for stand detection
        
        return confidence
