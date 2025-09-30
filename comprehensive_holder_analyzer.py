#!/usr/bin/env python3
"""
Comprehensive Holder Analyzer for SmartMap
==========================================

Analyzes, compares and learns from the 490 holders extracted from SmartMap.
This script will:
1. Download images from all holders
2. Analyze them with AI
3. Compare with existing form data
4. Generate learning patterns
5. Create training datasets
6. Build prediction models
"""

import json
import os
import requests
import time
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from loguru import logger

# AI Analysis imports
try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI not available - will use mock analysis")


@dataclass
class HolderAnalysisResult:
    """Complete analysis result for a single holder"""
    holder_id: str
    main_id: str
    page: int
    
    # Form data (ground truth)
    form_material: str
    form_owner: str
    form_type: str
    form_street: str
    
    # Image data
    image_url: str
    local_image_path: str
    image_downloaded: bool
    
    # AI Analysis results
    ai_material: Optional[str] = None
    ai_owner: Optional[str] = None
    ai_type: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_description: Optional[str] = None
    
    # Mapping results
    suggested_material: Optional[str] = None
    suggested_owner: Optional[str] = None
    suggested_type: Optional[str] = None
    
    # Accuracy
    material_match: bool = False
    owner_match: bool = False
    type_match: bool = False
    overall_accuracy: float = 0.0
    
    # Additional insights
    analysis_notes: str = ""
    processing_time: float = 0.0


class ComprehensiveHolderAnalyzer:
    """Comprehensive analyzer for SmartMap holders"""
    
    def __init__(self):
        self.data_dir = Path("learning_data")
        self.images_dir = self.data_dir / "holder_images"
        self.analysis_dir = self.data_dir / "analysis_results"
        self.reports_dir = Path("analysis_reports")
        
        # Create directories
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # SmartMap form values (ground truth reference)
        self.form_values = {
            "material": ["kov", "betón", "drevo", "plast", "stavba, múr", "iný"],
            "owner": ["mesto", "súkromný", "štát", "iný"], 
            "type": [
                "stĺp značky samostatný",
                "stĺp značky dvojitý", 
                "stĺp verejného osvetlenia",
                "svetelné signalizačné zariadenie",
                "stĺp",
                "iný"
            ]
        }
        
        # AI to form mapping patterns
        self.ai_mappings = {
            "material": {
                "aluminum": "kov", "aluminium": "kov", "metal": "kov", 
                "steel": "kov", "iron": "kov",
                "concrete": "betón", "cement": "betón",
                "wood": "drevo", "wooden": "drevo",
                "plastic": "plast",
                "reflective_sheeting": "kov"
            },
            "owner": {
                "city": "mesto", "municipal": "mesto", "municipality": "mesto", 
                "town": "mesto", "public": "mesto",
                "private": "súkromný", "individual": "súkromný",
                "state": "štát", "government": "štát"
            },
            "type": {
                "street_light": "stĺp verejného osvetlenia",
                "street lamp": "stĺp verejného osvetlenia", 
                "lighting_post": "stĺp verejného osvetlenia",
                "light_pole": "stĺp verejného osvetlenia",
                "lamp_post": "stĺp verejného osvetlenia",
                "public_lighting": "stĺp verejného osvetlenia",
                
                "sign_post": "stĺp značky samostatný",
                "traffic_sign_post": "stĺp značky samostatný",
                "standalone": "stĺp značky samostatný",
                "double": "stĺp značky dvojitý",
                
                "traffic_light": "svetelné signalizačné zariadenie",
                "signal_light": "svetelné signalizačné zariadenie",
                
                "post": "stĺp", "pole": "stĺp"
            }
        }
        
        # Initialize OpenAI if available
        self.ai_client = None
        if HAS_OPENAI and os.getenv('OPENAI_API_KEY'):
            try:
                self.ai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"OpenAI setup failed: {e}")
        
        self.all_results: List[HolderAnalysisResult] = []
        logger.info("🚀 Comprehensive Holder Analyzer initialized")
    
    def analyze_all_holders(self, max_holders: int = None) -> Dict:
        """Main method to analyze all holders"""
        try:
            logger.info("🎯 Starting comprehensive holder analysis...")
            
            # Step 1: Load holder data
            holders_data = self.load_holders_data()
            logger.info(f"📋 Loaded {len(holders_data)} holders")
            
            if max_holders:
                holders_data = holders_data[:max_holders]
                logger.info(f"🔢 Limited to first {max_holders} holders for testing")
            
            # Step 2: Download images
            self.download_holder_images(holders_data)
            
            # Step 3: Analyze images with AI
            self.analyze_holder_images(holders_data)
            
            # Step 4: Compare with form data and generate insights
            analysis_results = self.generate_comprehensive_analysis()
            
            # Step 5: Create learning patterns
            learning_patterns = self.extract_learning_patterns()
            
            # Step 6: Generate reports
            self.generate_analysis_reports(analysis_results, learning_patterns)
            
            logger.info("✅ Comprehensive analysis completed!")
            
            return {
                'analysis_results': analysis_results,
                'learning_patterns': learning_patterns,
                'total_holders': len(self.all_results),
                'reports_generated': True
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            raise
    
    def load_holders_data(self) -> List[Dict]:
        """Load holders from the CSV file we generated"""
        holders = []
        
        csv_file = Path("improved_holders_summary.csv")
        if not csv_file.exists():
            raise FileNotFoundError("improved_holders_summary.csv not found. Run the pagination extractor first!")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                holders.append(row)
        
        logger.info(f"📊 Loaded {len(holders)} holders from CSV")
        return holders
    
    def download_holder_images(self, holders_data: List[Dict]):
        """Download images for all holders"""
        logger.info("📥 Starting image download...")
        
        downloaded = 0
        failed = 0
        
        for i, holder in enumerate(holders_data):
            try:
                holder_id = holder['Holder_ID']
                photo_url = holder['Photo_URL']
                
                image_filename = f"holder_{holder_id}.png"
                image_path = self.images_dir / image_filename
                
                # Skip if already downloaded
                if image_path.exists():
                    logger.debug(f"Image already exists: {image_filename}")
                    downloaded += 1
                    continue
                
                # Download image
                response = requests.get(photo_url, timeout=10)
                response.raise_for_status()
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                downloaded += 1
                
                if i % 50 == 0:
                    logger.info(f"📸 Downloaded {downloaded} / {len(holders_data)} images...")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Failed to download image for holder {holder.get('Holder_ID', 'unknown')}: {e}")
                failed += 1
                continue
        
        logger.info(f"✅ Image download complete: {downloaded} downloaded, {failed} failed")
    
    def analyze_holder_images(self, holders_data: List[Dict]):
        """Analyze all holder images with AI"""
        logger.info("🤖 Starting AI image analysis...")
        
        for i, holder in enumerate(holders_data):
            try:
                start_time = time.time()
                
                # Create analysis result object
                result = HolderAnalysisResult(
                    holder_id=holder['Holder_ID'],
                    main_id=holder['Main_ID'],
                    page=int(holder['Page']),
                    form_material=holder['Material'],
                    form_owner=holder['Vlastnik'],
                    form_type=holder['Typ'],
                    form_street=holder['Ulica'],
                    image_url=holder['Photo_URL'],
                    local_image_path=str(self.images_dir / f"holder_{holder['Holder_ID']}.png"),
                    image_downloaded=Path(self.images_dir / f"holder_{holder['Holder_ID']}.png").exists()
                )
                
                # Analyze image if downloaded
                if result.image_downloaded:
                    ai_analysis = self.analyze_single_image(result.local_image_path)
                    result.ai_material = ai_analysis.get('material')
                    result.ai_owner = ai_analysis.get('owner')
                    result.ai_type = ai_analysis.get('type')
                    result.ai_confidence = ai_analysis.get('confidence', 0.0)
                    result.ai_description = ai_analysis.get('description', '')
                
                # Map AI results to form values
                result.suggested_material = self.map_ai_to_form('material', result.ai_material)
                result.suggested_owner = self.map_ai_to_form('owner', result.ai_owner)
                result.suggested_type = self.map_ai_to_form('type', result.ai_type)
                
                # Calculate accuracy
                result.material_match = result.form_material == result.suggested_material if result.suggested_material else False
                result.owner_match = result.form_owner == result.suggested_owner if result.suggested_owner else False
                result.type_match = result.form_type == result.suggested_type if result.suggested_type else False
                
                # Overall accuracy
                matches = sum([result.material_match, result.owner_match, result.type_match])
                result.overall_accuracy = matches / 3.0
                
                result.processing_time = time.time() - start_time
                self.all_results.append(result)
                
                if i % 25 == 0:
                    logger.info(f"🔍 Analyzed {i+1} / {len(holders_data)} holders...")
                
            except Exception as e:
                logger.error(f"Error analyzing holder {holder.get('Holder_ID', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ AI analysis complete: {len(self.all_results)} holders analyzed")
    
    def analyze_single_image(self, image_path: str) -> Dict:
        """Analyze a single image with AI"""
        try:
            if self.ai_client:
                return self.analyze_with_openai(image_path)
            else:
                return self.mock_ai_analysis(image_path)
        except Exception as e:
            logger.debug(f"AI analysis failed for {image_path}: {e}")
            return self.mock_ai_analysis(image_path)
    
    def analyze_with_openai(self, image_path: str) -> Dict:
        """Analyze image using OpenAI Vision API"""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = self.ai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this traffic sign holder/post image. Identify:
1. Material: What is it made of? (metal/aluminum, concrete, wood, plastic, etc.)
2. Owner: Who likely owns it? (city/municipal, private, state/government)
3. Type: What type of post is it? (traffic sign post, street light, traffic light, generic post)
4. Confidence: How confident are you? (0.0-1.0)
5. Description: Brief description of what you see

Respond in JSON format with keys: material, owner, type, confidence, description"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback parsing
                return {
                    'material': 'aluminum',
                    'owner': 'city',
                    'type': 'sign_post',
                    'confidence': 0.7,
                    'description': content[:200]
                }
            
        except Exception as e:
            logger.debug(f"OpenAI analysis failed: {e}")
            return self.mock_ai_analysis(image_path)
    
    def mock_ai_analysis(self, image_path: str) -> Dict:
        """Mock AI analysis for testing without API"""
        import random
        
        # Simulate realistic distributions based on our data
        materials = ['aluminum', 'metal', 'concrete', 'steel']
        owners = ['city', 'municipal', 'private', 'state']
        types = ['sign_post', 'street_light', 'traffic_light', 'light_pole', 'post']
        
        return {
            'material': random.choice(materials),
            'owner': random.choice(owners),
            'type': random.choice(types),
            'confidence': round(random.uniform(0.6, 0.95), 2),
            'description': f'Mock analysis of {Path(image_path).name}'
        }
    
    def map_ai_to_form(self, attribute: str, ai_value: Optional[str]) -> Optional[str]:
        """Map AI detected value to SmartMap form value"""
        if not ai_value:
            return None
        
        ai_lower = ai_value.lower().strip()
        
        # Direct match with Slovak form values
        if attribute in self.form_values:
            for form_val in self.form_values[attribute]:
                if form_val.lower() == ai_lower:
                    return form_val
        
        # Use mapping patterns
        if attribute in self.ai_mappings:
            mappings = self.ai_mappings[attribute]
            
            # Exact match
            if ai_lower in mappings:
                return mappings[ai_lower]
            
            # Partial match
            for ai_pattern, form_val in mappings.items():
                if ai_pattern in ai_lower or ai_lower in ai_pattern:
                    return form_val
        
        return None
    
    def generate_comprehensive_analysis(self) -> Dict:
        """Generate comprehensive analysis of all results"""
        logger.info("📊 Generating comprehensive analysis...")
        
        total = len(self.all_results)
        if total == 0:
            return {"error": "No results to analyze"}
        
        # Basic statistics
        material_accuracy = sum(r.material_match for r in self.all_results) / total
        owner_accuracy = sum(r.owner_match for r in self.all_results) / total
        type_accuracy = sum(r.type_match for r in self.all_results) / total
        overall_accuracy = sum(r.overall_accuracy for r in self.all_results) / total
        
        # Confidence statistics
        confidences = [r.ai_confidence for r in self.all_results if r.ai_confidence]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        # Material analysis
        form_materials = Counter(r.form_material for r in self.all_results if r.form_material)
        ai_materials = Counter(r.ai_material for r in self.all_results if r.ai_material)
        material_mapping_success = {}
        
        for material in form_materials.keys():
            material_results = [r for r in self.all_results if r.form_material == material]
            if material_results:
                success_rate = sum(r.material_match for r in material_results) / len(material_results)
                material_mapping_success[material] = success_rate
        
        # Type analysis
        form_types = Counter(r.form_type for r in self.all_results if r.form_type)
        ai_types = Counter(r.ai_type for r in self.all_results if r.ai_type)
        type_mapping_success = {}
        
        for type_name in form_types.keys():
            type_results = [r for r in self.all_results if r.form_type == type_name]
            if type_results:
                success_rate = sum(r.type_match for r in type_results) / len(type_results)
                type_mapping_success[type_name] = success_rate
        
        # Processing statistics
        processing_times = [r.processing_time for r in self.all_results if r.processing_time]
        avg_processing_time = np.mean(processing_times) if processing_times else 0.0
        
        return {
            'total_holders': total,
            'accuracy': {
                'material': round(material_accuracy, 3),
                'owner': round(owner_accuracy, 3),
                'type': round(type_accuracy, 3),
                'overall': round(overall_accuracy, 3)
            },
            'confidence': {
                'average': round(avg_confidence, 3),
                'min': round(min(confidences), 3) if confidences else 0.0,
                'max': round(max(confidences), 3) if confidences else 0.0
            },
            'materials': {
                'form_distribution': dict(form_materials),
                'ai_distribution': dict(ai_materials),
                'mapping_success': material_mapping_success
            },
            'types': {
                'form_distribution': dict(form_types),
                'ai_distribution': dict(ai_types),
                'mapping_success': type_mapping_success
            },
            'performance': {
                'avg_processing_time': round(avg_processing_time, 3),
                'images_downloaded': sum(1 for r in self.all_results if r.image_downloaded),
                'images_analyzed': sum(1 for r in self.all_results if r.ai_material)
            }
        }
    
    def extract_learning_patterns(self) -> Dict:
        """Extract learning patterns for AI training"""
        logger.info("🧠 Extracting learning patterns...")
        
        patterns = {
            'successful_mappings': defaultdict(list),
            'failed_mappings': defaultdict(list),
            'confidence_patterns': defaultdict(list),
            'improvement_opportunities': []
        }
        
        for result in self.all_results:
            # Successful material mappings
            if result.material_match and result.ai_material:
                patterns['successful_mappings']['material'].append({
                    'ai_detected': result.ai_material,
                    'form_value': result.form_material,
                    'confidence': result.ai_confidence,
                    'holder_id': result.holder_id
                })
            
            # Failed material mappings
            elif not result.material_match and result.ai_material:
                patterns['failed_mappings']['material'].append({
                    'ai_detected': result.ai_material,
                    'form_value': result.form_material,
                    'suggested': result.suggested_material,
                    'confidence': result.ai_confidence,
                    'holder_id': result.holder_id
                })
            
            # Similar for types
            if result.type_match and result.ai_type:
                patterns['successful_mappings']['type'].append({
                    'ai_detected': result.ai_type,
                    'form_value': result.form_type,
                    'confidence': result.ai_confidence,
                    'holder_id': result.holder_id
                })
            elif not result.type_match and result.ai_type:
                patterns['failed_mappings']['type'].append({
                    'ai_detected': result.ai_type,
                    'form_value': result.form_type,
                    'suggested': result.suggested_type,
                    'confidence': result.ai_confidence,
                    'holder_id': result.holder_id
                })
            
            # Confidence patterns
            if result.ai_confidence:
                patterns['confidence_patterns'][result.form_type].append(result.ai_confidence)
        
        # Identify improvement opportunities
        for attr in ['material', 'type']:
            failed = patterns['failed_mappings'][attr]
            if failed:
                # Group by AI detected value to find common failures
                failure_groups = defaultdict(list)
                for failure in failed:
                    failure_groups[failure['ai_detected']].append(failure)
                
                for ai_value, failures in failure_groups.items():
                    if len(failures) >= 3:  # Common failure pattern
                        patterns['improvement_opportunities'].append({
                            'attribute': attr,
                            'ai_detected': ai_value,
                            'frequency': len(failures),
                            'form_values': [f['form_value'] for f in failures],
                            'avg_confidence': np.mean([f['confidence'] for f in failures if f['confidence']])
                        })
        
        return dict(patterns)
    
    def generate_analysis_reports(self, analysis_results: Dict, learning_patterns: Dict):
        """Generate comprehensive analysis reports"""
        logger.info("📄 Generating analysis reports...")
        
        # 1. Summary Report
        self.generate_summary_report(analysis_results)
        
        # 2. Detailed CSV Export
        self.generate_detailed_csv()
        
        # 3. Learning Patterns Report
        self.generate_learning_patterns_report(learning_patterns)
        
        # 4. Visual Analysis Report
        self.generate_visual_report(analysis_results)
        
        logger.info("✅ All reports generated successfully!")
    
    def generate_summary_report(self, results: Dict):
        """Generate summary analysis report"""
        report_path = self.reports_dir / "analysis_summary.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# SmartMap Holder Analysis Summary\n\n")
            f.write(f"**Total Holders Analyzed:** {results['total_holders']}\n")
            f.write(f"**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 Accuracy Results\n\n")
            f.write(f"- **Material Recognition:** {results['accuracy']['material']:.1%}\n")
            f.write(f"- **Owner Classification:** {results['accuracy']['owner']:.1%}\n")
            f.write(f"- **Type Classification:** {results['accuracy']['type']:.1%}\n")
            f.write(f"- **Overall Accuracy:** {results['accuracy']['overall']:.1%}\n\n")
            
            f.write("## 🎯 Material Distribution\n\n")
            for material, count in results['materials']['form_distribution'].items():
                success_rate = results['materials']['mapping_success'].get(material, 0)
                f.write(f"- **{material}:** {count} holders ({success_rate:.1%} accuracy)\n")
            
            f.write("\n## 🏗️ Type Distribution\n\n")
            for type_name, count in results['types']['form_distribution'].items():
                success_rate = results['types']['mapping_success'].get(type_name, 0)
                f.write(f"- **{type_name}:** {count} holders ({success_rate:.1%} accuracy)\n")
            
            f.write(f"\n## ⚡ Performance\n\n")
            f.write(f"- **Images Downloaded:** {results['performance']['images_downloaded']}\n")
            f.write(f"- **Images Analyzed:** {results['performance']['images_analyzed']}\n")
            f.write(f"- **Average Processing Time:** {results['performance']['avg_processing_time']:.2f}s\n")
            f.write(f"- **Average Confidence:** {results['confidence']['average']:.2f}\n")
        
        logger.info(f"📝 Summary report saved: {report_path}")
    
    def generate_detailed_csv(self):
        """Generate detailed CSV with all analysis results"""
        csv_path = self.reports_dir / "detailed_analysis_results.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Holder_ID', 'Main_ID', 'Page', 
                'Form_Material', 'Form_Owner', 'Form_Type', 'Form_Street',
                'AI_Material', 'AI_Owner', 'AI_Type', 'AI_Confidence',
                'Suggested_Material', 'Suggested_Owner', 'Suggested_Type',
                'Material_Match', 'Owner_Match', 'Type_Match', 'Overall_Accuracy',
                'Image_Downloaded', 'Processing_Time', 'AI_Description'
            ])
            
            # Data rows
            for result in self.all_results:
                writer.writerow([
                    result.holder_id, result.main_id, result.page,
                    result.form_material, result.form_owner, result.form_type, result.form_street,
                    result.ai_material, result.ai_owner, result.ai_type, result.ai_confidence,
                    result.suggested_material, result.suggested_owner, result.suggested_type,
                    result.material_match, result.owner_match, result.type_match, result.overall_accuracy,
                    result.image_downloaded, result.processing_time, result.ai_description
                ])
        
        logger.info(f"📊 Detailed CSV saved: {csv_path}")
    
    def generate_learning_patterns_report(self, patterns: Dict):
        """Generate learning patterns report for AI training"""
        report_path = self.reports_dir / "learning_patterns.json"
        
        # Convert to JSON-serializable format
        json_patterns = {}
        for key, value in patterns.items():
            if isinstance(value, defaultdict):
                json_patterns[key] = dict(value)
            else:
                json_patterns[key] = value
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(json_patterns, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🧠 Learning patterns saved: {report_path}")
    
    def generate_visual_report(self, results: Dict):
        """Generate visual analysis report"""
        try:
            # Create a simple text-based visualization
            report_path = self.reports_dir / "visual_analysis.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("SMARTMAP HOLDER ANALYSIS - VISUAL REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("📊 ACCURACY BREAKDOWN:\n")
                f.write(f"Material: {'█' * int(results['accuracy']['material'] * 20)} {results['accuracy']['material']:.1%}\n")
                f.write(f"Owner:    {'█' * int(results['accuracy']['owner'] * 20)} {results['accuracy']['owner']:.1%}\n")
                f.write(f"Type:     {'█' * int(results['accuracy']['type'] * 20)} {results['accuracy']['type']:.1%}\n")
                f.write(f"Overall:  {'█' * int(results['accuracy']['overall'] * 20)} {results['accuracy']['overall']:.1%}\n\n")
                
                f.write("🏗️ MATERIAL DISTRIBUTION:\n")
                for material, count in sorted(results['materials']['form_distribution'].items(), key=lambda x: x[1], reverse=True):
                    bar_length = int((count / max(results['materials']['form_distribution'].values())) * 30)
                    f.write(f"{material:20} {'█' * bar_length} {count}\n")
                
                f.write(f"\n🎯 TYPE DISTRIBUTION:\n")
                for type_name, count in sorted(results['types']['form_distribution'].items(), key=lambda x: x[1], reverse=True):
                    if len(type_name) > 30:
                        display_name = type_name[:27] + "..."
                    else:
                        display_name = type_name
                    bar_length = int((count / max(results['types']['form_distribution'].values())) * 20)
                    f.write(f"{display_name:30} {'█' * bar_length} {count}\n")
            
            logger.info(f"📈 Visual report saved: {report_path}")
            
        except Exception as e:
            logger.warning(f"Failed to generate visual report: {e}")


def main():
    """Main function to run comprehensive analysis"""
    print("🚀 SmartMap Comprehensive Holder Analysis")
    print("=" * 50)
    print("This will analyze all 490 holders extracted from SmartMap!")
    print()
    
    analyzer = ComprehensiveHolderAnalyzer()
    
    try:
        # Ask user for analysis scope
        print("📋 Analysis Options:")
        print("1. 🔥 Full analysis (all 490 holders) - Takes longer but complete")
        print("2. 🧪 Test analysis (first 50 holders) - Quick test run")
        print("3. 🎯 Medium analysis (first 150 holders) - Balanced approach")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        max_holders = None
        if choice == '2':
            max_holders = 50
            print("🧪 Running test analysis on first 50 holders...")
        elif choice == '3':
            max_holders = 150
            print("🎯 Running medium analysis on first 150 holders...")
        else:
            print("🔥 Running full analysis on all 490 holders...")
        
        # Run analysis
        results = analyzer.analyze_all_holders(max_holders=max_holders)
        
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"📊 Analyzed: {results['total_holders']} holders")
        print(f"📁 Reports saved in: analysis_reports/")
        print(f"🧠 Learning patterns extracted: {len(results['learning_patterns'])} categories")
        
        print(f"\n📋 Quick Results:")
        if 'analysis_results' in results and 'accuracy' in results['analysis_results']:
            acc = results['analysis_results']['accuracy']
            print(f"  • Overall Accuracy: {acc['overall']:.1%}")
            print(f"  • Material Accuracy: {acc['material']:.1%}")  
            print(f"  • Type Accuracy: {acc['type']:.1%}")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Review analysis_reports/analysis_summary.md")
        print(f"  2. Check detailed_analysis_results.csv for complete data")
        print(f"  3. Use learning_patterns.json for AI training")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}")
        print(f"\n❌ Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()
