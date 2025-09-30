#!/usr/bin/env python3
"""
🧠 AI LEARNING SYSTEM
====================
Adaptive learning system for HOLDERBOT and SIGNBOT to improve accuracy over time

Features:
- Learning from user feedback and corrections
- Pattern recognition for common mistakes
- Adaptive prompt optimization
- Performance tracking and analytics
- Confidence calibration
"""

import json
import os
import time
from datetime import datetime
from collections import defaultdict, Counter
import statistics

class LearningSystem:
    def __init__(self, data_path="learning_data"):
        """Initialize the learning system"""
        self.data_path = data_path
        self.ensure_data_directory()
        
        # Learning databases
        self.holder_learning_db = self.load_learning_db("holder_learning.json")
        self.sign_learning_db = self.load_learning_db("sign_learning.json")
        
        # Performance tracking
        self.performance_stats = self.load_performance_stats()
        
        # Pattern recognition
        self.common_mistakes = self.load_common_mistakes()
        
    def ensure_data_directory(self):
        """Create learning data directory if it doesn't exist"""
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            
    def load_learning_db(self, filename):
        """Load learning database from file"""
        filepath = os.path.join(self.data_path, filename)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load {filename}: {e}")
        
        # Return default structure
        return {
            "corrections": [],
            "successful_predictions": [],
            "image_patterns": {},
            "confidence_calibration": {},
            "prompt_effectiveness": {}
        }
    
    def load_performance_stats(self):
        """Load performance statistics"""
        filepath = os.path.join(self.data_path, "performance_stats.json")
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load performance stats: {e}")
            
        return {
            "holder_stats": {
                "total_processed": 0,
                "correct_predictions": 0,
                "accuracy_history": [],
                "confidence_accuracy": {}
            },
            "sign_stats": {
                "total_processed": 0,
                "correct_predictions": 0,
                "accuracy_history": [],
                "sign_detection_accuracy": {}
            }
        }
    
    def load_common_mistakes(self):
        """Load common mistake patterns"""
        filepath = os.path.join(self.data_path, "common_mistakes.json")
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load common mistakes: {e}")
            
        return {
            "holder_mistakes": {},
            "sign_mistakes": {},
            "confusion_matrix": {}
        }
    
    def save_learning_data(self):
        """Save all learning data to files"""
        try:
            # Save holder learning database
            with open(os.path.join(self.data_path, "holder_learning.json"), 'w', encoding='utf-8') as f:
                json.dump(self.holder_learning_db, f, indent=2, ensure_ascii=False)
            
            # Save sign learning database
            with open(os.path.join(self.data_path, "sign_learning.json"), 'w', encoding='utf-8') as f:
                json.dump(self.sign_learning_db, f, indent=2, ensure_ascii=False)
            
            # Save performance stats
            with open(os.path.join(self.data_path, "performance_stats.json"), 'w', encoding='utf-8') as f:
                json.dump(self.performance_stats, f, indent=2, ensure_ascii=False)
            
            # Save common mistakes
            with open(os.path.join(self.data_path, "common_mistakes.json"), 'w', encoding='utf-8') as f:
                json.dump(self.common_mistakes, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to save learning data: {e}")
            return False
    
    def record_holder_prediction(self, holder_id, image_url, predicted_material, predicted_type, 
                               confidence, actual_material=None, actual_type=None, user_feedback=None):
        """Record a holder prediction for learning"""
        
        timestamp = datetime.now().isoformat()
        
        prediction_record = {
            "timestamp": timestamp,
            "holder_id": holder_id,
            "image_url": image_url,
            "predicted": {
                "material": predicted_material,
                "type": predicted_type
            },
            "confidence": confidence,
            "actual": {
                "material": actual_material,
                "type": actual_type
            } if actual_material and actual_type else None,
            "user_feedback": user_feedback,
            "correct": None
        }
        
        # Determine if prediction was correct
        if actual_material and actual_type:
            prediction_record["correct"] = (
                predicted_material == actual_material and 
                predicted_type == actual_type
            )
            
            # Update performance stats
            self.performance_stats["holder_stats"]["total_processed"] += 1
            if prediction_record["correct"]:
                self.performance_stats["holder_stats"]["correct_predictions"] += 1
            
            # Update accuracy history
            current_accuracy = (
                self.performance_stats["holder_stats"]["correct_predictions"] / 
                self.performance_stats["holder_stats"]["total_processed"]
            )
            self.performance_stats["holder_stats"]["accuracy_history"].append({
                "timestamp": timestamp,
                "accuracy": current_accuracy
            })
            
            # Record confidence calibration
            confidence_bucket = round(confidence * 10) * 10  # Round to nearest 10%
            if confidence_bucket not in self.performance_stats["holder_stats"]["confidence_accuracy"]:
                self.performance_stats["holder_stats"]["confidence_accuracy"][confidence_bucket] = {
                    "total": 0, "correct": 0
                }
            
            self.performance_stats["holder_stats"]["confidence_accuracy"][confidence_bucket]["total"] += 1
            if prediction_record["correct"]:
                self.performance_stats["holder_stats"]["confidence_accuracy"][confidence_bucket]["correct"] += 1
        
        # Add to learning database
        if prediction_record["correct"] == True:
            self.holder_learning_db["successful_predictions"].append(prediction_record)
        elif prediction_record["correct"] == False:
            self.holder_learning_db["corrections"].append(prediction_record)
            
            # Record common mistake
            mistake_key = f"{predicted_material}+{predicted_type} -> {actual_material}+{actual_type}"
            if mistake_key not in self.common_mistakes["holder_mistakes"]:
                self.common_mistakes["holder_mistakes"][mistake_key] = 0
            self.common_mistakes["holder_mistakes"][mistake_key] += 1
        
        self.save_learning_data()
        return prediction_record
    
    def record_sign_prediction(self, holder_id, image_url, predicted_signs, confidence,
                             actual_signs=None, user_feedback=None):
        """Record a sign prediction for learning"""
        
        timestamp = datetime.now().isoformat()
        
        prediction_record = {
            "timestamp": timestamp,
            "holder_id": holder_id,
            "image_url": image_url,
            "predicted_signs": predicted_signs,
            "confidence": confidence,
            "actual_signs": actual_signs,
            "user_feedback": user_feedback,
            "correct": None
        }
        
        # Determine if prediction was correct
        if actual_signs is not None:
            predicted_set = set(predicted_signs)
            actual_set = set(actual_signs)
            
            # Calculate accuracy metrics
            correct_signs = len(predicted_set.intersection(actual_set))
            total_actual = len(actual_set)
            total_predicted = len(predicted_set)
            
            # Precision and recall
            precision = correct_signs / total_predicted if total_predicted > 0 else 0
            recall = correct_signs / total_actual if total_actual > 0 else 0
            
            prediction_record["precision"] = precision
            prediction_record["recall"] = recall
            prediction_record["f1_score"] = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            prediction_record["correct"] = prediction_record["f1_score"] >= 0.8  # Consider F1 >= 0.8 as correct
            
            # Update performance stats
            self.performance_stats["sign_stats"]["total_processed"] += 1
            if prediction_record["correct"]:
                self.performance_stats["sign_stats"]["correct_predictions"] += 1
            
            # Record individual sign accuracy
            for sign in actual_signs:
                if sign not in self.performance_stats["sign_stats"]["sign_detection_accuracy"]:
                    self.performance_stats["sign_stats"]["sign_detection_accuracy"][sign] = {"total": 0, "detected": 0}
                
                self.performance_stats["sign_stats"]["sign_detection_accuracy"][sign]["total"] += 1
                if sign in predicted_signs:
                    self.performance_stats["sign_stats"]["sign_detection_accuracy"][sign]["detected"] += 1
        
        # Add to learning database
        if prediction_record["correct"] == True:
            self.sign_learning_db["successful_predictions"].append(prediction_record)
        elif prediction_record["correct"] == False:
            self.sign_learning_db["corrections"].append(prediction_record)
        
        self.save_learning_data()
        return prediction_record
    
    def get_learning_insights(self):
        """Get insights from learning data for prompt optimization"""
        
        insights = {
            "holder_insights": self._analyze_holder_learning(),
            "sign_insights": self._analyze_sign_learning(),
            "overall_performance": self._get_overall_performance()
        }
        
        return insights
    
    def _analyze_holder_learning(self):
        """Analyze holder learning data for insights"""
        
        insights = {
            "most_common_mistakes": {},
            "confidence_calibration": {},
            "material_accuracy": {},
            "type_accuracy": {},
            "recommendations": []
        }
        
        # Analyze common mistakes
        if self.common_mistakes["holder_mistakes"]:
            sorted_mistakes = sorted(
                self.common_mistakes["holder_mistakes"].items(),
                key=lambda x: x[1], reverse=True
            )
            insights["most_common_mistakes"] = dict(sorted_mistakes[:5])
        
        # Analyze confidence calibration
        conf_cal = self.performance_stats["holder_stats"]["confidence_accuracy"]
        for confidence_level, stats in conf_cal.items():
            if stats["total"] > 0:
                actual_accuracy = stats["correct"] / stats["total"]
                insights["confidence_calibration"][confidence_level] = {
                    "predicted_confidence": confidence_level,
                    "actual_accuracy": actual_accuracy,
                    "calibration_error": abs(confidence_level/100 - actual_accuracy)
                }
        
        # Generate recommendations
        if insights["most_common_mistakes"]:
            top_mistake = list(insights["most_common_mistakes"].keys())[0]
            insights["recommendations"].append(
                f"Focus on distinguishing {top_mistake.split(' -> ')[0]} from {top_mistake.split(' -> ')[1]}"
            )
        
        return insights
    
    def _analyze_sign_learning(self):
        """Analyze sign learning data for insights"""
        
        insights = {
            "hardest_signs_to_detect": {},
            "easiest_signs_to_detect": {},
            "common_false_positives": [],
            "missed_signs": [],
            "recommendations": []
        }
        
        # Analyze sign detection accuracy
        sign_accuracy = self.performance_stats["sign_stats"]["sign_detection_accuracy"]
        if sign_accuracy:
            # Calculate detection rates
            detection_rates = {}
            for sign, stats in sign_accuracy.items():
                if stats["total"] > 0:
                    detection_rates[sign] = stats["detected"] / stats["total"]
            
            # Find hardest and easiest signs
            if detection_rates:
                sorted_by_difficulty = sorted(detection_rates.items(), key=lambda x: x[1])
                insights["hardest_signs_to_detect"] = dict(sorted_by_difficulty[:3])
                insights["easiest_signs_to_detect"] = dict(sorted_by_difficulty[-3:])
        
        return insights
    
    def _get_overall_performance(self):
        """Get overall performance metrics"""
        
        performance = {
            "holder_bot": {
                "total_processed": self.performance_stats["holder_stats"]["total_processed"],
                "current_accuracy": 0,
                "accuracy_trend": "stable"
            },
            "sign_bot": {
                "total_processed": self.performance_stats["sign_stats"]["total_processed"],
                "current_accuracy": 0,
                "accuracy_trend": "stable"
            }
        }
        
        # Calculate current accuracy
        if performance["holder_bot"]["total_processed"] > 0:
            performance["holder_bot"]["current_accuracy"] = (
                self.performance_stats["holder_stats"]["correct_predictions"] /
                self.performance_stats["holder_stats"]["total_processed"]
            )
        
        if performance["sign_bot"]["total_processed"] > 0:
            performance["sign_bot"]["current_accuracy"] = (
                self.performance_stats["sign_stats"]["correct_predictions"] /
                self.performance_stats["sign_stats"]["total_processed"]
            )
        
        # Analyze accuracy trends
        holder_history = self.performance_stats["holder_stats"]["accuracy_history"]
        if len(holder_history) >= 10:
            recent_accuracy = [h["accuracy"] for h in holder_history[-10:]]
            earlier_accuracy = [h["accuracy"] for h in holder_history[-20:-10]] if len(holder_history) >= 20 else []
            
            if earlier_accuracy:
                recent_avg = statistics.mean(recent_accuracy)
                earlier_avg = statistics.mean(earlier_accuracy)
                
                if recent_avg > earlier_avg + 0.05:
                    performance["holder_bot"]["accuracy_trend"] = "improving"
                elif recent_avg < earlier_avg - 0.05:
                    performance["holder_bot"]["accuracy_trend"] = "declining"
        
        return performance
    
    def get_optimized_prompts(self):
        """Generate optimized prompts based on learning data"""
        
        insights = self.get_learning_insights()
        
        optimized_prompts = {
            "holder_prompt_additions": self._generate_holder_prompt_improvements(insights),
            "sign_prompt_additions": self._generate_sign_prompt_improvements(insights)
        }
        
        return optimized_prompts
    
    def _generate_holder_prompt_improvements(self, insights):
        """Generate improved holder prompts based on learning"""
        
        additions = []
        
        # Address common mistakes
        holder_insights = insights["holder_insights"]
        if holder_insights["most_common_mistakes"]:
            for mistake, count in list(holder_insights["most_common_mistakes"].items())[:3]:
                wrong, correct = mistake.split(" -> ")
                additions.append(
                    f"⚠️ COMMON MISTAKE: Don't confuse {wrong} with {correct}. "
                    f"This error occurred {count} times in learning data."
                )
        
        # Address confidence calibration issues
        if holder_insights["confidence_calibration"]:
            overconfident_levels = [
                level for level, cal in holder_insights["confidence_calibration"].items()
                if cal["calibration_error"] > 0.2 and cal["predicted_confidence"] > cal["actual_accuracy"] * 100
            ]
            
            if overconfident_levels:
                additions.append(
                    "🎯 CONFIDENCE CALIBRATION: You tend to be overconfident. "
                    "Only use high confidence (>0.8) when you're absolutely certain of visual evidence."
                )
        
        return additions
    
    def _generate_sign_prompt_improvements(self, insights):
        """Generate improved sign prompts based on learning"""
        
        additions = []
        
        # Address hard-to-detect signs
        sign_insights = insights["sign_insights"]
        if sign_insights["hardest_signs_to_detect"]:
            hard_signs = list(sign_insights["hardest_signs_to_detect"].keys())[:3]
            additions.append(
                f"🔍 FOCUS AREAS: Pay special attention to detecting these frequently missed signs: {', '.join(hard_signs)}. "
                "Look more carefully for these specific sign types."
            )
        
        return additions
    
    def run_learning_session(self, gui_instance):
        """Run an interactive learning session"""
        
        print("\n🧠 AI LEARNING SESSION STARTED")
        print("=" * 50)
        
        insights = self.get_learning_insights()
        
        print(f"📊 PERFORMANCE SUMMARY:")
        performance = insights["overall_performance"]
        
        print(f"   🏗️ HOLDERBOT: {performance['holder_bot']['current_accuracy']:.1%} accuracy "
              f"({performance['holder_bot']['total_processed']} processed)")
        print(f"   🚦 SIGNBOT: {performance['sign_bot']['current_accuracy']:.1%} accuracy "
              f"({performance['sign_bot']['total_processed']} processed)")
        
        print(f"\n🎯 KEY INSIGHTS:")
        
        # Holder insights
        holder_insights = insights["holder_insights"]
        if holder_insights["most_common_mistakes"]:
            print("   🏗️ HOLDERBOT Common Mistakes:")
            for mistake, count in list(holder_insights["most_common_mistakes"].items())[:3]:
                print(f"      • {mistake} ({count} times)")
        
        # Sign insights  
        sign_insights = insights["sign_insights"]
        if sign_insights["hardest_signs_to_detect"]:
            print("   🚦 SIGNBOT Hardest Signs:")
            for sign, accuracy in sign_insights["hardest_signs_to_detect"].items():
                print(f"      • Sign {sign}: {accuracy:.1%} detection rate")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in holder_insights.get("recommendations", []):
            print(f"   • {rec}")
        for rec in sign_insights.get("recommendations", []):
            print(f"   • {rec}")
        
        # Generate optimized prompts
        optimized_prompts = self.get_optimized_prompts()
        
        print(f"\n🔧 PROMPT OPTIMIZATIONS AVAILABLE:")
        print(f"   • {len(optimized_prompts['holder_prompt_additions'])} holder prompt improvements")
        print(f"   • {len(optimized_prompts['sign_prompt_additions'])} sign prompt improvements")
        
        print("\n✅ Learning session complete!")
        print("💡 The system will automatically use these insights to improve accuracy.")
        
        return insights
    
    def get_accuracy_report(self, bot_type):
        """Get accuracy report for specified bot type ('holder' or 'sign')"""
        if bot_type == 'holder':
            stats = self.performance_stats["holder_stats"]
            total = stats["total_processed"]
            correct = stats["correct_predictions"]
            
            # Calculate average confidence from recent predictions
            avg_confidence = 0.0
            if hasattr(self, 'holder_learning_db') and self.holder_learning_db:
                all_predictions = (self.holder_learning_db.get("successful_predictions", []) + 
                                 self.holder_learning_db.get("corrections", []))
                if all_predictions:
                    confidences = [p.get("confidence", 0.5) for p in all_predictions[-10:]]  # Last 10
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'total_predictions': total,
                'correct_predictions': correct,
                'incorrect_predictions': total - correct,
                'accuracy': correct / total if total > 0 else 0.0,
                'avg_confidence': avg_confidence
            }
        
        elif bot_type == 'sign':
            stats = self.performance_stats["sign_stats"]
            total = stats["total_processed"]
            correct = stats["correct_predictions"]
            
            # Calculate average confidence from recent predictions
            avg_confidence = 0.0
            if hasattr(self, 'sign_learning_db') and self.sign_learning_db:
                all_predictions = (self.sign_learning_db.get("successful_predictions", []) + 
                                 self.sign_learning_db.get("corrections", []))
                if all_predictions:
                    confidences = [p.get("confidence", 0.5) for p in all_predictions[-10:]]  # Last 10
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'total_predictions': total,
                'correct_predictions': correct,
                'incorrect_predictions': total - correct,
                'accuracy': correct / total if total > 0 else 0.0,
                'avg_confidence': avg_confidence
            }
        
        else:
            # Invalid bot type
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'incorrect_predictions': 0,
                'accuracy': 0.0,
                'avg_confidence': 0.0
            }
    
    def analyze_errors(self):
        """Analyze errors and patterns for both holder and sign predictions"""
        analysis = {
            'holder_errors': {},
            'sign_errors': {},
            'error_patterns': [],
            'confidence_issues': []
        }
        
        # Analyze holder errors
        holder_corrections = self.holder_learning_db.get("corrections", [])
        if holder_corrections:
            # Count error types
            material_errors = Counter()
            type_errors = Counter()
            
            for correction in holder_corrections:
                if correction.get("predicted") and correction.get("actual"):
                    predicted = correction["predicted"]
                    actual = correction["actual"]
                    
                    if predicted["material"] != actual["material"]:
                        error_key = f"{predicted['material']} → {actual['material']}"
                        material_errors[error_key] += 1
                    
                    if predicted["type"] != actual["type"]:
                        error_key = f"{predicted['type']} → {actual['type']}"
                        type_errors[error_key] += 1
            
            analysis['holder_errors']['material_confusion'] = dict(material_errors.most_common(5))
            analysis['holder_errors']['type_confusion'] = dict(type_errors.most_common(5))
        
        # Analyze sign errors
        sign_corrections = self.sign_learning_db.get("corrections", [])
        if sign_corrections:
            missed_signs = Counter()
            false_positives = Counter()
            
            for correction in sign_corrections:
                predicted_signs = set(correction.get("predicted_signs", []))
                actual_signs = set(correction.get("actual_signs", []))
                
                # Signs that were missed (in actual but not predicted)
                for missed in actual_signs - predicted_signs:
                    missed_signs[missed] += 1
                
                # False positives (predicted but not actual)
                for false_pos in predicted_signs - actual_signs:
                    false_positives[false_pos] += 1
            
            analysis['sign_errors']['frequently_missed'] = dict(missed_signs.most_common(5))
            analysis['sign_errors']['false_positives'] = dict(false_positives.most_common(5))
        
        # Identify confidence calibration issues
        holder_stats = self.performance_stats["holder_stats"]
        for conf_level, stats in holder_stats.get("confidence_accuracy", {}).items():
            if stats["total"] >= 5:  # Only analyze if we have enough data
                actual_accuracy = stats["correct"] / stats["total"]
                predicted_confidence = conf_level / 100.0
                
                if abs(actual_accuracy - predicted_confidence) > 0.2:  # 20% calibration error
                    analysis['confidence_issues'].append({
                        'confidence_level': conf_level,
                        'predicted_confidence': predicted_confidence,
                        'actual_accuracy': actual_accuracy,
                        'error_type': 'overconfident' if predicted_confidence > actual_accuracy else 'underconfident'
                    })
        
        return analysis
    
    def get_optimization_suggestions(self):
        """Generate optimization suggestions based on error analysis"""
        analysis = self.analyze_errors()
        suggestions = {
            'holder_suggestions': [],
            'sign_suggestions': [],
            'general_suggestions': []
        }
        
        # Holder-specific suggestions
        holder_errors = analysis.get('holder_errors', {})
        if holder_errors.get('material_confusion'):
            most_common = list(holder_errors['material_confusion'].items())[0]
            suggestions['holder_suggestions'].append(
                f"Improve material distinction: {most_common[0]} (confused {most_common[1]} times)"
            )
            suggestions['holder_suggestions'].append(
                "Consider adding more detailed material texture analysis to prompts"
            )
        
        if holder_errors.get('type_confusion'):
            most_common = list(holder_errors['type_confusion'].items())[0]
            suggestions['holder_suggestions'].append(
                f"Improve type classification: {most_common[0]} (confused {most_common[1]} times)"
            )
            suggestions['holder_suggestions'].append(
                "Focus on structural features that distinguish pole types"
            )
        
        # Sign-specific suggestions
        sign_errors = analysis.get('sign_errors', {})
        if sign_errors.get('frequently_missed'):
            missed_signs = list(sign_errors['frequently_missed'].keys())[:3]
            suggestions['sign_suggestions'].append(
                f"Improve detection for frequently missed signs: {', '.join(missed_signs)}"
            )
            suggestions['sign_suggestions'].append(
                "Consider using multi-pass detection for small or partially obscured signs"
            )
        
        if sign_errors.get('false_positives'):
            false_pos = list(sign_errors['false_positives'].keys())[:3]
            suggestions['sign_suggestions'].append(
                f"Reduce false positives for signs: {', '.join(false_pos)}"
            )
            suggestions['sign_suggestions'].append(
                "Add stricter validation criteria for sign detection confidence"
            )
        
        # General suggestions
        confidence_issues = analysis.get('confidence_issues', [])
        if confidence_issues:
            overconfident = [issue for issue in confidence_issues if issue['error_type'] == 'overconfident']
            underconfident = [issue for issue in confidence_issues if issue['error_type'] == 'underconfident']
            
            if overconfident:
                suggestions['general_suggestions'].append(
                    "Calibrate confidence: AI tends to be overconfident - use more conservative confidence scoring"
                )
            if underconfident:
                suggestions['general_suggestions'].append(
                    "Calibrate confidence: AI tends to be underconfident - consider higher confidence for clear cases"
                )
        
        # Add general suggestions based on data volume
        holder_total = self.performance_stats["holder_stats"]["total_processed"]
        sign_total = self.performance_stats["sign_stats"]["total_processed"]
        
        if holder_total < 10:
            suggestions['general_suggestions'].append(
                f"Collect more holder analysis data (currently {holder_total}, aim for 50+)"
            )
        
        if sign_total < 10:
            suggestions['general_suggestions'].append(
                f"Collect more sign detection data (currently {sign_total}, aim for 50+)"
            )
        
        # Performance-based suggestions
        holder_accuracy = self.get_accuracy_report('holder')['accuracy']
        sign_accuracy = self.get_accuracy_report('sign')['accuracy']
        
        if holder_accuracy < 0.7:
            suggestions['holder_suggestions'].append(
                "Consider using more detailed holder analysis prompts or examples"
            )
        
        if sign_accuracy < 0.7:
            suggestions['sign_suggestions'].append(
                "Consider using higher resolution images or multiple analysis passes"
            )
        
        return suggestions
    
    def clear_all_data(self):
        """Clear all learning data and reset the system"""
        try:
            # Reset learning databases
            self.holder_learning_db = {
                "corrections": [],
                "successful_predictions": [],
                "image_patterns": {},
                "confidence_calibration": {},
                "prompt_effectiveness": {}
            }
            
            self.sign_learning_db = {
                "corrections": [],
                "successful_predictions": [],
                "image_patterns": {},
                "confidence_calibration": {},
                "prompt_effectiveness": {}
            }
            
            # Reset performance stats
            self.performance_stats = {
                "holder_stats": {
                    "total_processed": 0,
                    "correct_predictions": 0,
                    "accuracy_history": [],
                    "confidence_accuracy": {}
                },
                "sign_stats": {
                    "total_processed": 0,
                    "correct_predictions": 0,
                    "accuracy_history": [],
                    "sign_detection_accuracy": {}
                }
            }
            
            # Reset common mistakes
            self.common_mistakes = {
                "holder_mistakes": {},
                "sign_mistakes": {},
                "confusion_matrix": {}
            }
            
            # Save the cleared data
            success = self.save_learning_data()
            
            # Also remove the physical files to ensure clean slate
            import glob
            data_files = glob.glob(os.path.join(self.data_path, "*.json"))
            for file_path in data_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"⚠️ Could not remove {file_path}: {e}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error clearing learning data: {e}")
            return False

if __name__ == "__main__":
    # Test the learning system
    learning_system = LearningSystem()
    
    # Simulate some learning data
    print("🧪 Testing learning system...")
    
    # Record some holder predictions
    learning_system.record_holder_prediction(
        holder_id="1843",
        image_url="https://example.com/1843.png",
        predicted_material="kov",
        predicted_type="stĺp značky samostatný",
        confidence=0.85,
        actual_material="betón",
        actual_type="stĺp značky samostatný",
        user_feedback="Material was wrong - it's concrete, not metal"
    )
    
    # Record some sign predictions
    learning_system.record_sign_prediction(
        holder_id="1843",
        image_url="https://example.com/1843.png", 
        predicted_signs=["223", "319"],
        confidence=0.75,
        actual_signs=["223", "100"],
        user_feedback="Missed the no-entry sign, detected parking sign that wasn't there"
    )
    
    # Run learning session
    insights = learning_system.run_learning_session(None)
    
    print("✅ Learning system test complete!")
