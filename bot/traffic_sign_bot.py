"""
Main Traffic Sign Automation Bot
Combines web automation and image analysis for GIS traffic sign data entry
"""

import os
import sys
import time
from typing import Dict, List, Optional
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from src.web_automation import GISWebAutomation
from src.image_analysis import TrafficSignAnalyzer
from config.config import Config, TrafficSignAttributes
from loguru import logger


class TrafficSignBot:
    """
    Main bot class that orchestrates the entire workflow:
    1. Analyze traffic sign images
    2. Login to GIS website
    3. Fill attribute forms with analyzed data
    4. Save and process multiple signs
    """
    
    def __init__(self):
        self.web_automation = None
        self.image_analyzer = None
        self.logger = logger
        
        # Configure logging
        self.logger.add(Config.LOG_FILE, rotation="10 MB", level=Config.LOG_LEVEL)
        self.logger.info("Traffic Sign Bot initialized")
        
        # Validate configuration
        if not Config.validate_config():
            raise ValueError("Invalid configuration. Please check your .env file.")
    
    def initialize(self) -> bool:
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing Traffic Sign Bot...")
            
            # Initialize web automation
            self.web_automation = GISWebAutomation()
            if not self.web_automation.setup_browser():
                self.logger.error("Failed to setup browser")
                return False
            
            # Initialize image analyzer
            self.image_analyzer = TrafficSignAnalyzer()
            
            self.logger.info("Bot initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {str(e)}")
            return False
    
    def login_to_system(self) -> bool:
        """Login to the GIS system"""
        try:
            self.logger.info("Logging into GIS system...")
            
            # Login to WordPress
            if not self.web_automation.login_to_wordpress():
                self.logger.error("WordPress login failed")
                return False
            
            # Navigate to GIS admin
            if not self.web_automation.navigate_to_gis_admin():
                self.logger.error("Failed to navigate to GIS admin")
                return False
            
            self.logger.info("Successfully logged into GIS system")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
    
    def process_single_image(self, image_path: str, manual_override: Dict = None) -> bool:
        """
        Process a single traffic sign image
        
        Args:
            image_path: Path to the traffic sign image
            manual_override: Manual corrections to analysis results
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Processing image: {image_path}")
            
            # Validate image
            if not self.image_analyzer.validate_image(image_path):
                self.logger.error(f"Invalid image: {image_path}")
                return False
            
            # Analyze image
            analysis_results = self.image_analyzer.analyze_image(image_path)
            if not analysis_results:
                self.logger.error("Image analysis failed")
                return False
            
            # Apply manual overrides if provided
            if manual_override:
                self.logger.info("Applying manual overrides...")
                analysis_results.update(manual_override)
            
            # Get confidence scores
            confidence = self.image_analyzer.get_analysis_confidence(analysis_results)
            self.logger.info(f"Analysis confidence: {confidence}")
            
            # Find traffic sign element on the web page
            sign_element = self.web_automation.find_traffic_sign_element(image_path)
            if not sign_element:
                self.logger.warning("No traffic sign element found on page")
                # Continue anyway - might be able to fill form directly
            
            # Fill the attribute form
            success = self.web_automation.fill_attribute_form(analysis_results)
            if not success:
                self.logger.error("Failed to fill attribute form")
                return False
            
            # Save the form
            if not self.web_automation.save_form():
                self.logger.warning("Failed to save form - may need manual intervention")
            
            self.logger.info(f"Successfully processed image: {image_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")
            return False
    
    def process_image_batch(self, image_folder: str, output_report: str = None) -> Dict:
        """
        Process multiple traffic sign images in a folder
        
        Args:
            image_folder: Path to folder containing images
            output_report: Path for processing report
            
        Returns:
            Dict: Processing results and statistics
        """
        try:
            self.logger.info(f"Starting batch processing: {image_folder}")
            
            if not os.path.exists(image_folder):
                raise ValueError(f"Image folder not found: {image_folder}")
            
            # Get all valid images
            supported_formats = tuple(f".{fmt.lower()}" for fmt in Config.SUPPORTED_FORMATS)
            image_files = [
                f for f in os.listdir(image_folder)
                if f.lower().endswith(supported_formats)
            ]
            
            if not image_files:
                self.logger.warning("No valid images found in folder")
                return {'processed': 0, 'failed': 0, 'total': 0}
            
            self.logger.info(f"Found {len(image_files)} images to process")
            
            # Process each image
            processed = 0
            failed = 0
            results = {}
            
            for image_file in image_files:
                image_path = os.path.join(image_folder, image_file)
                
                try:
                    success = self.process_single_image(image_path)
                    if success:
                        processed += 1
                        results[image_file] = 'SUCCESS'
                    else:
                        failed += 1
                        results[image_file] = 'FAILED'
                        
                    # Small delay between processing to avoid overwhelming the server
                    time.sleep(2)
                    
                except Exception as e:
                    failed += 1
                    results[image_file] = f'ERROR: {str(e)}'
                    self.logger.error(f"Error processing {image_file}: {str(e)}")
            
            # Generate report
            report_data = {
                'processed': processed,
                'failed': failed,
                'total': len(image_files),
                'success_rate': (processed / len(image_files)) * 100 if image_files else 0,
                'results': results
            }
            
            # Save report if requested
            if output_report:
                self._save_processing_report(report_data, output_report)
            
            self.logger.info(f"Batch processing completed: {processed}/{len(image_files)} successful")
            return report_data
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            return {'processed': 0, 'failed': 0, 'total': 0, 'error': str(e)}
    
    def interactive_mode(self):
        """Run the bot in interactive mode for manual control"""
        try:
            self.logger.info("Starting interactive mode...")
            print("=== Traffic Sign Bot - Interactive Mode ===")
            print("Commands:")
            print("1. process <image_path> - Process single image")
            print("2. batch <folder_path> - Process folder of images") 
            print("3. screenshot - Take screenshot of current page")
            print("4. analyze <image_path> - Analyze image without web automation")
            print("5. quit - Exit the bot")
            print()
            
            while True:
                try:
                    command = input("Enter command: ").strip().split()
                    
                    if not command:
                        continue
                    
                    action = command[0].lower()
                    
                    if action == 'quit':
                        break
                    
                    elif action == 'process' and len(command) > 1:
                        image_path = ' '.join(command[1:])
                        self.process_single_image(image_path)
                    
                    elif action == 'batch' and len(command) > 1:
                        folder_path = ' '.join(command[1:])
                        results = self.process_image_batch(folder_path)
                        print(f"Batch results: {results}")
                    
                    elif action == 'screenshot':
                        if self.web_automation:
                            screenshot_path = self.web_automation.take_screenshot()
                            print(f"Screenshot saved: {screenshot_path}")
                        else:
                            print("Web automation not initialized")
                    
                    elif action == 'analyze' and len(command) > 1:
                        image_path = ' '.join(command[1:])
                        results = self.image_analyzer.analyze_image(image_path)
                        print(f"Analysis results: {results}")
                    
                    else:
                        print("Invalid command. Type 'quit' to exit.")
                
                except KeyboardInterrupt:
                    print("\\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            self.logger.info("Interactive mode ended")
            
        except Exception as e:
            self.logger.error(f"Interactive mode error: {str(e)}")
    
    def _save_processing_report(self, report_data: Dict, output_path: str):
        """Save processing report to file"""
        try:
            import json
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            self.logger.info(f"Processing report saved: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {str(e)}")
    
    def cleanup(self):
        """Clean up bot resources"""
        try:
            if self.web_automation:
                self.web_automation.cleanup()
            self.logger.info("Bot cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Convenience functions for quick usage
def analyze_image(image_path: str) -> Dict:
    """Quick function to analyze a single image"""
    analyzer = TrafficSignAnalyzer()
    return analyzer.analyze_image(image_path)


def process_image_with_bot(image_path: str, manual_override: Dict = None) -> bool:
    """Quick function to process a single image with full bot"""
    with TrafficSignBot() as bot:
        if bot.login_to_system():
            return bot.process_single_image(image_path, manual_override)
    return False


def batch_process_folder(folder_path: str, output_report: str = None) -> Dict:
    """Quick function to batch process a folder"""
    with TrafficSignBot() as bot:
        if bot.login_to_system():
            return bot.process_image_batch(folder_path, output_report)
    return {'error': 'Failed to initialize bot or login'}


if __name__ == "__main__":
    # Example usage when running the script directly
    print("Traffic Sign Bot - Starting...")
    
    # Check if image path provided as command line argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        
        if os.path.isfile(image_path):
            print(f"Processing single image: {image_path}")
            result = process_image_with_bot(image_path)
            print(f"Result: {'Success' if result else 'Failed'}")
            
        elif os.path.isdir(image_path):
            print(f"Processing folder: {image_path}")
            results = batch_process_folder(image_path, f"{image_path}/processing_report.json")
            print(f"Batch processing results: {results}")
            
        else:
            print(f"Invalid path: {image_path}")
    
    else:
        # Run in interactive mode
        with TrafficSignBot() as bot:
            if bot.login_to_system():
                bot.interactive_mode()
            else:
                print("Failed to initialize bot or login to system")
