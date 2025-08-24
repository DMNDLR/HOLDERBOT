# GIS Traffic Sign Automation Bot 🚦🤖

An intelligent automation bot that analyzes traffic sign photos and automatically fills out attribute forms in GIS-based WordPress systems. Perfect for streamlining traffic management workflows!

## ✨ Features

- **🔍 Image Analysis**: Automatically detects traffic sign materials, conditions, sizes, and stand types
- **🌐 Web Automation**: Logs into WordPress/GIS systems and fills forms automatically  
- **📊 Batch Processing**: Process multiple images at once with detailed reporting
- **🎯 Interactive Mode**: Manual control for fine-tuning and testing
- **📝 Smart Form Filling**: Handles dropdowns, checkboxes, and text inputs intelligently
- **🛡️ Error Handling**: Robust error handling and logging for reliable operation

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/DMNDLR/my-project.git
cd my-project

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit the `.env` file with your GIS system details:

```env
# WordPress Login Credentials
SITE_URL=https://your-gis-site.com
LOGIN_URL=https://your-gis-site.com/wp-admin
USERNAME=your_username
PASSWORD=your_password

# GIS Page URLs
GIS_ADMIN_URL=https://your-gis-site.com/devadmin
TRAFFIC_SIGNS_URL=https://your-gis-site.com/traffic-signs
```

### 3. Usage

#### Quick Image Analysis (No Web Automation)
```python
from bot.traffic_sign_bot import analyze_image

results = analyze_image("path/to/traffic_sign.jpg")
print(results)
# Output: {'material': 'aluminum', 'condition': 'good', 'size': '600x600mm', ...}
```

#### Full Automation
```python
from bot.traffic_sign_bot import process_image_with_bot

# Process single image with web automation
success = process_image_with_bot("path/to/traffic_sign.jpg")
```

#### Interactive Mode
```python
python example_usage.py
# or
python bot/traffic_sign_bot.py
```

## 📁 Project Structure

```
my-project/
├── bot/                    # Main bot modules
│   └── traffic_sign_bot.py # Main bot class
├── src/                    # Core functionality
│   ├── web_automation.py   # Browser automation
│   └── image_analysis.py   # Image processing
├── config/                 # Configuration
│   └── config.py          # Settings and constants
├── images/                 # Image storage
├── logs/                   # Log files
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
└── example_usage.py       # Usage examples
```

## 🔧 Advanced Usage

### Batch Processing
```python
from bot.traffic_sign_bot import TrafficSignBot

with TrafficSignBot() as bot:
    if bot.login_to_system():
        results = bot.process_image_batch(
            image_folder="./images",
            output_report="./reports/batch_results.json"
        )
        print(f"Processed {results['processed']} images successfully")
```

### Custom Analysis Override
```python
# Override analysis results if needed
manual_overrides = {
    'material': 'steel',      # Force steel material
    'condition': 'excellent'  # Override condition
}

success = process_image_with_bot(
    "sign.jpg", 
    manual_override=manual_overrides
)
```

### Image Enhancement
```python
from src.image_analysis import TrafficSignAnalyzer

analyzer = TrafficSignAnalyzer()
enhanced_path = analyzer.enhance_image("low_quality_sign.jpg")
results = analyzer.analyze_image(enhanced_path)
```

## 🎯 Supported Attributes

The bot can detect and classify:

**Materials:**
- Aluminum
- Steel  
- Plastic
- Composite
- Reflective Sheeting

**Stand Types:**
- Metal Post
- Wooden Post  
- Concrete Post
- U-Channel Post
- Square Tube Post
- Round Post

**Conditions:**
- Excellent
- Good
- Fair
- Poor
- Damaged
- Needs Replacement

**Common Sizes:**
- 600x600mm
- 750x750mm
- 900x900mm
- 600x300mm
- 900x600mm
- Custom

## 🛠️ Configuration Options

### Browser Settings
```env
BROWSER_TYPE=chrome          # Browser type
HEADLESS_MODE=false         # Run browser in background
WAIT_TIMEOUT=30             # Page load timeout
IMPLICIT_WAIT=10           # Element wait timeout
```

### Image Processing
```env
IMAGE_FOLDER=./images       # Default image folder
SUPPORTED_FORMATS=jpg,jpeg,png,bmp
MAX_IMAGE_SIZE_MB=10       # Max file size
```

### Logging
```env
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
LOG_FILE=./logs/bot.log    # Log file location
```

## 🔍 Troubleshooting

### Common Issues

**"Failed to setup browser"**
- Ensure Chrome is installed
- Try running: `pip install --upgrade selenium webdriver-manager`

**"Login failed"**
- Check your credentials in `.env`
- Verify the LOGIN_URL is correct
- Ensure you have proper permissions

**"No traffic sign elements found"**
- The web page structure might be different
- Check the GIS_ADMIN_URL
- Use screenshot feature to debug: `bot.web_automation.take_screenshot()`

**"Image analysis failed"**
- Check image format (jpg, png, bmp supported)
- Ensure image is not corrupted
- Try image enhancement: `analyzer.enhance_image()`

### Debug Mode
```python
# Enable detailed logging
from config.config import Config
Config.LOG_LEVEL = "DEBUG"
Config.HEADLESS_MODE = False  # See browser actions
```

## 📊 Performance Tips

- **Batch Processing**: Use `process_image_batch()` for multiple images
- **Image Quality**: Higher quality images = better analysis results
- **Network**: Stable internet connection for web automation
- **Resources**: Close other browser instances when running

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Format code
black src/ bot/
```

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the log files in `./logs/`
3. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - System information
   - Log excerpts (remove sensitive data)

## 🎉 Acknowledgments

- Built with Selenium for web automation
- OpenCV and PIL for image processing
- Loguru for excellent logging
- Chrome WebDriver for browser control

---

**Happy Automating! 🚦✨**
