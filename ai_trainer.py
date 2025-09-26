#!/usr/bin/env python3
"""
🎓 AI TRAINING SYSTEM
====================
Train the local AI model using actual holder photos and manual labels.
This solves the problem of how the AI knows what to recognize!

Features:
- Manual photo labeling interface
- Import existing GPT Vision results as training data
- Train machine learning models with real photos
- Validate and test model accuracy
- Progressive learning (add more photos over time)
- Visual feedback and accuracy tracking
"""

import cv2
import numpy as np
import json
import time
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
from dataclasses import dataclass
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# Import our modules
from advanced_local_ai import AdvancedLocalAI
from photo_manager import PhotoManager
from local_ai_database import LocalAIDatabase, HolderAnalysis

@dataclass
class TrainingExample:
    """Single training example with photo and labels"""
    holder_id: str
    photo_path: str
    material: str
    holder_type: str
    verified: bool = True
    features: Optional[List[float]] = None
    timestamp: float = 0.0

class AITrainer:
    """AI training system for holder recognition"""
    
    def __init__(self):
        self.setup_logging()
        
        # Initialize components
        self.local_ai = AdvancedLocalAI()
        self.photo_manager = PhotoManager()
        self.database = LocalAIDatabase()
        
        # Training data
        self.training_examples = []
        
        # Available options
        self.materials = ['kov', 'betón', 'drevo', 'plast']
        self.holder_types = [
            'stĺp značky samostatný',
            'stĺp značky dvojitý', 
            'stĺp verejného osvetlenia',
            'stĺp svetelného signalizačného zariadenia'
        ]
        
        self.logger.info("🎓 AI Trainer initialized")
        
    def setup_logging(self):
        """Setup logging for training operations"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("AITrainer")
        
    def create_training_gui(self):
        """Create GUI for manual photo labeling"""
        self.root = tk.Tk()
        self.root.title("🎓 AI Training System - Manual Photo Labeling")
        self.root.geometry("1200x800")
        
        # Set dark theme
        self.setup_dark_theme()
        
        # Current training state
        self.current_holder_id = ""
        self.current_photo_path = ""
        self.training_queue = []
        self.current_index = 0
        
        self.setup_gui_layout()
        
    def setup_dark_theme(self):
        """Setup dark theme colors"""
        # Dark theme colors
        bg_color = "#2b2b2b"  # Dark gray background
        fg_color = "#ffffff"  # White text
        accent_color = "#404040"  # Lighter gray for frames
        button_color = "#505050"  # Button background
        
        # Configure root window
        self.root.configure(bg=bg_color)
        
        # Configure ttk styles for dark theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=button_color, foreground=fg_color)
        style.configure('TRadiobutton', background=bg_color, foreground=fg_color)
        style.configure('TSeparator', background=accent_color)
        
        # Button hover effects
        style.map('TButton',
                  background=[('active', '#606060')],
                  foreground=[('active', fg_color)])
        
    def setup_gui_layout(self):
        """Setup the GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame - Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load photos button
        ttk.Button(control_frame, text="📁 Load Holder Photos", 
                  command=self.load_photos_for_training).pack(side=tk.LEFT, padx=(0, 10))
        
        # Import existing results button
        ttk.Button(control_frame, text="📥 Import GPT Results", 
                  command=self.import_gpt_results).pack(side=tk.LEFT, padx=(0, 10))
        
        # Train model button
        ttk.Button(control_frame, text="🧠 Train Model", 
                  command=self.train_model).pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress label
        self.progress_label = ttk.Label(control_frame, text="Ready to train...")
        self.progress_label.pack(side=tk.RIGHT)
        
        # Middle frame - Image and controls
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Image display
        image_frame = ttk.Frame(content_frame)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Image label
        self.image_label = ttk.Label(image_frame, text="Load photos to start training", 
                                   anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Labeling controls
        label_frame = ttk.Frame(content_frame, width=300)
        label_frame.pack(side=tk.RIGHT, fill=tk.Y)
        label_frame.pack_propagate(False)
        
        # Holder ID display
        ttk.Label(label_frame, text="Holder ID:").pack(anchor=tk.W, pady=(0, 5))
        self.holder_id_label = ttk.Label(label_frame, text="", font=('Arial', 12, 'bold'))
        self.holder_id_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Material selection
        ttk.Label(label_frame, text="Material:").pack(anchor=tk.W, pady=(0, 5))
        self.material_var = tk.StringVar(value=self.materials[0])
        for material in self.materials:
            ttk.Radiobutton(label_frame, text=material, variable=self.material_var, 
                          value=material).pack(anchor=tk.W)
        
        ttk.Separator(label_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Type selection
        ttk.Label(label_frame, text="Holder Type:").pack(anchor=tk.W, pady=(0, 5))
        self.type_var = tk.StringVar(value=self.holder_types[0])
        for holder_type in self.holder_types:
            ttk.Radiobutton(label_frame, text=holder_type, variable=self.type_var, 
                          value=holder_type).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(label_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # AI Prediction display (if available)
        ttk.Label(label_frame, text="AI Prediction:").pack(anchor=tk.W, pady=(0, 5))
        self.ai_prediction_label = ttk.Label(label_frame, text="Not analyzed", 
                                           foreground="gray")
        self.ai_prediction_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Navigation and action buttons
        button_frame = ttk.Frame(label_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="⬅ Previous", 
                  command=self.previous_photo).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Next ➡", 
                  command=self.next_photo).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Save label button
        ttk.Button(label_frame, text="💾 Save Labels", 
                  command=self.save_current_label).pack(fill=tk.X, pady=10)
        
        # Auto-analyze button
        ttk.Button(label_frame, text="🔍 Analyze with AI", 
                  command=self.analyze_current_photo).pack(fill=tk.X, pady=5)
        
        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Statistics
        self.stats_label = ttk.Label(status_frame, text="")
        self.stats_label.pack(side=tk.RIGHT)
        
    def load_photos_for_training(self):
        """Load holder photos for manual labeling"""
        try:
            # Check if sample_photos exists and offer to use it
            sample_photos_path = Path("sample_photos/holders-photos")
            if sample_photos_path.exists():
                use_sample = messagebox.askyesno(
                    "Use Sample Photos", 
                    f"Found {len(list(sample_photos_path.glob('*.png')))} photos in sample_photos folder.\n\nUse these photos for training?"
                )
                if use_sample:
                    folder_path = str(sample_photos_path)
                else:
                    folder_path = filedialog.askdirectory(title="Select photo folder")
            else:
                # Browse for photo folder
                folder_path = filedialog.askdirectory(title="Select photo folder")
            
            if folder_path:
                # Load photos from folder
                photo_files = []
                for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    photo_files.extend(Path(folder_path).glob(f'*{ext}'))
                    
                self.training_queue = []
                for photo_path in photo_files:
                    holder_id = photo_path.stem  # Use filename as holder ID
                    self.training_queue.append({
                        'holder_id': holder_id,
                        'photo_path': str(photo_path),
                        'labeled': False
                    })
                    
                self.current_index = 0
                self.update_display()
                self.update_status()
                
                messagebox.showinfo("Success", f"Loaded {len(self.training_queue)} photos for training")
            else:
                messagebox.showwarning("No Selection", "No folder selected.")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load photos: {e}")
            messagebox.showerror("Error", f"Failed to load photos: {e}")
            
    def update_display(self):
        """Update the display with current photo"""
        if not self.training_queue or self.current_index >= len(self.training_queue):
            return
            
        current_item = self.training_queue[self.current_index]
        self.current_holder_id = current_item['holder_id']
        self.current_photo_path = current_item['photo_path']
        
        # Update holder ID display
        self.holder_id_label.config(text=self.current_holder_id)
        
        # Load and display image
        try:
            # Load image
            image = Image.open(self.current_photo_path)
            
            # Resize to fit display
            display_size = (600, 400)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Update display
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Keep a reference
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load image: {e}")
            self.image_label.config(image="", text=f"Failed to load image: {e}")
            
        # Check if this holder already has labels in database
        existing_analysis = self.database.get_analysis(self.current_holder_id)
        if existing_analysis:
            self.material_var.set(existing_analysis.material)
            self.type_var.set(existing_analysis.holder_type)
            current_item['labeled'] = True
            
        self.update_progress()
        
    def analyze_current_photo(self):
        """Analyze current photo with AI and show prediction"""
        if not self.current_photo_path:
            return
            
        try:
            # Analyze with local AI
            photo_url = f"file://{self.current_photo_path}"
            result = self.local_ai.analyze_holder_from_url(self.current_holder_id, self.current_photo_path)
            
            if result:
                prediction_text = f"Material: {result.get('material', 'Unknown')} ({result.get('material_confidence', 0):.2f})\nType: {result.get('type', 'Unknown')} ({result.get('type_confidence', 0):.2f})"
                self.ai_prediction_label.config(text=prediction_text, foreground="blue")
                
                # Optionally auto-fill if confidence is high
                if result.get('confidence', 0) > 0.8:
                    response = messagebox.askyesno("High Confidence", 
                                                 f"AI is confident about this prediction. Auto-fill?\n\n{prediction_text}")
                    if response:
                        self.material_var.set(result.get('material', ''))
                        self.type_var.set(result.get('type', ''))
            else:
                self.ai_prediction_label.config(text="Analysis failed", foreground="red")
                
        except Exception as e:
            self.logger.error(f"❌ AI analysis failed: {e}")
            self.ai_prediction_label.config(text=f"Error: {e}", foreground="red")
            
    def save_current_label(self):
        """Save the current manual label"""
        if not self.current_holder_id:
            return
            
        try:
            # Create training example
            example = TrainingExample(
                holder_id=self.current_holder_id,
                photo_path=self.current_photo_path,
                material=self.material_var.get(),
                holder_type=self.type_var.get(),
                verified=True,
                timestamp=time.time()
            )
            
            # Extract features from photo
            image = cv2.imread(self.current_photo_path)
            if image is not None:
                example.features = self.local_ai.extract_comprehensive_features(image)
                
            # Add to training examples
            self.training_examples.append(example)
            
            # Also save to database
            analysis = HolderAnalysis(
                holder_id=self.current_holder_id,
                material=self.material_var.get(),
                holder_type=self.type_var.get(),
                confidence=1.0,  # Manual labels are 100% confident
                analysis_method="manual_training",
                timestamp=time.time(),
                verified=True,
                photo_path=self.current_photo_path
            )
            
            self.database.store_analysis(analysis)
            
            # Mark as labeled
            if self.current_index < len(self.training_queue):
                self.training_queue[self.current_index]['labeled'] = True
                
            self.update_status()
            self.logger.info(f"✅ Saved label for holder {self.current_holder_id}")
            
            # Auto-advance to next
            self.next_photo()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save label: {e}")
            messagebox.showerror("Error", f"Failed to save label: {e}")
            
    def previous_photo(self):
        """Go to previous photo"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()
            
    def next_photo(self):
        """Go to next photo"""
        if self.current_index < len(self.training_queue) - 1:
            self.current_index += 1
            self.update_display()
        else:
            messagebox.showinfo("Complete", "You've reached the end of the training queue!")
            
    def update_progress(self):
        """Update progress display"""
        if self.training_queue:
            total = len(self.training_queue)
            current = self.current_index + 1
            labeled_count = sum(1 for item in self.training_queue if item.get('labeled', False))
            
            self.progress_label.config(text=f"Photo {current}/{total} | Labeled: {labeled_count}")
        else:
            self.progress_label.config(text="No photos loaded")
            
    def update_status(self):
        """Update status information"""
        training_count = len(self.training_examples)
        self.status_label.config(text=f"Training examples: {training_count}")
        
        # Update statistics
        if self.training_queue:
            labeled_count = sum(1 for item in self.training_queue if item.get('labeled', False))
            total_count = len(self.training_queue)
            percentage = (labeled_count / total_count * 100) if total_count > 0 else 0
            
            self.stats_label.config(text=f"Progress: {labeled_count}/{total_count} ({percentage:.1f}%)")
            
    def import_gpt_results(self):
        """Import existing GPT Vision results as training data"""
        try:
            # Ask for GPT results file
            file_path = filedialog.askopenfilename(
                title="Select GPT Results File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Load and import
            imported_count = self.database.bulk_import_existing_data(file_path)
            
            if imported_count:
                messagebox.showinfo("Success", f"Imported {imported_count} existing results as training data")
                self.logger.info(f"✅ Imported {imported_count} GPT results")
            else:
                messagebox.showwarning("Warning", "No data was imported. Check the file format.")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to import GPT results: {e}")
            messagebox.showerror("Error", f"Failed to import: {e}")
            
    def train_model(self):
        """Train the AI model with collected training data"""
        try:
            # Prepare training data
            training_data = []
            
            # Add manual training examples
            for example in self.training_examples:
                if example.features:
                    training_data.append({
                        'holder_id': example.holder_id,
                        'material': example.material,
                        'type': example.holder_type,
                        'features': example.features,
                        'verified': example.verified
                    })
                    
            # Also get data from database
            db_stats = self.database.get_accuracy_stats()
            
            if len(training_data) < 10:
                response = messagebox.askyesno("Low Training Data", 
                                            f"Only {len(training_data)} training examples available. "
                                            f"Models work better with 50+ examples. Continue anyway?")
                if not response:
                    return
                    
            # Train the models
            self.logger.info(f"🧠 Training models with {len(training_data)} examples")
            
            success = self.local_ai.train_models_from_data(training_data)
            
            if success:
                messagebox.showinfo("Success", f"AI models trained successfully with {len(training_data)} examples!")
                self.logger.info("✅ Model training completed")
            else:
                messagebox.showerror("Error", "Model training failed. Check the logs.")
                
        except Exception as e:
            self.logger.error(f"❌ Model training failed: {e}")
            messagebox.showerror("Error", f"Training failed: {e}")
            
    def run_training_gui(self):
        """Run the training GUI"""
        self.create_training_gui()
        self.root.mainloop()
        
    def batch_extract_features_from_existing_data(self):
        """Extract features from all existing photos in database"""
        self.logger.info("📊 Extracting features from existing data...")
        
        # Get all analyses from database
        # This would need a method to get all analyses, which we'd need to add
        
        # For now, just show how it would work conceptually
        print("This would extract features from all existing photos and retrain the model")

if __name__ == "__main__":
    import tkinter.simpledialog
    
    trainer = AITrainer()
    
    print("🎓 AI TRAINING SYSTEM")
    print("=" * 50)
    print("This will help train the AI to recognize holders from actual photos!")
    print()
    print("Options:")
    print("1. 🖼️  Manual Photo Labeling GUI")
    print("2. 📥 Import existing GPT results") 
    print("3. 🧠 Train model from existing data")
    
    # For now, just start the GUI
    trainer.run_training_gui()
