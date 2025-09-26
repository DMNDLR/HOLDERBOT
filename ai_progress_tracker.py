#!/usr/bin/env python3
"""
🧠 AI PROGRESS TRACKER & REAL TRAINING
=====================================
Track training progress and implement real AI improvement over time.
"""

import json
import numpy as np
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from pathlib import Path
import time

class AIProgressTracker:
    def __init__(self):
        self.model_holders = None
        self.model_signs = None
        self.training_history = []
        self.accuracy_history = []
        
    def extract_features_from_rectangle(self, image_path: str, rect: Dict) -> List[float]:
        """Extract features from a rectangle region in image"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            # Extract rectangle region
            x1, y1, x2, y2 = int(rect['x1']), int(rect['y1']), int(rect['x2']), int(rect['y2'])
            
            # Make sure coordinates are valid
            h, w = image.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 <= x1 or y2 <= y1:
                return []
            
            roi = image[y1:y2, x1:x2]
            
            # Extract basic features
            features = []
            
            # Size features
            width = x2 - x1
            height = y2 - y1
            aspect_ratio = width / height if height > 0 else 0
            area = width * height
            
            features.extend([width, height, aspect_ratio, area])
            
            # Color features
            if roi.size > 0:
                # RGB mean and std
                rgb_mean = np.mean(roi, axis=(0, 1))
                rgb_std = np.std(roi, axis=(0, 1))
                features.extend(rgb_mean.tolist())
                features.extend(rgb_std.tolist())
                
                # HSV features
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                hsv_mean = np.mean(hsv, axis=(0, 1))
                features.extend(hsv_mean.tolist())
                
                # Edge density
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.sum(edges > 0) / edges.size
                features.append(edge_density)
                
            return features
            
        except Exception as e:
            print(f"Feature extraction failed: {e}")
            return []
    
    def train_from_rectangles(self, training_data: List[Dict]) -> Dict:
        """Train AI models from rectangle training data"""
        print("🧠 Training AI models from your rectangle data...")
        
        # Prepare training data
        holder_features = []
        holder_labels = []
        sign_features = []
        sign_labels = []
        
        processed_items = 0
        
        for item in training_data:
            if 'rectangles' not in item or not item.get('photo_path'):
                continue
                
            photo_path = item['photo_path']
            if not os.path.exists(photo_path):
                continue
            
            rectangles = item['rectangles']
            
            for rect in rectangles:
                features = self.extract_features_from_rectangle(photo_path, rect)
                if not features:
                    continue
                    
                if rect['type'] == 'holder':
                    holder_features.append(features)
                    holder_labels.append(1)  # 1 = holder
                    
                    # Add negative examples (background)
                    neg_features = self.generate_negative_samples(photo_path, rect)
                    for neg_feat in neg_features:
                        holder_features.append(neg_feat)
                        holder_labels.append(0)  # 0 = not holder
                        
                elif rect['type'] == 'sign':
                    sign_features.append(features)
                    sign_labels.append(1)  # 1 = sign
                    
                    # Add negative examples
                    neg_features = self.generate_negative_samples(photo_path, rect)
                    for neg_feat in neg_features:
                        sign_features.append(neg_feat)
                        sign_labels.append(0)  # 0 = not sign
                        
            processed_items += 1
            if processed_items % 10 == 0:
                print(f"  Processed {processed_items} photos...")
        
        results = {}
        
        # Train holder detection model
        if len(holder_features) > 20:  # Need minimum samples
            print(f"📊 Training holder detector with {len(holder_features)} samples...")
            
            X = np.array(holder_features)
            y = np.array(holder_labels)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            self.model_holders = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model_holders.fit(X_train, y_train)
            
            # Test accuracy
            y_pred = self.model_holders.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            results['holder_accuracy'] = accuracy
            results['holder_samples'] = len(holder_features)
            
            # Save model
            joblib.dump(self.model_holders, 'holder_detector.joblib')
            print(f"  ✅ Holder detector trained: {accuracy:.2%} accuracy")
            
        # Train sign detection model
        if len(sign_features) > 20:
            print(f"📊 Training sign detector with {len(sign_features)} samples...")
            
            X = np.array(sign_features)
            y = np.array(sign_labels)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            self.model_signs = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model_signs.fit(X_train, y_train)
            
            # Test accuracy
            y_pred = self.model_signs.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            results['sign_accuracy'] = accuracy
            results['sign_samples'] = len(sign_features)
            
            # Save model
            joblib.dump(self.model_signs, 'sign_detector.joblib')
            print(f"  ✅ Sign detector trained: {accuracy:.2%} accuracy")
        
        # Save training history
        training_record = {
            'timestamp': time.time(),
            'holder_samples': results.get('holder_samples', 0),
            'sign_samples': results.get('sign_samples', 0),
            'holder_accuracy': results.get('holder_accuracy', 0),
            'sign_accuracy': results.get('sign_accuracy', 0)
        }
        
        self.training_history.append(training_record)
        self.save_progress_history()
        
        return results
    
    def generate_negative_samples(self, image_path: str, positive_rect: Dict, num_samples: int = 3) -> List[List[float]]:
        """Generate negative training samples (background areas)"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            h, w = image.shape[:2]
            negative_features = []
            
            # Generate random rectangles that don't overlap with positive ones
            for _ in range(num_samples):
                # Random rectangle size (similar to positive)
                pos_w = positive_rect['x2'] - positive_rect['x1']
                pos_h = positive_rect['y2'] - positive_rect['y1']
                
                rand_w = int(pos_w * np.random.uniform(0.7, 1.3))
                rand_h = int(pos_h * np.random.uniform(0.7, 1.3))
                
                # Random position
                if w > rand_w and h > rand_h:
                    x1 = np.random.randint(0, w - rand_w)
                    y1 = np.random.randint(0, h - rand_h)
                    x2 = x1 + rand_w
                    y2 = y1 + rand_h
                    
                    # Check if it overlaps with positive rectangle
                    if not self.rectangles_overlap(
                        positive_rect['x1'], positive_rect['y1'], positive_rect['x2'], positive_rect['y2'],
                        x1, y1, x2, y2
                    ):
                        neg_rect = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
                        features = self.extract_features_from_rectangle(image_path, neg_rect)
                        if features:
                            negative_features.append(features)
            
            return negative_features
            
        except Exception as e:
            print(f"Negative sampling failed: {e}")
            return []
    
    def rectangles_overlap(self, x1a, y1a, x2a, y2a, x1b, y1b, x2b, y2b) -> bool:
        """Check if two rectangles overlap"""
        return not (x2a < x1b or x2b < x1a or y2a < y1b or y2b < y1a)
    
    def predict_objects(self, image_path: str) -> List[Dict]:
        """Make real AI predictions on image"""
        if not os.path.exists(image_path):
            return []
            
        predictions = []
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            h, w = image.shape[:2]
            
            # Sliding window detection (simplified)
            step_size = 30
            window_sizes = [(60, 80), (40, 60), (80, 100)]  # Different scales
            
            for window_w, window_h in window_sizes:
                for y in range(0, h - window_h, step_size):
                    for x in range(0, w - window_w, step_size):
                        rect = {
                            'x1': x, 'y1': y, 
                            'x2': x + window_w, 'y2': y + window_h
                        }
                        
                        features = self.extract_features_from_rectangle(image_path, rect)
                        if not features:
                            continue
                        
                        # Test with holder model
                        if self.model_holders is not None:
                            try:
                                # Pad features to match training size
                                features_array = np.array(features).reshape(1, -1)
                                if features_array.shape[1] == self.model_holders.n_features_in_:
                                    holder_prob = self.model_holders.predict_proba(features_array)[0][1]
                                    
                                    if holder_prob > 0.7:  # High confidence threshold
                                        predictions.append({
                                            'type': 'holder',
                                            'confidence': holder_prob,
                                            'bbox': [x, y, x + window_w, y + window_h]
                                        })
                            except:
                                pass
                        
                        # Test with sign model
                        if self.model_signs is not None:
                            try:
                                features_array = np.array(features).reshape(1, -1)
                                if features_array.shape[1] == self.model_signs.n_features_in_:
                                    sign_prob = self.model_signs.predict_proba(features_array)[0][1]
                                    
                                    if sign_prob > 0.6:  # Lower threshold for signs
                                        predictions.append({
                                            'type': 'sign',
                                            'confidence': sign_prob,
                                            'bbox': [x, y, x + window_w, y + window_h]
                                        })
                            except:
                                pass
            
            # Non-maximum suppression to remove overlapping detections
            predictions = self.non_max_suppression(predictions)
            
        except Exception as e:
            print(f"Prediction failed: {e}")
        
        return predictions[:10]  # Limit to top 10 predictions
    
    def non_max_suppression(self, predictions: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """Remove overlapping predictions"""
        if not predictions:
            return []
        
        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        filtered = []
        for pred in predictions:
            bbox = pred['bbox']
            
            # Check if this prediction overlaps significantly with any already selected
            should_keep = True
            for kept in filtered:
                if self.calculate_iou(bbox, kept['bbox']) > iou_threshold:
                    should_keep = False
                    break
            
            if should_keep:
                filtered.append(pred)
        
        return filtered
    
    def calculate_iou(self, bbox1: List, bbox2: List) -> float:
        """Calculate Intersection over Union of two bounding boxes"""
        x1a, y1a, x2a, y2a = bbox1
        x1b, y1b, x2b, y2b = bbox2
        
        # Calculate intersection
        xi1, yi1 = max(x1a, x1b), max(y1a, y1b)
        xi2, yi2 = min(x2a, x2b), min(x2b, y2b)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        
        # Calculate union
        area1 = (x2a - x1a) * (y2a - y1a)
        area2 = (x2b - x1b) * (y2b - y1b)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def load_existing_models(self):
        """Load previously trained models"""
        try:
            if os.path.exists('holder_detector.joblib'):
                self.model_holders = joblib.load('holder_detector.joblib')
                print("✅ Loaded existing holder detector")
            
            if os.path.exists('sign_detector.joblib'):
                self.model_signs = joblib.load('sign_detector.joblib')
                print("✅ Loaded existing sign detector")
                
        except Exception as e:
            print(f"Failed to load models: {e}")
    
    def save_progress_history(self):
        """Save training progress history"""
        try:
            with open('training_progress.json', 'w') as f:
                json.dump(self.training_history, f, indent=2)
        except Exception as e:
            print(f"Failed to save progress: {e}")
    
    def load_progress_history(self):
        """Load training progress history"""
        try:
            if os.path.exists('training_progress.json'):
                with open('training_progress.json', 'r') as f:
                    self.training_history = json.load(f)
        except Exception as e:
            print(f"Failed to load progress: {e}")
    
    def generate_progress_report(self) -> Dict:
        """Generate detailed progress report"""
        if not self.training_history:
            return {
                'status': 'no_training',
                'message': 'No training completed yet. Draw rectangles and save them first!'
            }
        
        latest = self.training_history[-1]
        
        report = {
            'status': 'trained',
            'latest_training': {
                'holder_samples': latest.get('holder_samples', 0),
                'sign_samples': latest.get('sign_samples', 0),
                'holder_accuracy': latest.get('holder_accuracy', 0),
                'sign_accuracy': latest.get('sign_accuracy', 0)
            },
            'improvement': {
                'training_sessions': len(self.training_history),
                'first_training': self.training_history[0] if self.training_history else None,
                'latest_training': latest
            }
        }
        
        # Calculate improvement over time
        if len(self.training_history) > 1:
            first = self.training_history[0]
            report['improvement']['holder_accuracy_gain'] = latest.get('holder_accuracy', 0) - first.get('holder_accuracy', 0)
            report['improvement']['sign_accuracy_gain'] = latest.get('sign_accuracy', 0) - first.get('sign_accuracy', 0)
        
        return report

if __name__ == "__main__":
    tracker = AIProgressTracker()
    tracker.load_progress_history()
    tracker.load_existing_models()
    
    report = tracker.generate_progress_report()
    print(json.dumps(report, indent=2))