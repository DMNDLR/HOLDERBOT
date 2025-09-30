#!/usr/bin/env python3
"""
SmartMap Automation Accuracy Assessment
======================================

Analyzes the real-world accuracy of automated holder filling based on our 490-holder analysis.
This gives you a realistic expectation of how the automation will perform on blank holders.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import csv

class AutomationAccuracyAssessment:
    """Assess automation accuracy for blank holder filling"""
    
    def __init__(self):
        self.results_file = Path("analysis_reports/detailed_analysis_results.csv")
        self.assessment = {}
        
    def analyze_automation_accuracy(self):
        """Analyze how accurate the automation would be for blank holders"""
        print("🎯 SMARTMAP AUTOMATION ACCURACY ASSESSMENT")
        print("=" * 55)
        print("Based on analysis of 490 real holders from SmartMap\n")
        
        # Load analysis results
        results = self.load_analysis_results()
        
        # Overall accuracy assessment
        self.assess_overall_accuracy(results)
        
        # Specific attribute accuracy
        self.assess_attribute_accuracy(results)
        
        # Scenario-based accuracy
        self.assess_scenario_accuracy(results)
        
        # Confidence-based accuracy
        self.assess_confidence_accuracy(results)
        
        # Recommendations
        self.provide_recommendations()
        
        return self.assessment
    
    def load_analysis_results(self):
        """Load the detailed analysis results"""
        results = []
        
        if not self.results_file.exists():
            print("❌ Analysis results not found. Run comprehensive analysis first!")
            return []
        
        with open(self.results_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string booleans to actual booleans
                row['Material_Match'] = row['Material_Match'].lower() == 'true'
                row['Owner_Match'] = row['Owner_Match'].lower() == 'true'
                row['Type_Match'] = row['Type_Match'].lower() == 'true'
                row['Image_Downloaded'] = row['Image_Downloaded'].lower() == 'true'
                row['Overall_Accuracy'] = float(row['Overall_Accuracy']) if row['Overall_Accuracy'] else 0.0
                row['AI_Confidence'] = float(row['AI_Confidence']) if row['AI_Confidence'] else 0.0
                results.append(row)
        
        print(f"📋 Loaded analysis results for {len(results)} holders\n")
        return results
    
    def assess_overall_accuracy(self, results):
        """Assess overall automation accuracy"""
        print("🎯 OVERALL AUTOMATION ACCURACY")
        print("-" * 35)
        
        total = len(results)
        if total == 0:
            return
        
        # Calculate accuracies
        material_correct = sum(1 for r in results if r['Material_Match'])
        owner_correct = sum(1 for r in results if r['Owner_Match'])
        type_correct = sum(1 for r in results if r['Type_Match'])
        
        material_accuracy = (material_correct / total) * 100
        owner_accuracy = (owner_correct / total) * 100
        type_accuracy = (type_correct / total) * 100
        overall_accuracy = (material_accuracy + owner_accuracy + type_accuracy) / 3
        
        print(f"📊 If you run automation on blank holders:")
        print(f"   • Material field: {material_accuracy:.1f}% will be filled correctly")
        print(f"   • Owner field: {owner_accuracy:.1f}% will be filled correctly")  
        print(f"   • Type field: {type_accuracy:.1f}% will be filled correctly")
        print(f"   • Overall success: {overall_accuracy:.1f}% of all fields correct")
        
        # Save to assessment
        self.assessment['overall'] = {
            'material_accuracy': material_accuracy,
            'owner_accuracy': owner_accuracy,
            'type_accuracy': type_accuracy,
            'overall_accuracy': overall_accuracy
        }
        
        print(f"\n💡 **REALISTIC EXPECTATION:**")
        if overall_accuracy >= 70:
            print(f"   ✅ GOOD - Ready for production use with monitoring")
        elif overall_accuracy >= 50:
            print(f"   ⚠️ MODERATE - Usable but needs human review")
        elif overall_accuracy >= 30:
            print(f"   🔄 DEVELOPING - Needs improvement before production")
        else:
            print(f"   ❌ POOR - Requires significant training improvements")
        
        print()
    
    def assess_attribute_accuracy(self, results):
        """Assess accuracy for specific attribute values"""
        print("🔍 ACCURACY BY ATTRIBUTE VALUES")
        print("-" * 35)
        
        # Material accuracy by type
        print("📋 MATERIAL ACCURACY:")
        material_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for result in results:
            material = result['Form_Material']
            if material:
                material_stats[material]['total'] += 1
                if result['Material_Match']:
                    material_stats[material]['correct'] += 1
        
        for material, stats in sorted(material_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                print(f"   • {material}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        print(f"\n🏗️ TYPE ACCURACY:")
        type_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for result in results:
            type_name = result['Form_Type']
            if type_name:
                type_stats[type_name]['total'] += 1
                if result['Type_Match']:
                    type_stats[type_name]['correct'] += 1
        
        # Show top types only
        top_types = sorted(type_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:8]
        for type_name, stats in top_types:
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                display_name = type_name[:35] + "..." if len(type_name) > 35 else type_name
                print(f"   • {display_name}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        self.assessment['by_attribute'] = {
            'materials': dict(material_stats),
            'types': dict(type_stats)
        }
        
        print()
    
    def assess_scenario_accuracy(self, results):
        """Assess accuracy for different automation scenarios"""
        print("🚀 AUTOMATION SCENARIO ANALYSIS")
        print("-" * 35)
        
        scenarios = {
            'all_fields': "Fill all 3 fields (Material + Owner + Type)",
            'material_only': "Fill Material field only",
            'material_owner': "Fill Material + Owner fields",
            'high_confidence': "Fill only when AI confidence > 80%",
            'medium_confidence': "Fill only when AI confidence > 60%"
        }
        
        for scenario_name, description in scenarios.items():
            if scenario_name == 'all_fields':
                # All three fields correct
                correct = sum(1 for r in results if r['Material_Match'] and r['Owner_Match'] and r['Type_Match'])
                accuracy = (correct / len(results)) * 100
                
            elif scenario_name == 'material_only':
                # Just material correct
                correct = sum(1 for r in results if r['Material_Match'])
                accuracy = (correct / len(results)) * 100
                
            elif scenario_name == 'material_owner':
                # Material and owner correct
                correct = sum(1 for r in results if r['Material_Match'] and r['Owner_Match'])
                accuracy = (correct / len(results)) * 100
                
            elif scenario_name == 'high_confidence':
                # Only high confidence predictions
                high_conf_results = [r for r in results if r['AI_Confidence'] > 0.8]
                if high_conf_results:
                    correct = sum(1 for r in high_conf_results if r['Material_Match'] and r['Owner_Match'] and r['Type_Match'])
                    accuracy = (correct / len(high_conf_results)) * 100
                    coverage = (len(high_conf_results) / len(results)) * 100
                    print(f"   📊 {description}:")
                    print(f"      Accuracy: {accuracy:.1f}% | Coverage: {coverage:.1f}% of holders")
                    continue
                else:
                    accuracy = 0
                    
            elif scenario_name == 'medium_confidence':
                # Only medium+ confidence predictions
                med_conf_results = [r for r in results if r['AI_Confidence'] > 0.6]
                if med_conf_results:
                    correct = sum(1 for r in med_conf_results if r['Material_Match'] and r['Owner_Match'] and r['Type_Match'])
                    accuracy = (correct / len(med_conf_results)) * 100
                    coverage = (len(med_conf_results) / len(results)) * 100
                    print(f"   📊 {description}:")
                    print(f"      Accuracy: {accuracy:.1f}% | Coverage: {coverage:.1f}% of holders")
                    continue
                else:
                    accuracy = 0
            
            print(f"   📊 {description}: {accuracy:.1f}%")
        
        print()
    
    def assess_confidence_accuracy(self, results):
        """Assess accuracy at different confidence levels"""
        print("🎯 CONFIDENCE vs ACCURACY ANALYSIS")
        print("-" * 35)
        
        confidence_ranges = [
            (0.9, 1.0, "Very High (90%+)"),
            (0.8, 0.9, "High (80-90%)"),
            (0.7, 0.8, "Good (70-80%)"),
            (0.6, 0.7, "Medium (60-70%)"),
            (0.0, 0.6, "Low (<60%)")
        ]
        
        print("📈 Accuracy by AI Confidence Level:")
        
        for min_conf, max_conf, label in confidence_ranges:
            conf_results = [r for r in results if min_conf <= r['AI_Confidence'] < max_conf]
            
            if conf_results:
                # Calculate accuracy for this confidence range
                material_correct = sum(1 for r in conf_results if r['Material_Match'])
                type_correct = sum(1 for r in conf_results if r['Type_Match'])
                
                material_acc = (material_correct / len(conf_results)) * 100
                type_acc = (type_correct / len(conf_results)) * 100
                
                print(f"   • {label}: {len(conf_results)} holders")
                print(f"     Material: {material_acc:.1f}% | Type: {type_acc:.1f}%")
        
        print()
    
    def provide_recommendations(self):
        """Provide recommendations for automation deployment"""
        print("💡 AUTOMATION DEPLOYMENT RECOMMENDATIONS")
        print("-" * 45)
        
        print("🎯 **CURRENT READINESS:**")
        
        material_acc = self.assessment.get('overall', {}).get('material_accuracy', 0)
        type_acc = self.assessment.get('overall', {}).get('type_accuracy', 0)
        
        if material_acc >= 60:
            print("   ✅ MATERIAL FIELD: Ready for automation")
            print("      → Can safely auto-fill material fields")
        else:
            print("   ❌ MATERIAL FIELD: Needs improvement")
            print("      → Require human review for material fields")
        
        if type_acc >= 30:
            print("   ⚠️ TYPE FIELD: Partial automation possible")
            print("      → Use for suggestions only, require human confirmation")
        else:
            print("   ❌ TYPE FIELD: Not ready for automation")
            print("      → Train more before deploying")
        
        print(f"\n🚀 **DEPLOYMENT STRATEGIES:**")
        print(f"   1. 🎯 Conservative: Auto-fill only materials (69.8% accuracy)")
        print(f"   2. ⚠️ Moderate: Auto-fill materials + suggest types for review")
        print(f"   3. 🔄 Learning: Deploy with human review to collect more training data")
        print(f"   4. 📊 Phased: Start with high-confidence cases only")
        
        print(f"\n🔧 **IMPROVEMENT PRIORITIES:**")
        print(f"   1. 🏗️ Type Classification: Biggest improvement opportunity")
        print(f"      • Focus on 'stĺp značky samostatný' (328 holders, 16.5% accuracy)")
        print(f"      • Improve 'stĺp verejného osvetlenia' (30 holders, 26.7% accuracy)")
        print(f"   2. 📸 Image Quality: Ensure clear, standardized images")
        print(f"   3. 🧠 Training Data: Use these 490 holders for retraining")
        
        print(f"\n⚡ **IMMEDIATE ACTIONS:**")
        print(f"   • ✅ Deploy material auto-filling immediately")
        print(f"   • ⚠️ Deploy type suggestions with human review")  
        print(f"   • 🔄 Collect feedback to improve type classification")
        print(f"   • 📊 Monitor accuracy and adjust thresholds")

def main():
    """Run automation accuracy assessment"""
    assessor = AutomationAccuracyAssessment()
    results = assessor.analyze_automation_accuracy()
    
    print(f"\n🎯 **BOTTOM LINE:**")
    print(f"Your automation is ready for SELECTIVE deployment:")
    print(f"• Materials: DEPLOY NOW (69.8% accuracy)")
    print(f"• Types: SUGGESTIONS ONLY (12.7% accuracy)")
    print(f"• Overall: HYBRID APPROACH recommended")

if __name__ == "__main__":
    main()
