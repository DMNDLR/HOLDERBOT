"""
Example Usage Script for Traffic Sign Automation Bot
Demonstrates different ways to use the bot
"""

import os
from bot.traffic_sign_bot import TrafficSignBot, analyze_image, process_image_with_bot
from src.image_analysis import TrafficSignAnalyzer


def example_single_image_analysis():
    """Example: Analyze a single image without web automation"""
    print("=== Example 1: Single Image Analysis ===")
    
    # You can test this with any traffic sign image
    # For now, we'll create a dummy path - replace with real image path
    image_path = "./images/traffic_sign_1.jpg"
    
    if os.path.exists(image_path):
        print(f"Analyzing image: {image_path}")
        
        # Method 1: Using the convenience function
        results = analyze_image(image_path)
        print(f"Analysis results: {results}")
        
        # Method 2: Using the analyzer directly
        analyzer = TrafficSignAnalyzer()
        confidence = analyzer.get_analysis_confidence(results)
        print(f"Confidence scores: {confidence}")
        
    else:
        print(f"Image not found: {image_path}")
        print("Please add a traffic sign image to the images folder to test this example")


def example_full_automation():
    """Example: Full automation with web interface"""
    print("\\n=== Example 2: Full Automation ===")
    
    image_path = "./images/traffic_sign_1.jpg"
    
    if os.path.exists(image_path):
        print(f"Processing image with full automation: {image_path}")
        
        # Optional: Manual overrides if the analysis is wrong
        manual_overrides = {
            'material': 'aluminum',  # Override if analysis detected wrong material
            'condition': 'good'      # Override if analysis detected wrong condition
        }
        
        # Process with the bot
        success = process_image_with_bot(image_path, manual_overrides)
        print(f"Processing result: {'Success' if success else 'Failed'}")
        
    else:
        print(f"Image not found: {image_path}")
        print("Please add a traffic sign image to test this example")


def example_batch_processing():
    """Example: Batch process multiple images"""
    print("\\n=== Example 3: Batch Processing ===")
    
    images_folder = "./images"
    
    if os.path.exists(images_folder):
        with TrafficSignBot() as bot:
            if bot.login_to_system():
                results = bot.process_image_batch(
                    image_folder=images_folder,
                    output_report="./logs/batch_report.json"
                )
                
                print(f"Batch processing results:")
                print(f"- Total images: {results.get('total', 0)}")
                print(f"- Successfully processed: {results.get('processed', 0)}")
                print(f"- Failed: {results.get('failed', 0)}")
                print(f"- Success rate: {results.get('success_rate', 0):.1f}%")
            else:
                print("Failed to login to the system")
    else:
        print(f"Images folder not found: {images_folder}")


def example_interactive_mode():
    """Example: Interactive mode for manual control"""
    print("\\n=== Example 4: Interactive Mode ===")
    print("This will start the bot in interactive mode...")
    print("Note: You need to configure your .env file first!")
    
    try:
        with TrafficSignBot() as bot:
            if bot.login_to_system():
                print("Bot initialized successfully!")
                print("Starting interactive mode...")
                bot.interactive_mode()
            else:
                print("Failed to initialize bot or login")
                print("Please check your configuration in the .env file")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure you have configured the .env file with your website details")


def example_configuration_check():
    """Example: Check if configuration is valid"""
    print("=== Configuration Check ===")
    
    from config.config import Config
    
    print("Checking configuration...")
    
    required_configs = [
        ('SITE_URL', Config.SITE_URL),
        ('LOGIN_URL', Config.LOGIN_URL),
        ('USERNAME', Config.USERNAME),
        ('PASSWORD', '***' if Config.PASSWORD else ''),
        ('GIS_ADMIN_URL', Config.GIS_ADMIN_URL)
    ]
    
    print("\\nConfiguration status:")
    all_configured = True
    
    for name, value in required_configs:
        status = "✓ Configured" if value else "✗ Missing"
        if not value:
            all_configured = False
        print(f"  {name}: {status}")
    
    print(f"\\nOverall status: {'✓ Ready to use' if all_configured else '✗ Needs configuration'}")
    
    if not all_configured:
        print("\\nTo configure the bot:")
        print("1. Edit the .env file in the project root")
        print("2. Fill in your website URL, login credentials, and GIS admin URL")
        print("3. Save the file and try again")
    
    return all_configured


def create_sample_image():
    """Create a simple sample image for testing (if OpenCV available)"""
    try:
        import cv2
        import numpy as np
        
        # Create a simple traffic sign-like image
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255  # White background
        
        # Draw a red circle (stop sign like)
        cv2.circle(img, (200, 200), 150, (0, 0, 255), -1)  # Red circle
        cv2.circle(img, (200, 200), 150, (0, 0, 0), 5)     # Black border
        
        # Add some text
        cv2.putText(img, "STOP", (150, 210), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Save the sample image
        os.makedirs("images", exist_ok=True)
        sample_path = "./images/sample_traffic_sign.jpg"
        cv2.imwrite(sample_path, img)
        
        print(f"Created sample image: {sample_path}")
        return sample_path
        
    except ImportError:
        print("OpenCV not available - cannot create sample image")
        return None
    except Exception as e:
        print(f"Error creating sample image: {str(e)}")
        return None


def main():
    """Main function demonstrating all examples"""
    print("Traffic Sign Automation Bot - Example Usage\\n")
    
    # Check configuration first
    config_ok = example_configuration_check()
    
    # Create a sample image if none exists
    if not os.path.exists("./images") or not os.listdir("./images"):
        print("\\nNo images found. Creating sample image...")
        create_sample_image()
    
    print("\\n" + "="*50)
    print("Choose an example to run:")
    print("1. Single image analysis only")
    print("2. Full automation (requires configuration)")
    print("3. Batch processing (requires configuration)")
    print("4. Interactive mode (requires configuration)")
    print("5. Run all examples")
    print("0. Exit")
    
    try:
        choice = input("\\nEnter your choice (0-5): ").strip()
        
        if choice == "1":
            example_single_image_analysis()
        elif choice == "2":
            if config_ok:
                example_full_automation()
            else:
                print("Please configure the bot first (.env file)")
        elif choice == "3":
            if config_ok:
                example_batch_processing()
            else:
                print("Please configure the bot first (.env file)")
        elif choice == "4":
            if config_ok:
                example_interactive_mode()
            else:
                print("Please configure the bot first (.env file)")
        elif choice == "5":
            example_single_image_analysis()
            if config_ok:
                example_full_automation()
                example_batch_processing()
            else:
                print("\\nSkipping web automation examples - please configure .env file")
        elif choice == "0":
            print("Goodbye!")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\\nExiting...")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
