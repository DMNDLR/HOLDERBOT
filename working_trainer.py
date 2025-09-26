#!/usr/bin/env python3
"""
🎯 SIMPLE WORKING AI TRAINER
============================
ONE FILE THAT ACTUALLY WORKS!

This is a simplified, working version that:
1. Loads photos properly
2. Shows what's happening step by step
3. Draws rectangles that actually work
4. Shows YOLO predictions that you can see
5. Saves everything properly

NO CONFUSION - JUST WORKING AI TRAINING!
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import json
import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# Try to import YOLO, but work without it if not available
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ YOLO available")
except ImportError:
    YOLO_AVAILABLE = False
    print("❌ YOLO not available")

@dataclass
class Rectangle:
    """Simple rectangle with coordinates and type"""
    x1: int
    y1: int
    x2: int
    y2: int
    type: str  # 'holder' or 'sign'
    source: str = 'manual'  # 'manual' or 'yolo'
    confidence: float = 1.0

class SimpleWorkingTrainer:
    """Simple trainer that actually works"""
    
    def __init__(self):
        self.photos = []
        self.current_photo_index = 0
        self.current_image = None
        self.photo_tk = None
        
        # Rectangle drawing
        self.rectangles = []
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        self.drawing_mode = 'holder'  # 'holder' or 'sign'
        
        # YOLO
        self.yolo_model = None
        self.yolo_rectangles = []
        
        # Training data storage
        self.all_training_data = []
        
        print("🎯 Simple Working Trainer initialized")
        
    def create_gui(self):
        """Create simple, working GUI"""
        self.root = tk.Tk()
        self.root.title("🎯 Simple Working AI Trainer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top controls
        self.create_controls(main_frame)
        
        # Main content
        self.create_content(main_frame)
        
        # Status
        self.create_status(main_frame)
        
        print("✅ GUI created successfully")
        
    def create_controls(self, parent):
        """Create control buttons"""
        controls = tk.Frame(parent, bg='#2b2b2b')
        controls.pack(fill=tk.X, pady=(0, 10))
        
        # Load photos
        load_btn = tk.Button(controls, text="📁 LOAD PHOTOS", 
                            command=self.load_photos,
                            bg='#0066cc', fg='white', 
                            font=('Arial', 12, 'bold'))
        load_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # YOLO Bootstrap
        if YOLO_AVAILABLE:
            yolo_btn = tk.Button(controls, text="🤖 YOLO SCAN", 
                               command=self.run_yolo_scan,
                               bg='#ff6600', fg='white',
                               font=('Arial', 12, 'bold'))
            yolo_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Show what we have
        data_btn = tk.Button(controls, text="📊 SHOW DATA", 
                           command=self.show_all_data,
                           bg='#009900', fg='white',
                           font=('Arial', 12, 'bold'))
        data_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Navigation
        self.nav_frame = tk.Frame(controls, bg='#2b2b2b')
        self.nav_frame.pack(side=tk.RIGHT)
        
        self.prev_btn = tk.Button(self.nav_frame, text="⬅", 
                                 command=self.prev_photo,
                                 bg='#666666', fg='white')
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.photo_label = tk.Label(self.nav_frame, text="No photos", 
                                   bg='#2b2b2b', fg='white')
        self.photo_label.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(self.nav_frame, text="➡", 
                                 command=self.next_photo,
                                 bg='#666666', fg='white')
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
    def create_content(self, parent):
        """Create main content area"""
        content = tk.Frame(parent, bg='#2b2b2b')
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Image and drawing
        left_frame = tk.Frame(content, bg='#2b2b2b')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Drawing mode
        mode_frame = tk.Frame(left_frame, bg='#2b2b2b')
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(mode_frame, text="Drawing Mode:", 
                bg='#2b2b2b', fg='white').pack(side=tk.LEFT)
        
        self.mode_var = tk.StringVar(value='holder')
        tk.Radiobutton(mode_frame, text="🟢 Holders", variable=self.mode_var,
                      value='holder', bg='#2b2b2b', fg='#00ff00',
                      selectcolor='#2b2b2b',
                      command=self.change_mode).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="🔵 Signs", variable=self.mode_var,
                      value='sign', bg='#2b2b2b', fg='#0099ff',
                      selectcolor='#2b2b2b',
                      command=self.change_mode).pack(side=tk.LEFT)
        
        # Canvas for image
        self.canvas = tk.Canvas(left_frame, bg='#1a1a1a', width=700, height=500)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)
        
        # Drawing controls
        draw_controls = tk.Frame(left_frame, bg='#2b2b2b')
        draw_controls.pack(fill=tk.X, pady=5)
        
        tk.Button(draw_controls, text="🗑️ Clear All", 
                 command=self.clear_rectangles,
                 bg='#cc0000', fg='white').pack(side=tk.LEFT, padx=5)
        
        tk.Button(draw_controls, text="💾 Save Current", 
                 command=self.save_current_photo,
                 bg='#009900', fg='white').pack(side=tk.LEFT, padx=5)
        
        # Right side - Info and data
        right_frame = tk.Frame(content, bg='#404040', width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        # Current photo info
        tk.Label(right_frame, text="📸 CURRENT PHOTO", 
                bg='#404040', fg='white', 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.current_info = tk.Text(right_frame, height=8, 
                                   bg='#1a1a1a', fg='#00ff00',
                                   font=('Consolas', 9))
        self.current_info.pack(fill=tk.X, padx=10, pady=5)
        
        # All data summary
        tk.Label(right_frame, text="📊 ALL TRAINING DATA", 
                bg='#404040', fg='white', 
                font=('Arial', 12, 'bold')).pack(pady=(20, 10))
        
        self.all_data_info = tk.Text(right_frame, height=12, 
                                    bg='#1a1a1a', fg='#ffff00',
                                    font=('Consolas', 9))
        self.all_data_info.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def create_status(self, parent):
        """Create status bar"""
        self.status_frame = tk.Frame(parent, bg='#404040')
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(self.status_frame, text="Ready to load photos", 
                                    bg='#404040', fg='white')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
    def load_photos(self):
        """Load photos from folder"""
        try:
            # Check for sample photos first
            sample_path = Path("sample_photos/holders-photos")
            if sample_path.exists():
                use_sample = messagebox.askyesno(
                    "Sample Photos Found",
                    f"Found {len(list(sample_path.glob('*.png')))} photos in sample_photos.\n\nUse these?"
                )
                if use_sample:
                    folder = str(sample_path)
                else:
                    folder = filedialog.askdirectory(title="Select photo folder")
            else:
                folder = filedialog.askdirectory(title="Select photo folder")
                
            if not folder:
                return
                
            # Load all images
            extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            self.photos = []
            
            for ext in extensions:
                self.photos.extend(Path(folder).glob(f'*{ext}'))
                self.photos.extend(Path(folder).glob(f'*{ext.upper()}'))
                
            self.photos = sorted(self.photos)
            
            if self.photos:
                self.current_photo_index = 0
                self.load_current_photo()
                messagebox.showinfo("Success", f"Loaded {len(self.photos)} photos!")
                self.status_label.config(text=f"Loaded {len(self.photos)} photos - Ready to work!")
            else:
                messagebox.showwarning("No Photos", "No image files found!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load photos: {e}")
            
    def load_current_photo(self):
        """Load and display current photo"""
        if not self.photos or self.current_photo_index >= len(self.photos):
            return
            
        try:
            photo_path = self.photos[self.current_photo_index]
            self.current_image = Image.open(photo_path)
            
            # Resize to fit canvas
            canvas_width = 700
            canvas_height = 500
            
            img_width, img_height = self.current_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            display_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo_tk = ImageTk.PhotoImage(display_image)
            
            # Display on canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_tk)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            
            # Update navigation
            self.photo_label.config(text=f"{self.current_photo_index + 1}/{len(self.photos)}: {photo_path.name}")
            
            # Clear rectangles for new photo
            self.rectangles = []
            self.yolo_rectangles = []
            
            # Update display
            self.update_current_info()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load photo: {e}")
            
    def change_mode(self):
        """Change drawing mode"""
        self.drawing_mode = self.mode_var.get()
        print(f"Drawing mode: {self.drawing_mode}")
        
    def start_draw(self, event):
        """Start drawing rectangle"""
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        
    def draw_drag(self, event):
        """Draw rectangle while dragging"""
        if self.drawing:
            # Remove previous preview
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                
            # Draw preview rectangle
            color = '#00ff00' if self.drawing_mode == 'holder' else '#0099ff'
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=2, dash=(3, 3)
            )
            
    def end_draw(self, event):
        """Finish drawing rectangle"""
        if self.drawing:
            self.drawing = False
            
            # Calculate coordinates
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            
            # Only add if big enough
            if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                rect = Rectangle(x1=x1, y1=y1, x2=x2, y2=y2, 
                               type=self.drawing_mode, source='manual')
                self.rectangles.append(rect)
                
                print(f"✅ Added {self.drawing_mode} rectangle: {x1},{y1} to {x2},{y2}")
                
                # Redraw all rectangles
                self.redraw_rectangles()
                self.update_current_info()
            
            # Remove preview
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
                
    def redraw_rectangles(self):
        """Redraw all rectangles on canvas"""
        # Clear existing rectangles
        self.canvas.delete("rectangle")
        
        # Draw manual rectangles
        for i, rect in enumerate(self.rectangles):
            color = '#00ff00' if rect.type == 'holder' else '#0099ff'
            
            self.canvas.create_rectangle(
                rect.x1, rect.y1, rect.x2, rect.y2,
                outline=color, width=3, tags="rectangle"
            )
            
            # Add label
            self.canvas.create_text(
                rect.x1 + 5, rect.y1 - 15,
                text=f"MANUAL {rect.type.upper()} #{i+1}",
                fill=color, font=('Arial', 9, 'bold'),
                tags="rectangle", anchor=tk.W
            )
            
        # Draw YOLO rectangles
        for i, rect in enumerate(self.yolo_rectangles):
            color = '#ffff00' if rect.type == 'holder' else '#ff6600'
            
            self.canvas.create_rectangle(
                rect.x1, rect.y1, rect.x2, rect.y2,
                outline=color, width=2, dash=(5, 5), tags="rectangle"
            )
            
            # Add label
            self.canvas.create_text(
                rect.x1 + 5, rect.y1 - 15,
                text=f"YOLO {rect.type.upper()} {rect.confidence:.2f}",
                fill=color, font=('Arial', 8, 'bold'),
                tags="rectangle", anchor=tk.W
            )
            
    def clear_rectangles(self):
        """Clear all rectangles"""
        self.rectangles = []
        self.yolo_rectangles = []
        self.canvas.delete("rectangle")
        self.update_current_info()
        print("🗑️ Cleared all rectangles")
        
    def save_current_photo(self):
        """Save current photo's rectangles and data"""
        if not self.photos or not (self.rectangles or self.yolo_rectangles):
            messagebox.showwarning("No Data", "No rectangles to save!")
            return
            
        try:
            photo_path = self.photos[self.current_photo_index]
            
            # Create training data entry
            training_entry = {
                'photo_id': photo_path.stem,
                'photo_path': str(photo_path),
                'timestamp': time.time(),
                'manual_rectangles': [],
                'yolo_rectangles': [],
                'total_rectangles': len(self.rectangles) + len(self.yolo_rectangles)
            }
            
            # Add manual rectangles
            for rect in self.rectangles:
                training_entry['manual_rectangles'].append({
                    'x1': rect.x1, 'y1': rect.y1, 'x2': rect.x2, 'y2': rect.y2,
                    'type': rect.type,
                    'source': 'manual',
                    'confidence': 1.0
                })
                
            # Add YOLO rectangles
            for rect in self.yolo_rectangles:
                training_entry['yolo_rectangles'].append({
                    'x1': rect.x1, 'y1': rect.y1, 'x2': rect.x2, 'y2': rect.y2,
                    'type': rect.type,
                    'source': 'yolo',
                    'confidence': rect.confidence
                })
                
            # Add to all training data
            self.all_training_data.append(training_entry)
            
            # Save to file
            output_file = f"working_training_data_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_training_data, f, indent=2, ensure_ascii=False)
                
            messagebox.showinfo("Saved!", 
                               f"Saved {len(self.rectangles)} manual + {len(self.yolo_rectangles)} YOLO rectangles!\n\n" +
                               f"Total training data: {len(self.all_training_data)} photos\n" +
                               f"File: {output_file}")
            
            self.update_all_data_info()
            print(f"✅ Saved training data for {photo_path.name}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save: {e}")
            
    def run_yolo_scan(self):
        """Run YOLO scan on current photo"""
        if not YOLO_AVAILABLE:
            messagebox.showerror("YOLO Error", "YOLO not available!")
            return
            
        if not self.photos:
            messagebox.showwarning("No Photos", "Load photos first!")
            return
            
        try:
            # Initialize YOLO if needed
            if not self.yolo_model:
                self.status_label.config(text="Loading YOLO model...")
                self.root.update()
                self.yolo_model = YOLO('yolov8n.pt')
                
            current_photo = self.photos[self.current_photo_index]
            self.status_label.config(text=f"YOLO scanning {current_photo.name}...")
            self.root.update()
            
            # Run YOLO detection
            results = self.yolo_model(str(current_photo), conf=0.25, verbose=False)
            
            # Clear previous YOLO rectangles
            self.yolo_rectangles = []
            
            # Process results
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Get coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = result.names[class_id]
                        
                        # Scale coordinates to canvas size
                        img_width, img_height = self.current_image.size
                        canvas_width, canvas_height = 700, 500
                        scale_x = canvas_width / img_width
                        scale_y = canvas_height / img_height
                        scale = min(scale_x, scale_y)
                        
                        scaled_x1 = int(x1 * scale)
                        scaled_y1 = int(y1 * scale)
                        scaled_x2 = int(x2 * scale)
                        scaled_y2 = int(y2 * scale)
                        
                        # Interpret as holder or sign
                        obj_type = self.interpret_yolo_class(class_name, scaled_x2-scaled_x1, scaled_y2-scaled_y1)
                        
                        rect = Rectangle(x1=scaled_x1, y1=scaled_y1, x2=scaled_x2, y2=scaled_y2,
                                       type=obj_type, source='yolo', confidence=confidence)
                        self.yolo_rectangles.append(rect)
                        
            # Redraw everything
            self.redraw_rectangles()
            self.update_current_info()
            
            # Show results
            holders = len([r for r in self.yolo_rectangles if r.type == 'holder'])
            signs = len([r for r in self.yolo_rectangles if r.type == 'sign'])
            
            messagebox.showinfo("YOLO Results", 
                               f"YOLO detected:\n{holders} holders (yellow)\n{signs} signs (orange)\n\n" +
                               "You can now review and save these predictions!")
            
            self.status_label.config(text=f"YOLO found {len(self.yolo_rectangles)} objects")
            
        except Exception as e:
            messagebox.showerror("YOLO Error", f"YOLO scan failed: {e}")
            self.status_label.config(text="YOLO scan failed")
            
    def interpret_yolo_class(self, class_name, width, height):
        """Interpret YOLO class as holder or sign"""
        aspect_ratio = height / width if width > 0 else 1
        
        # Traffic signs are usually detected directly
        if 'sign' in class_name.lower() or 'traffic' in class_name.lower():
            return 'sign'
            
        # Tall objects are likely holders
        if aspect_ratio > 2.0:
            return 'holder'
            
        # Small square objects are likely signs  
        if aspect_ratio < 1.5 and width < 100:
            return 'sign'
            
        # Default to holder for ambiguous cases
        return 'holder'
        
    def prev_photo(self):
        """Go to previous photo"""
        if self.photos and self.current_photo_index > 0:
            self.current_photo_index -= 1
            self.load_current_photo()
            
    def next_photo(self):
        """Go to next photo"""
        if self.photos and self.current_photo_index < len(self.photos) - 1:
            self.current_photo_index += 1
            self.load_current_photo()
            
    def update_current_info(self):
        """Update current photo info display"""
        self.current_info.delete(1.0, tk.END)
        
        if not self.photos:
            self.current_info.insert(tk.END, "No photos loaded")
            return
            
        photo_path = self.photos[self.current_photo_index]
        
        info = f"📸 {photo_path.name}\n\n"
        
        # Manual rectangles
        manual_holders = len([r for r in self.rectangles if r.type == 'holder'])
        manual_signs = len([r for r in self.rectangles if r.type == 'sign'])
        info += f"✋ MANUAL DRAWN:\n"
        info += f"  Holders: {manual_holders}\n"
        info += f"  Signs: {manual_signs}\n"
        info += f"  Total: {len(self.rectangles)}\n\n"
        
        # YOLO rectangles
        yolo_holders = len([r for r in self.yolo_rectangles if r.type == 'holder'])
        yolo_signs = len([r for r in self.yolo_rectangles if r.type == 'sign'])
        info += f"🤖 YOLO DETECTED:\n"
        info += f"  Holders: {yolo_holders}\n"
        info += f"  Signs: {yolo_signs}\n"
        info += f"  Total: {len(self.yolo_rectangles)}\n\n"
        
        total = len(self.rectangles) + len(self.yolo_rectangles)
        if total > 0:
            info += f"✅ READY TO SAVE: {total} objects"
        else:
            info += f"⚠️ Draw rectangles or run YOLO scan"
            
        self.current_info.insert(tk.END, info)
        
    def update_all_data_info(self):
        """Update all training data info"""
        self.all_data_info.delete(1.0, tk.END)
        
        if not self.all_training_data:
            self.all_data_info.insert(tk.END, "No training data saved yet\n\nDraw rectangles and click 'Save Current'")
            return
            
        total_photos = len(self.all_training_data)
        total_manual = sum(len(item['manual_rectangles']) for item in self.all_training_data)
        total_yolo = sum(len(item['yolo_rectangles']) for item in self.all_training_data)
        total_objects = total_manual + total_yolo
        
        info = f"📊 TRAINING DATA SUMMARY:\n\n"
        info += f"Photos saved: {total_photos}\n"
        info += f"Manual rectangles: {total_manual}\n"
        info += f"YOLO rectangles: {total_yolo}\n"
        info += f"Total objects: {total_objects}\n\n"
        
        if total_objects >= 50:
            info += f"✅ EXCELLENT! Ready for AI training\n"
        elif total_objects >= 20:
            info += f"🟡 GOOD! Keep adding more data\n"
        else:
            info += f"🔴 Need more data for good AI\n"
            
        info += f"\nRECOMMENDED: 100+ objects\n"
        
        # Recent files
        info += f"\n📄 RECENT SAVES:\n"
        for i, item in enumerate(reversed(self.all_training_data[-5:])):
            info += f"{i+1}. {item['photo_id']} ({item['total_rectangles']} objects)\n"
            
        self.all_data_info.insert(tk.END, info)
        
    def show_all_data(self):
        """Show comprehensive data analysis"""
        # Load any existing training data files
        self.load_existing_data()
        
        # Create data window
        data_window = tk.Toplevel(self.root)
        data_window.title("📊 All Training Data Analysis")
        data_window.geometry("800x600")
        data_window.configure(bg='#1a1a1a')
        
        # Header
        header = tk.Label(data_window, text="📊 COMPLETE TRAINING DATA ANALYSIS",
                         bg='#1a1a1a', fg='#00ff00', font=('Arial', 16, 'bold'))
        header.pack(pady=10)
        
        # Data display
        text_frame = tk.Frame(data_window, bg='#1a1a1a')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        data_text = tk.Text(text_frame, bg='#1a1a1a', fg='white', 
                           font=('Consolas', 11), wrap=tk.WORD)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=data_text.yview)
        data_text.configure(yscrollcommand=scrollbar.set)
        
        data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report()
        data_text.insert(tk.END, report)
        data_text.config(state=tk.DISABLED)
        
    def load_existing_data(self):
        """Load existing training data files"""
        try:
            # Look for working training data files
            data_files = list(Path('.').glob('working_training_data_*.json'))
            for file in data_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            # Merge without duplicates
                            existing_ids = {item['photo_id'] for item in self.all_training_data}
                            for item in data:
                                if item['photo_id'] not in existing_ids:
                                    self.all_training_data.append(item)
                except:
                    continue
                    
        except Exception as e:
            print(f"Failed to load existing data: {e}")
            
    def generate_comprehensive_report(self):
        """Generate comprehensive training data report"""
        if not self.all_training_data:
            return """⚠️ NO TRAINING DATA FOUND!

To get started:
1. Click '📁 LOAD PHOTOS' to load your traffic sign photos
2. Draw green rectangles around holders
3. Draw blue rectangles around signs  
4. OR click '🤖 YOLO SCAN' for instant predictions
5. Click '💾 Save Current' to save your work

The system will guide you through the entire process!"""

        total_photos = len(self.all_training_data)
        total_manual = sum(len(item['manual_rectangles']) for item in self.all_training_data)
        total_yolo = sum(len(item['yolo_rectangles']) for item in self.all_training_data)
        total_objects = total_manual + total_yolo
        
        # Count by type
        manual_holders = sum(1 for item in self.all_training_data 
                           for rect in item['manual_rectangles'] 
                           if rect['type'] == 'holder')
        manual_signs = sum(1 for item in self.all_training_data 
                         for rect in item['manual_rectangles'] 
                         if rect['type'] == 'sign')
        yolo_holders = sum(1 for item in self.all_training_data 
                         for rect in item['yolo_rectangles'] 
                         if rect['type'] == 'holder')
        yolo_signs = sum(1 for item in self.all_training_data 
                       for rect in item['yolo_rectangles'] 
                       if rect['type'] == 'sign')
        
        report = f"""✅ TRAINING DATA ANALYSIS COMPLETE!

📊 SUMMARY:
• Total photos with data: {total_photos}
• Total objects labeled: {total_objects}
• Manual quality: {(total_manual/total_objects*100):.1f}% ({total_manual} objects)
• YOLO predictions: {(total_yolo/total_objects*100):.1f}% ({total_yolo} objects)

📦 OBJECT BREAKDOWN:
• Manual holders: {manual_holders}
• Manual signs: {manual_signs}
• YOLO holders: {yolo_holders}
• YOLO signs: {yolo_signs}

🎯 TRAINING READINESS:"""

        if total_objects >= 100:
            report += f"""
✅ EXCELLENT! ({total_objects} objects)
Your dataset is ready for high-quality AI training!
- Sufficient data for good accuracy
- Mix of manual and YOLO data is ideal
- Ready to train custom models"""
        elif total_objects >= 50:
            report += f"""
🟡 GOOD START! ({total_objects} objects)
You have a solid foundation. Recommendations:
- Add 50+ more objects for better accuracy
- Continue mixing manual corrections with YOLO
- Focus on difficult cases YOLO missed"""
        elif total_objects >= 20:
            report += f"""
🟠 GETTING THERE! ({total_objects} objects)
You're making progress. Next steps:
- Add 30+ more objects
- Use YOLO scan to speed up the process
- Manually correct YOLO predictions"""
        else:
            report += f"""
🔴 NEED MORE DATA! ({total_objects} objects)
To build effective AI:
- Target: 100+ objects minimum
- Use YOLO scan for quick predictions
- Draw rectangles on 20+ more photos"""

        report += f"""

💡 RECOMMENDATIONS:
1. Manual annotations are higher quality than YOLO
2. Correct YOLO predictions to improve training data
3. Focus on photos YOLO struggled with
4. Save your work frequently
5. Aim for balanced holder/sign examples

🚀 NEXT STEPS:
- Continue labeling photos
- Use this data to train custom AI models
- The more data you add, the better your AI becomes!"""

        return report
        
    def run(self):
        """Run the application"""
        self.create_gui()
        self.update_all_data_info()  # Initial update
        self.root.mainloop()

if __name__ == "__main__":
    print("🎯 Starting Simple Working AI Trainer...")
    trainer = SimpleWorkingTrainer()
    trainer.run()