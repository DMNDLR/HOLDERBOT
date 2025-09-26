# Slovak Traffic Sign AI Trainer 🎯🚦

A sophisticated manual AI training tool for labeling Slovak traffic sign holders and signs with advanced computer vision detection capabilities.

## 🚀 Latest Improvements (2025-09-26)

**MAJOR UPDATE**: Fixed aggressive computer vision detection that was creating too many overlapping rectangles!

✅ **Enhanced Detection Algorithms**: Much stricter filtering with solidity and rectangularity checks  
✅ **Non-Maximum Suppression**: Automatic removal of overlapping detections  
✅ **Sensitivity Controls**: Conservative/Normal/Aggressive modes for different photo conditions  
✅ **Detection Limits**: Max 2 poles, 3 signs per image to prevent false positive explosion  
✅ **Better Filtering**: Uses Intersection over Union (IoU) for overlap detection  

## ✨ Features

### 🎯 Manual Training Interface
- Clean, optimized UI designed for standard monitors (1400x800)
- Easy rectangle drawing with click & drag
- Drag-to-move functionality for repositioning rectangles
- Toggle buttons for each detected rectangle
- Big, visible save button for training data

### 🤖 Advanced Computer Vision Detection
- **Real image analysis** using OpenCV instead of basic pattern matching
- **Vertical structure detection** for traffic sign poles using edge detection and morphological operations
- **Rectangular contour detection** for traffic signs
- **Circular shape detection** using HoughCircles for round signs (speed limits, etc.)

### 🧹 Smart Filtering System
- **Non-Maximum Suppression (NMS)** to remove overlapping detections
- **Intersection over Union (IoU)** calculation for overlap detection
- **Confidence-based filtering** keeps only the best detections
- **Detection limits**: Max 2 poles, 3 rectangular signs, 2 circular signs per image

### 🎚️ Sensitivity Controls
- **Conservative**: Strictest criteria, fewest false positives
- **Normal**: Balanced detection (default)
- **Aggressive**: More permissive, higher recall
- Adjustable based on photo quality and angles

## 📥 Installation

```bash
pip install opencv-python pillow numpy tkinter
```

## 🖥️ Usage

1. **Load Photos**: Click "📁 LOAD PHOTOS" to select your training images
2. **Choose Detection Mode**: Select Conservative/Normal/Aggressive based on your photos
3. **Auto-Detect**: Click "🤖 AUTO DETECT" to let the AI find objects
4. **Manual Adjustment**: Draw additional rectangles or move existing ones
5. **Save Training Data**: Click "💾 SAVE THIS PHOTO" to store your labels

```bash
python optimized_trainer.py
```

## 🔧 Technical Details

### Computer Vision Pipeline
- **Image Processing**: Converts images to grayscale and scales to canvas size
- **Edge Detection**: Uses Canny edge detection with adjustable thresholds
- **Morphological Operations**: Enhances vertical and rectangular structures
- **Contour Analysis**: Filters shapes based on aspect ratio, area, and solidity
- **Post-Processing**: Applies NMS to remove overlapping detections

### Key Algorithms

#### Enhanced Pole Detection
```python
def detect_vertical_structures(self, img, sensitivity='normal'):
    # Stronger edge detection
    edges = cv2.Canny(img, 80, 200)  # Higher thresholds
    
    # Adjustable criteria based on sensitivity
    if sensitivity == 'conservative':
        min_h, max_h, min_aspect, min_area, max_w = 150, 300, 5, 1200, 40
    elif sensitivity == 'aggressive':
        min_h, max_h, min_aspect, min_area, max_w = 80, 400, 3, 500, 60
    else:  # normal
        min_h, max_h, min_aspect, min_area, max_w = 120, 350, 4, 800, 50
```

#### Non-Maximum Suppression
```python
def apply_nms(self, rectangles, overlap_threshold=0.3):
    # Sort by confidence (highest first)
    sorted_rects = sorted(rectangles, key=lambda r: r.confidence, reverse=True)
    
    kept = []
    for rect in sorted_rects:
        should_keep = True
        for kept_rect in kept:
            overlap = self.calculate_overlap(rect, kept_rect)
            if overlap > overlap_threshold:
                should_keep = False
                break
        if should_keep:
            kept.append(rect)
```

### Data Format
Training data is saved in JSON format with:
- Photo metadata (filename, dimensions, timestamp)
- Rectangle coordinates and types (holder/sign)
- Quality metrics and confidence scores
- Session statistics for progress tracking

## 📁 File Structure
```
optimized_trainer.py                    # Main training application
conversation_log_*.txt                  # Development session logs
optimized_training_data_*.json         # Saved training datasets
AI_TRAINER_README.md                   # This documentation
```

## 🐛 Problem Solved

### Before (The Issue)
The original system created too many overlapping rectangles that didn't align with actual traffic signs and poles, requiring manual corrections every time.

### After (The Solution)
1. **Enhanced Detection**: Stricter filtering criteria with shape validation
2. **Overlap Removal**: Automatic elimination of duplicate detections  
3. **User Control**: Sensitivity settings for different photo conditions
4. **Smart Limits**: Prevents explosion of false detections

## 📈 Results Expected
- Much fewer false positive detections
- No more overlapping rectangles covering the same object
- Better alignment with actual traffic signs and poles
- User control over detection sensitivity
- Cleaner, more usable auto-detection results
- Less manual correction needed

## 🔄 Next Steps
1. Test the improved detection on various photos
2. Fine-tune sensitivity parameters based on your specific dataset
3. Consider adding more advanced deep learning detection if needed
4. Collect feedback on detection quality improvements

---

For detailed development logs, see `conversation_log_ai_trainer_improvements.txt`