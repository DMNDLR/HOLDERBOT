"""
Form-Aware SmartMap Attribute Validator
Uses actual SmartMap form dropdown values for accurate comparison
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from loguru import logger


@dataclass
class FormMapping:
    """Maps AI analysis results to actual form dropdown values"""
    ai_values: List[str]
    form_value: str
    confidence: float
    notes: str = ""


@dataclass
class AttributeComparison:
    """Data class for attribute comparison results"""
    holder_id: str
    attribute_name: str
    form_value: Optional[str]
    analysis_value: Optional[str]
    suggested_form_value: Optional[str]  # What the AI should select in form
    match: bool
    confidence: float
    notes: str = ""
    image_path: str = ""


class FormAwareValidator:
    """Validator that uses actual SmartMap form values"""
    
    def __init__(self):
        self.learning_data_dir = Path("learning_data/complete_holders")
        self.results_dir = Path("validation_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Actual SmartMap form dropdown values (from your screenshot)
        self.form_values = {
            "material": [
                "kov",           # metal
                "betón",         # concrete
                "drevo",         # wood
                "plast",         # plastic
                "stavba, múr",   # building, wall
                "iný"            # other
            ],
            
            # We'll need to get the actual dropdown values for these too
            "owner": [
                "mesto",         # city (most common from our data)
                "súkromný",      # private
                "štát",          # state
                "iný"            # other
            ],
            
            "type": [
                "stĺp značky samostatný",              # standalone sign post
                "stĺp značky dvojitý",                 # double sign post  
                "stĺp verejného osvetlenia",           # street lighting post
                "svetelné signalizačné zariadenie",    # traffic light
                "stĺp",                                # generic post
                "iný"                                  # other
            ]
            # Street is typically a text input, not dropdown
        }
        
        # AI analysis to form value mappings
        self.ai_to_form_mappings = {
            "material": {
                # AI detects these -> should map to form values
                "aluminum": FormMapping(["aluminum", "metal"], "kov", 0.9, "AI detected aluminum -> kov"),
                "steel": FormMapping(["steel", "metal", "iron"], "kov", 0.9, "AI detected steel -> kov"),
                "metal": FormMapping(["metal"], "kov", 0.8, "AI detected metal -> kov"),
                "concrete": FormMapping(["concrete", "cement"], "betón", 0.9, "AI detected concrete -> betón"),
                "wood": FormMapping(["wood", "wooden"], "drevo", 0.9, "AI detected wood -> drevo"),
                "plastic": FormMapping(["plastic"], "plast", 0.9, "AI detected plastic -> plast"),
                "reflective_sheeting": FormMapping(["reflective", "sheeting"], "kov", 0.7, "Reflective sheeting usually on metal -> kov"),
                # Direct Slovak matches
                "kov": FormMapping(["kov"], "kov", 1.0, "Direct Slovak match"),
                "betón": FormMapping(["betón"], "betón", 1.0, "Direct Slovak match"),
                "drevo": FormMapping(["drevo"], "drevo", 1.0, "Direct Slovak match"),
                "plast": FormMapping(["plast"], "plast", 1.0, "Direct Slovak match"),
            },
            
            "owner": {
                "city": FormMapping(["city", "municipal", "municipality"], "mesto", 0.9, "City/municipal -> mesto"),
                "town": FormMapping(["town"], "mesto", 0.8, "Town -> mesto"),
                "private": FormMapping(["private", "individual"], "súkromný", 0.9, "Private owner"),
                "state": FormMapping(["state", "government"], "štát", 0.9, "Government -> štát"),
                # Direct Slovak matches
                "mesto": FormMapping(["mesto"], "mesto", 1.0, "Direct Slovak match"),
                "súkromný": FormMapping(["súkromný"], "súkromný", 1.0, "Direct Slovak match"),
                "štát": FormMapping(["štát"], "štát", 1.0, "Direct Slovak match"),
            },
            
            "type": {
                # AI English to Slovak form mapping
                "post": FormMapping(["post", "pole"], "stĺp", 0.7, "Generic post type"),
                "sign_post": FormMapping(["sign_post", "traffic_sign_post"], "stĺp značky samostatný", 0.8, "Sign post -> standalone"),
                "light_pole": FormMapping(["light_pole", "lighting_post", "street_light"], "stĺp verejného osvetlenia", 0.9, "Lighting post"),
                "traffic_light": FormMapping(["traffic_light", "signal_light"], "svetelné signalizačné zariadenie", 0.9, "Traffic signal"),
                "round_post": FormMapping(["round_post", "u_channel_post"], "stĺp", 0.7, "Post type -> stĺp"),
                # Direct Slovak matches
                "stĺp": FormMapping(["stĺp"], "stĺp", 0.8, "Generic post"),
                "stĺp značky samostatný": FormMapping(["stĺp značky samostatný"], "stĺp značky samostatný", 1.0, "Direct match"),
                "stĺp značky dvojitý": FormMapping(["stĺp značky dvojitý"], "stĺp značky dvojitý", 1.0, "Direct match"),
                "stĺp verejného osvetlenia": FormMapping(["stĺp verejného osvetlenia"], "stĺp verejného osvetlenia", 1.0, "Direct match"),
                "svetelné signalizačné zariadenie": FormMapping(["svetelné signalizačné zariadenie"], "svetelné signalizačné zariadenie", 1.0, "Direct match"),
            }
        }
        
        logger.info("Form-Aware Validator initialized with actual SmartMap form values")
    
    def validate_and_suggest_form_values(self) -> Dict:
        """Validate existing data and suggest correct form values for AI training"""
        try:
            logger.info("🔍 Starting form-aware validation...")
            
            holder_files = list(self.learning_data_dir.glob("holder_*_learning.json"))
            logger.info(f"Found {len(holder_files)} holder files to validate")
            
            all_comparisons = []
            form_suggestions = defaultdict(list)
            
            for holder_file in holder_files:
                try:
                    comparisons = self.validate_single_holder_with_form_mapping(holder_file)
                    all_comparisons.extend(comparisons)
                    
                    # Collect form suggestions for training
                    for comp in comparisons:
                        if comp.suggested_form_value:
                            form_suggestions[comp.attribute_name].append({
                                'holder_id': comp.holder_id,
                                'ai_detected': comp.analysis_value,
                                'should_select': comp.suggested_form_value,
                                'confidence': comp.confidence,
                                'image_path': comp.image_path
                            })
                            
                except Exception as e:
                    logger.error(f"Error validating {holder_file}: {str(e)}")
                    continue
            
            # Calculate results
            validation_result = self._calculate_form_aware_results(all_comparisons)
            
            # Generate training data
            training_data = self._generate_form_training_data(form_suggestions, validation_result)
            
            # Save everything
            self._save_form_aware_results(validation_result, training_data)
            
            logger.info(f"✅ Form-aware validation completed")
            return {
                'validation_result': validation_result,
                'training_data': training_data,
                'form_suggestions': dict(form_suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error during form-aware validation: {str(e)}")
            raise
    
    def validate_single_holder_with_form_mapping(self, holder_file: Path) -> List[AttributeComparison]:
        """Validate a single holder with form value mapping"""
        try:
            with open(holder_file, 'r', encoding='utf-8') as f:
                holder_data = json.load(f)
            
            holder_id = holder_data.get('holder_id', holder_data.get('main_id', 'unknown'))
            
            # Extract form and analysis attributes
            form_attributes = self._extract_form_attributes(holder_data)
            analysis_attributes = self._extract_analysis_attributes(holder_data)
            
            # Get image path
            image_path = ""
            if 'image_data' in holder_data and 'local_path' in holder_data['image_data']:
                image_path = holder_data['image_data']['local_path']
            
            comparisons = []
            
            # Check each core attribute
            for attr_name in ["owner", "material", "type"]:
                form_value = form_attributes.get(self._get_form_key_for_attribute(attr_name))
                analysis_value = analysis_attributes.get(self._get_analysis_key_for_attribute(attr_name))
                
                # Map AI analysis to suggested form value
                suggested_form_value, confidence, notes = self._map_ai_to_form_value(attr_name, analysis_value)
                
                # Check if form value matches suggested value
                match = False
                if form_value and suggested_form_value:
                    match = form_value.lower() == suggested_form_value.lower()
                    if match:
                        confidence = max(confidence, 0.9)  # Boost confidence for exact matches
                elif not form_value and not analysis_value:
                    match = True
                    confidence = 1.0
                    notes = "Both empty"
                elif not analysis_value:
                    confidence = 0.0
                    notes = "AI analysis missing - needs training"
                
                comparison = AttributeComparison(
                    holder_id=holder_id,
                    attribute_name=attr_name,
                    form_value=form_value,
                    analysis_value=analysis_value,
                    suggested_form_value=suggested_form_value,
                    match=match,
                    confidence=confidence,
                    notes=notes,
                    image_path=image_path
                )
                
                comparisons.append(comparison)
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error validating holder file {holder_file}: {str(e)}")
            return []
    
    def _get_form_key_for_attribute(self, attr_name: str) -> str:
        """Get the form key for an attribute"""
        mapping = {
            "owner": "vlastnik",
            "material": "material", 
            "type": "typ",
            "street": "ulica"
        }
        return mapping.get(attr_name, attr_name)
    
    def _get_analysis_key_for_attribute(self, attr_name: str) -> str:
        """Get the analysis key for an attribute"""
        mapping = {
            "owner": "Vlastník",
            "material": "Materiál", 
            "type": "Základný typ",
            "street": "ulica"
        }
        return mapping.get(attr_name, attr_name)
    
    def _extract_form_attributes(self, holder_data: Dict) -> Dict[str, str]:
        """Extract form attributes (actual values from SmartMap)"""
        form_attributes = {}
        
        # From holder_data.attributes (table data)
        if 'holder_data' in holder_data and 'attributes' in holder_data['holder_data']:
            attrs = holder_data['holder_data']['attributes']
            for key, value in attrs.items():
                if value:
                    form_attributes[key] = str(value).strip()
        
        # From form_attributes (edit form data)
        if 'form_attributes' in holder_data:
            for key, value in holder_data['form_attributes'].items():
                if value:
                    form_attributes[key] = str(value).strip()
        
        return form_attributes
    
    def _extract_analysis_attributes(self, holder_data: Dict) -> Dict[str, str]:
        """Extract AI analysis attributes"""
        analysis_attributes = {}
        
        # From various analysis sources
        sources = [
            'analysis_results',
            'slovak_analysis', 
            'visual_analysis'
        ]
        
        for source in sources:
            if source in holder_data:
                data = holder_data[source]
                if isinstance(data, dict):
                    for key, value in data.items():
                        if value:
                            analysis_attributes[key] = str(value).strip()
        
        # From training_pair
        if 'training_pair' in holder_data and 'visual_prediction' in holder_data['training_pair']:
            prediction = holder_data['training_pair']['visual_prediction']
            if isinstance(prediction, dict):
                for key, value in prediction.items():
                    if value:
                        analysis_attributes[key] = str(value).strip()
        
        return analysis_attributes
    
    def _map_ai_to_form_value(self, attr_name: str, ai_value: Optional[str]) -> Tuple[Optional[str], float, str]:
        """Map AI analysis value to correct SmartMap form value"""
        
        if not ai_value:
            return None, 0.0, "AI analysis missing"
        
        ai_lower = ai_value.lower().strip()
        
        if attr_name in self.ai_to_form_mappings:
            mappings = self.ai_to_form_mappings[attr_name]
            
            # Check for exact matches first
            if ai_lower in mappings:
                mapping = mappings[ai_lower]
                return mapping.form_value, mapping.confidence, mapping.notes
            
            # Check for partial matches
            for ai_pattern, mapping in mappings.items():
                if ai_pattern in ai_lower or ai_lower in ai_pattern:
                    confidence = mapping.confidence * 0.8  # Reduce confidence for partial match
                    return mapping.form_value, confidence, f"Partial match: {mapping.notes}"
                    
                # Check if AI value is in the mapping's AI values list
                for ai_val in mapping.ai_values:
                    if ai_val.lower() in ai_lower:
                        confidence = mapping.confidence * 0.9
                        return mapping.form_value, confidence, f"Pattern match: {mapping.notes}"
        
        return None, 0.0, f"No mapping found for AI value: {ai_value}"
    
    def _calculate_form_aware_results(self, comparisons: List[AttributeComparison]) -> Dict:
        """Calculate results with form-aware metrics"""
        
        total_comparisons = len(comparisons)
        if total_comparisons == 0:
            return {'error': 'No comparisons found'}
        
        # Count different types of results
        exact_matches = sum(1 for c in comparisons if c.match and c.confidence >= 0.9)
        partial_matches = sum(1 for c in comparisons if c.match and 0.5 <= c.confidence < 0.9)
        no_matches = sum(1 for c in comparisons if not c.match)
        missing_ai = sum(1 for c in comparisons if not c.analysis_value)
        
        # Calculate accuracy
        total_accuracy = sum(c.confidence if c.match else 0.0 for c in comparisons)
        accuracy_percentage = (total_accuracy / total_comparisons) * 100
        
        # Attribute-specific accuracy
        attribute_accuracy = {}
        attributes = defaultdict(list)
        
        for comparison in comparisons:
            attributes[comparison.attribute_name].append(comparison)
        
        for attr_name, attr_comparisons in attributes.items():
            attr_accuracy = sum(c.confidence if c.match else 0.0 for c in attr_comparisons)
            attr_accuracy_pct = (attr_accuracy / len(attr_comparisons)) * 100
            attribute_accuracy[attr_name] = attr_accuracy_pct
        
        return {
            'total_holders': len(set(c.holder_id for c in comparisons)),
            'total_comparisons': total_comparisons,
            'exact_matches': exact_matches,
            'partial_matches': partial_matches,
            'no_matches': no_matches,
            'missing_ai_analysis': missing_ai,
            'accuracy_percentage': accuracy_percentage,
            'attribute_accuracy': attribute_accuracy,
            'comparisons': comparisons
        }
    
    def _generate_form_training_data(self, form_suggestions: Dict, validation_result: Dict) -> Dict:
        """Generate training data for improving AI to match form values"""
        
        training_data = {
            'timestamp': time.strftime("%Y%m%d_%H%M%S"),
            'form_value_mappings': self.form_values,
            'ai_to_form_mappings': {},
            'training_recommendations': [],
            'missing_analysis_count': validation_result.get('missing_ai_analysis', 0),
            'suggested_improvements': []
        }
        
        # Convert form suggestions to training mappings
        for attr_name, suggestions in form_suggestions.items():
            if suggestions:
                training_data['ai_to_form_mappings'][attr_name] = suggestions
        
        # Generate specific recommendations
        for attr_name, accuracy in validation_result.get('attribute_accuracy', {}).items():
            if accuracy < 50:
                training_data['training_recommendations'].append({
                    'attribute': attr_name,
                    'current_accuracy': accuracy,
                    'priority': 'HIGH',
                    'action': f'Retrain AI to detect {attr_name} and map to form values: {self.form_values.get(attr_name, [])}',
                    'available_form_values': self.form_values.get(attr_name, [])
                })
        
        # Specific improvement suggestions
        if validation_result.get('missing_ai_analysis', 0) > 20:
            training_data['suggested_improvements'].append({
                'issue': 'Many holders have missing AI analysis',
                'solution': 'Improve image analysis to always return values',
                'affected_holders': validation_result.get('missing_ai_analysis', 0)
            })
        
        return training_data
    
    def _save_form_aware_results(self, validation_result: Dict, training_data: Dict):
        """Save form-aware validation results"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save validation results
        results_file = self.results_dir / f"form_aware_validation_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            # Convert comparisons to serializable format
            serializable_result = dict(validation_result)
            if 'comparisons' in serializable_result:
                serializable_result['comparisons'] = [
                    {
                        'holder_id': c.holder_id,
                        'attribute_name': c.attribute_name,
                        'form_value': c.form_value,
                        'analysis_value': c.analysis_value,
                        'suggested_form_value': c.suggested_form_value,
                        'match': c.match,
                        'confidence': c.confidence,
                        'notes': c.notes,
                        'image_path': c.image_path
                    }
                    for c in serializable_result['comparisons']
                ]
            
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Form-aware validation saved: {results_file}")
        
        # Save training data
        training_file = self.results_dir / f"form_training_data_{timestamp}.json"
        with open(training_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"🎯 Training data saved: {training_file}")
        
        # Save human-readable summary
        self._save_form_summary_report(validation_result, training_data, timestamp)
    
    def _save_form_summary_report(self, validation_result: Dict, training_data: Dict, timestamp: str):
        """Save human-readable summary of form-aware validation"""
        report_file = self.results_dir / f"form_aware_summary_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🔍 Form-Aware SmartMap Validation Report\n")
            f.write("=" * 55 + "\n\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Total Holders: {validation_result.get('total_holders', 0)}\n")
            f.write(f"Total Comparisons: {validation_result.get('total_comparisons', 0)}\n\n")
            
            f.write("📊 FORM-AWARE RESULTS:\n")
            f.write(f"  • Overall Accuracy: {validation_result.get('accuracy_percentage', 0):.1f}%\n")
            f.write(f"  • Exact Matches: {validation_result.get('exact_matches', 0)}\n")
            f.write(f"  • Partial Matches: {validation_result.get('partial_matches', 0)}\n") 
            f.write(f"  • No Matches: {validation_result.get('no_matches', 0)}\n")
            f.write(f"  • Missing AI Analysis: {validation_result.get('missing_ai_analysis', 0)}\n\n")
            
            f.write("📋 ATTRIBUTE ACCURACY (Form-Aware):\n")
            for attr_name, accuracy in sorted(validation_result.get('attribute_accuracy', {}).items(), key=lambda x: x[1], reverse=True):
                f.write(f"  • {attr_name}: {accuracy:.1f}%\n")
            
            f.write("\n🎯 SMARTMAP FORM VALUES:\n")
            for attr_name, form_values in self.form_values.items():
                f.write(f"  • {attr_name}: {', '.join(form_values)}\n")
            
            f.write("\n💡 TRAINING RECOMMENDATIONS:\n")
            for rec in training_data.get('training_recommendations', []):
                f.write(f"  • {rec['attribute']} ({rec['current_accuracy']:.1f}%): {rec['action']}\n")
        
        logger.info(f"📄 Form-aware summary saved: {report_file}")


def main():
    """Main function to run form-aware validation"""
    print("🔍 Form-Aware SmartMap Validator")
    print("=" * 45)
    print("Using actual SmartMap form dropdown values...\n")
    
    validator = FormAwareValidator()
    
    try:
        # Run validation
        results = validator.validate_and_suggest_form_values()
        
        validation_result = results['validation_result']
        training_data = results['training_data']
        
        # Print summary
        print("📊 FORM-AWARE VALIDATION RESULTS:")
        print(f"  Total Holders: {validation_result.get('total_holders', 0)}")
        print(f"  Total Comparisons: {validation_result.get('total_comparisons', 0)}")
        print(f"  Overall Accuracy: {validation_result.get('accuracy_percentage', 0):.1f}%")
        print(f"  Missing AI Analysis: {validation_result.get('missing_ai_analysis', 0)}")
        
        print("\n📋 Attribute Accuracy (with form mapping):")
        for attr_name, accuracy in sorted(validation_result.get('attribute_accuracy', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"  • {attr_name}: {accuracy:.1f}%")
        
        print("\n🎯 SmartMap Form Values:")
        for attr_name, form_values in validator.form_values.items():
            print(f"  • {attr_name}: {', '.join(form_values)}")
        
        print("\n✅ Form-aware results saved to validation_results/ folder")
        print("🎯 Training data generated for AI improvement")
        
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        raise


if __name__ == "__main__":
    main()
