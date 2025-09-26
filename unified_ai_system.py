#!/usr/bin/env python3
"""
🧠 UNIFIED AI LEARNING SYSTEM
=============================
The MOST EFFECTIVE way to train Slovak traffic AI by combining:
- Your existing manual rectangles
- YOLO bootstrap predictions
- Progressive learning and improvement
- All data sources unified into one smart system

This system learns from EVERYTHING you have!
"""

import json
import numpy as np
import cv2
from pathlib import Path
import time
from typing import Dict, List, Optional
import os

class UnifiedAISystem:
    def __init__(self):
        """Initialize the unified learning system"""
        self.manual_data = []      # Your hand-drawn rectangles
        self.yolo_data = []        # YOLO bootstrap predictions  
        self.corrected_data = []   # YOLO predictions you've corrected
        self.combined_dataset = [] # Final unified dataset
        self.learning_stats = {}
        
        print("🧠 Unified AI Learning System initialized")
        
    def import_all_existing_data(self):
        """Import ALL existing data sources"""
        total_imported = 0
        
        # 1. Import your existing training data
        training_files = list(Path(".").glob("training_data_*.json"))
        for file in training_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    manual_count = 0
                    for item in data:
                        if item.get('rectangles') and item.get('labeled_by') == 'manual':
                            self.manual_data.append(item)
                            manual_count += 1
                    
                    if manual_count > 0:
                        print(f"✅ Imported {manual_count} manual annotations from {file.name}")
                        total_imported += manual_count
            except Exception as e:
                print(f"⚠️ Failed to import {file}: {e}")
        
        # 2. Import YOLO bootstrap data
        yolo_files = list(Path(".").glob("yolo_bootstrap_*.json"))
        for file in yolo_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    yolo_count = 0
                    for item in data.get('training_data', []):
                        if item.get('rectangles'):
                            self.yolo_data.append(item)
                            yolo_count += 1
                    
                    if yolo_count > 0:
                        print(f"✅ Imported {yolo_count} YOLO predictions from {file.name}")
                        total_imported += yolo_count
            except Exception as e:
                print(f"⚠️ Failed to import {file}: {e}")
        
        # 3. Import project data
        if os.path.exists("training_project.json"):
            try:
                with open("training_project.json", 'r', encoding='utf-8') as f:
                    project = json.load(f)
                    project_count = 0
                    
                    # Import from photo_progress
                    for photo_id, progress in project.get('photo_progress', {}).items():
                        rectangles = progress.get('rectangles', [])
                        if rectangles:
                            item = {
                                'photo_id': photo_id,
                                'rectangles': rectangles,
                                'labeled_by': 'manual_session',
                                'timestamp': time.time(),
                                'attributes': progress.get('attributes', {})
                            }
                            self.manual_data.append(item)
                            project_count += 1
                    
                    # Import from training_data
                    for item in project.get('training_data', []):
                        if item.get('rectangles'):
                            if item.get('labeled_by') == 'yolo_bootstrap':
                                self.yolo_data.append(item)
                            else:
                                self.manual_data.append(item)
                            project_count += 1
                    
                    if project_count > 0:
                        print(f"✅ Imported {project_count} items from project file")
                        total_imported += project_count
                        
            except Exception as e:
                print(f"⚠️ Failed to import project: {e}")
        
        print(f"\n📊 TOTAL IMPORTED: {total_imported} training items")
        return total_imported
    
    def analyze_data_quality(self) -> Dict:
        """Analyze the quality and distribution of all data"""
        analysis = {
            'manual_data': {
                'count': len(self.manual_data),
                'rectangles': sum(len(item.get('rectangles', [])) for item in self.manual_data),
                'holders': 0,
                'signs': 0
            },
            'yolo_data': {
                'count': len(self.yolo_data), 
                'rectangles': sum(len(item.get('rectangles', [])) for item in self.yolo_data),
                'holders': 0,
                'signs': 0
            },
            'quality_scores': {},
            'recommendations': []
        }
        
        # Count object types in manual data
        for item in self.manual_data:
            for rect in item.get('rectangles', []):
                if rect.get('type') == 'holder':
                    analysis['manual_data']['holders'] += 1
                elif rect.get('type') == 'sign':
                    analysis['manual_data']['signs'] += 1
        
        # Count object types in YOLO data  
        for item in self.yolo_data:
            for rect in item.get('rectangles', []):
                if rect.get('type') == 'holder':
                    analysis['yolo_data']['holders'] += 1
                elif rect.get('type') == 'sign':
                    analysis['yolo_data']['signs'] += 1
        
        # Quality assessment
        total_rectangles = analysis['manual_data']['rectangles'] + analysis['yolo_data']['rectangles']
        manual_percentage = (analysis['manual_data']['rectangles'] / total_rectangles * 100) if total_rectangles > 0 else 0
        
        analysis['quality_scores'] = {
            'total_rectangles': total_rectangles,
            'manual_percentage': manual_percentage,
            'yolo_percentage': 100 - manual_percentage,
            'data_diversity': self.calculate_diversity_score()
        }
        
        # Generate recommendations
        if total_rectangles < 50:
            analysis['recommendations'].append("Need more training data (current: {}, recommended: 200+)")
        if manual_percentage < 20:
            analysis['recommendations'].append("Need more manual corrections for quality")
        if analysis['manual_data']['holders'] < 20:
            analysis['recommendations'].append("Need more manual holder examples")
        if analysis['manual_data']['signs'] < 20:
            analysis['recommendations'].append("Need more manual sign examples")
        
        if not analysis['recommendations']:
            analysis['recommendations'].append("Dataset looks good! Ready for training.")
            
        return analysis
    
    def calculate_diversity_score(self) -> float:
        """Calculate how diverse the dataset is"""
        unique_photos = set()
        
        for item in self.manual_data + self.yolo_data:
            photo_id = item.get('photo_id')
            if photo_id:
                unique_photos.add(photo_id)
        
        # Simple diversity based on number of unique photos
        return len(unique_photos)
    
    def create_unified_dataset(self) -> List[Dict]:
        """Create the most effective unified training dataset"""
        print("\n🔄 Creating unified dataset...")
        
        unified = []
        photo_data = {}  # Group by photo_id
        
        # Group all data by photo_id
        for item in self.manual_data:
            photo_id = item.get('photo_id')
            if photo_id:
                if photo_id not in photo_data:
                    photo_data[photo_id] = {'manual': [], 'yolo': [], 'photo_path': item.get('photo_path')}
                photo_data[photo_id]['manual'].append(item)
        
        for item in self.yolo_data:
            photo_id = item.get('photo_id')
            if photo_id:
                if photo_id not in photo_data:
                    photo_data[photo_id] = {'manual': [], 'yolo': [], 'photo_path': item.get('photo_path')}
                photo_data[photo_id]['yolo'].append(item)
        
        # Create unified items
        for photo_id, data in photo_data.items():
            manual_items = data['manual']
            yolo_items = data['yolo']
            
            # Combine rectangles intelligently
            final_rectangles = []
            
            if manual_items:
                # Manual data takes priority (higher quality)
                for item in manual_items:
                    final_rectangles.extend(item.get('rectangles', []))
                    
                unified_item = {
                    'photo_id': photo_id,
                    'photo_path': data['photo_path'],
                    'rectangles': final_rectangles,
                    'data_source': 'manual_priority',
                    'quality': 'high',
                    'timestamp': time.time()
                }
                
            elif yolo_items:
                # Use YOLO data if no manual data available
                for item in yolo_items:
                    yolo_rects = item.get('rectangles', [])
                    # Filter YOLO rectangles by confidence
                    filtered_rects = [r for r in yolo_rects if r.get('confidence', 0) > 0.3]
                    final_rectangles.extend(filtered_rects)
                    
                unified_item = {
                    'photo_id': photo_id,
                    'photo_path': data['photo_path'], 
                    'rectangles': final_rectangles,
                    'data_source': 'yolo_filtered',
                    'quality': 'medium',
                    'timestamp': time.time()
                }
            else:
                continue
                
            if final_rectangles:  # Only add if has rectangles
                unified.append(unified_item)
        
        self.combined_dataset = unified
        
        # Statistics
        total_photos = len(unified)
        total_rectangles = sum(len(item['rectangles']) for item in unified)
        manual_photos = len([item for item in unified if item['data_source'] == 'manual_priority'])
        yolo_photos = len([item for item in unified if item['data_source'] == 'yolo_filtered'])
        
        print(f"✅ Unified dataset created:")
        print(f"  📸 Total photos: {total_photos}")
        print(f"  📦 Total rectangles: {total_rectangles}")
        print(f"  ✋ Manual photos: {manual_photos} (high quality)")
        print(f"  🤖 YOLO photos: {yolo_photos} (medium quality)")
        print(f"  📊 Average rectangles/photo: {total_rectangles/total_photos:.1f}")
        
        return unified
    
    def progressive_learning_strategy(self) -> Dict:
        """Design the most effective learning strategy"""
        analysis = self.analyze_data_quality()
        
        strategy = {
            'current_phase': '',
            'next_actions': [],
            'priority_tasks': [],
            'effectiveness_score': 0
        }
        
        manual_rects = analysis['manual_data']['rectangles']
        yolo_rects = analysis['yolo_data']['rectangles']
        total_rects = manual_rects + yolo_rects
        
        # Determine current phase
        if manual_rects < 20:
            strategy['current_phase'] = 'bootstrap_phase'
            strategy['next_actions'] = [
                'Use YOLO bootstrap to get initial predictions',
                'Manually correct 50-100 YOLO predictions',
                'Focus on diverse photo types'
            ]
            strategy['effectiveness_score'] = 2
            
        elif manual_rects < 100:
            strategy['current_phase'] = 'correction_phase'
            strategy['next_actions'] = [
                'Continue correcting YOLO predictions',
                'Add manual rectangles for missed objects',
                'Focus on difficult cases YOLO missed'
            ]
            strategy['effectiveness_score'] = 5
            
        elif manual_rects < 200:
            strategy['current_phase'] = 'training_phase'
            strategy['next_actions'] = [
                'Train first custom AI model',
                'Test accuracy on validation set',
                'Compare with YOLO baseline'
            ]
            strategy['effectiveness_score'] = 7
            
        else:
            strategy['current_phase'] = 'refinement_phase'
            strategy['next_actions'] = [
                'Fine-tune AI model',
                'Add hard negative examples',
                'Optimize for production use'
            ]
            strategy['effectiveness_score'] = 9
        
        # Priority tasks based on data gaps
        if analysis['manual_data']['holders'] < analysis['manual_data']['signs']:
            strategy['priority_tasks'].append('Add more holder examples')
        if analysis['manual_data']['signs'] < analysis['manual_data']['holders']:
            strategy['priority_tasks'].append('Add more sign examples')
        
        return strategy
    
    def save_unified_dataset(self, filename: str = None):
        """Save the unified dataset"""
        if not filename:
            filename = f"unified_dataset_{int(time.time())}.json"
            
        try:
            dataset_info = {
                'version': '1.0',
                'created': time.time(),
                'statistics': {
                    'total_photos': len(self.combined_dataset),
                    'total_rectangles': sum(len(item['rectangles']) for item in self.combined_dataset),
                    'data_sources': {}
                },
                'dataset': self.combined_dataset
            }
            
            # Count data sources
            for item in self.combined_dataset:
                source = item.get('data_source', 'unknown')
                dataset_info['statistics']['data_sources'][source] = dataset_info['statistics']['data_sources'].get(source, 0) + 1
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Unified dataset saved to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to save dataset: {e}")
            return None
    
    def generate_effectiveness_report(self) -> str:
        """Generate comprehensive effectiveness report"""
        analysis = self.analyze_data_quality()
        strategy = self.progressive_learning_strategy()
        
        report = f"""
🧠 UNIFIED AI LEARNING SYSTEM - EFFECTIVENESS REPORT
{'='*60}

📊 CURRENT DATA STATUS:
• Manual annotations: {analysis['manual_data']['rectangles']} rectangles ({analysis['manual_data']['count']} photos)
  - Holders: {analysis['manual_data']['holders']}
  - Signs: {analysis['manual_data']['signs']}
  
• YOLO predictions: {analysis['yolo_data']['rectangles']} rectangles ({analysis['yolo_data']['count']} photos)
  - Holders: {analysis['yolo_data']['holders']} 
  - Signs: {analysis['yolo_data']['signs']}

• Total dataset: {analysis['quality_scores']['total_rectangles']} rectangles
• Manual quality: {analysis['quality_scores']['manual_percentage']:.1f}%
• Photo diversity: {analysis['quality_scores']['data_diversity']} unique photos

🎯 LEARNING PHASE: {strategy['current_phase'].upper().replace('_', ' ')}
Effectiveness Score: {strategy['effectiveness_score']}/10

🚀 NEXT ACTIONS:
"""
        
        for i, action in enumerate(strategy['next_actions'], 1):
            report += f"{i}. {action}\n"
        
        report += f"\n⚡ PRIORITY TASKS:\n"
        for i, task in enumerate(strategy['priority_tasks'], 1):
            report += f"{i}. {task}\n"
        
        report += f"\n💡 RECOMMENDATIONS:\n"
        for i, rec in enumerate(analysis['recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        return report

def main():
    """Main function to run the unified system"""
    system = UnifiedAISystem()
    
    print("🚀 UNIFIED AI LEARNING SYSTEM")
    print("="*50)
    
    # Import all existing data
    total_imported = system.import_all_existing_data()
    
    if total_imported == 0:
        print("\n⚠️  No existing training data found!")
        print("Start by drawing some rectangles or running YOLO bootstrap.")
        return
    
    # Create unified dataset
    unified = system.create_unified_dataset()
    
    # Save unified dataset
    filename = system.save_unified_dataset()
    
    # Generate and show effectiveness report
    report = system.generate_effectiveness_report()
    print(report)
    
    return system, unified, filename

if __name__ == "__main__":
    main()