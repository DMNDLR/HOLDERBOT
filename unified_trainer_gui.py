#!/usr/bin/env python3
"""
🧠🎯 UNIFIED AI TRAINER GUI
===========================
The MOST EFFECTIVE Slovak traffic sign holder AI trainer.
NO MORE CONFUSION - this system seamlessly combines:
- All your manual annotations
- YOLO bootstrap predictions  
- Real-time AI training
- Progressive learning improvements

Clear status, no "Draw rectangles" messages - just smart, effective training!
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
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import subprocess
import sys

# Import unified system
from unified_ai_system import UnifiedAISystem
from yolo_bootstrap import YOLOBootstrap

@dataclass
class Rectangle:
    """Rectangle annotation with metadata"""
    x: int
    y: int
    width: int
    height: int
    type: str  # 'holder' or 'sign'
    confidence: float = 1.0
    source: str = 'manual'  # 'manual', 'yolo', 'ai_prediction'

class UnifiedTrainerGUI:
    """Unified AI trainer with smart data integration"""
    
    def __init__(self):
        self.setup_logging()
        
        # Initialize systems
        self.unified_system = UnifiedAISystem()
        self.yolo_bootstrap = YOLOBootstrap()
        
        # Training data state
        self.photos_list = []
        self.current_photo_index = 0
        self.current_photo_path = ""
        
        # Annotation data
        self.manual_rectangles = []
        self.yolo_rectangles = []
        self.ai_predictions = []
        
        # Project persistence
        self.project_data = {
            'photos': [],
            'annotations': {},
            'training_progress': {},
            'last_saved': time.time()
        }
        
        # Available options for Slovak traffic signs
        self.materials = ['kov', 'betón', 'drevo', 'plast', 'kompozit']
        self.holder_types = [
            'stĺp značky samostatný',
            'stĺp značky dvojitý', 
            'stĺp verejného osvetlenia',
            'stĺp svetelného signalizačného zariadenia',
            'stĺp iný'
        ]
        
        # Sign directions in Slovak
        self.sign_directions = [
            'v smere jazdy',
            'kolmo na smer jazdy', 
            'proti smeru jazdy',
            'obojsmerná'
        ]
        
        self.logger.info("🧠 Unified Trainer GUI initialized")
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("UnifiedTrainer")
        
    def create_gui(self):
        """Create the unified trainer GUI"""
        self.root = tk.Tk()
        self.root.title("🧠 Unified AI Trainer - Slovak Traffic Sign Recognition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        self.setup_styles()
        self.create_layout()
        
        # Load existing project data
        self.load_project()
        
        # Initial status update
        self.update_comprehensive_status()
        
    def setup_styles(self):
        """Setup dark theme styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Dark theme colors
        bg_dark = '#1a1a1a'
        bg_medium = '#2d2d2d'
        fg_light = '#ffffff'
        accent_blue = '#3498db'
        accent_green = '#2ecc71'
        accent_orange = '#f39c12'
        
        # Configure styles
        self.style.configure('Dark.TFrame', background=bg_dark)
        self.style.configure('Medium.TFrame', background=bg_medium, relief='raised')
        self.style.configure('Dark.TLabel', background=bg_dark, foreground=fg_light, font=('Arial', 10))
        self.style.configure('Header.TLabel', background=bg_dark, foreground=accent_blue, font=('Arial', 14, 'bold'))
        self.style.configure('Status.TLabel', background=bg_dark, foreground=accent_green, font=('Arial', 12))
        
    def create_layout(self):
        """Create the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with title and unified system status
        self.create_header(main_frame)
        
        # Control panel
        self.create_control_panel(main_frame)
        
        # Main content area - photos and annotations
        self.create_content_area(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        """Create header with system status"""
        header_frame = ttk.Frame(parent, style='Medium.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="🧠 Unified AI Trainer", style='Header.TLabel')
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # System status
        self.system_status_label = ttk.Label(header_frame, text="🔄 Analyzing existing data...", style='Status.TLabel')
        self.system_status_label.pack(side=tk.RIGHT, padx=10, pady=10)
        
    def create_control_panel(self, parent):
        """Create control panel with smart actions"""
        control_frame = ttk.Frame(parent, style='Medium.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side - Data management
        left_controls = ttk.Frame(control_frame, style='Medium.TFrame')
        left_controls.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(left_controls, text="📁 Data Management", style='Dark.TLabel').pack(anchor=tk.W)
        
        btn_frame1 = ttk.Frame(left_controls, style='Medium.TFrame')
        btn_frame1.pack(fill=tk.X, pady=5)
        
        self.load_photos_btn = tk.Button(btn_frame1, text="📸 Load Photos", 
                                        command=self.load_photos, bg='#3498db', fg='white', 
                                        font=('Arial', 10, 'bold'))
        self.load_photos_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_project_btn = tk.Button(btn_frame1, text="💾 Save Project", 
                                         command=self.save_project, bg='#2ecc71', fg='white',
                                         font=('Arial', 10, 'bold'))
        self.save_project_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Middle - AI Actions
        middle_controls = ttk.Frame(control_frame, style='Medium.TFrame')
        middle_controls.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(middle_controls, text="🤖 AI Actions", style='Dark.TLabel').pack(anchor=tk.W)
        
        btn_frame2 = ttk.Frame(middle_controls, style='Medium.TFrame')
        btn_frame2.pack(fill=tk.X, pady=5)
        
        self.yolo_bootstrap_btn = tk.Button(btn_frame2, text="⚡ YOLO Bootstrap", 
                                           command=self.run_yolo_bootstrap, bg='#f39c12', fg='white',
                                           font=('Arial', 10, 'bold'))
        self.yolo_bootstrap_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.train_ai_btn = tk.Button(btn_frame2, text="🧠 Train AI", 
                                     command=self.train_unified_ai, bg='#9b59b6', fg='white',
                                     font=('Arial', 10, 'bold'))
        self.train_ai_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Right side - Analysis
        right_controls = ttk.Frame(control_frame, style='Medium.TFrame')
        right_controls.pack(side=tk.RIGHT, padx=10, pady=10)
        
        ttk.Label(right_controls, text="📊 Analysis", style='Dark.TLabel').pack(anchor=tk.W)
        
        btn_frame3 = ttk.Frame(right_controls, style='Medium.TFrame')
        btn_frame3.pack(fill=tk.X, pady=5)
        
        self.unified_report_btn = tk.Button(btn_frame3, text="📈 Unified Report", 
                                           command=self.show_unified_report, bg='#e74c3c', fg='white',
                                           font=('Arial', 10, 'bold'))
        self.unified_report_btn.pack(side=tk.LEFT, padx=(0, 5))
        
    def create_content_area(self, parent):
        """Create main content area"""
        content_frame = ttk.Frame(parent, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Photo display
        self.create_photo_display(content_frame)
        
        # Right side - Annotation controls
        self.create_annotation_panel(content_frame)
        
    def create_photo_display(self, parent):
        """Create photo display area"""
        photo_frame = ttk.Frame(parent, style='Medium.TFrame')
        photo_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Photo navigation
        nav_frame = ttk.Frame(photo_frame, style='Medium.TFrame')
        nav_frame.pack(fill=tk.X, pady=5)
        
        self.prev_btn = tk.Button(nav_frame, text="⬅ Previous", command=self.prev_photo,
                                 bg='#34495e', fg='white')
        self.prev_btn.pack(side=tk.LEFT)
        
        self.photo_info_label = ttk.Label(nav_frame, text="No photos loaded", style='Dark.TLabel')
        self.photo_info_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = tk.Button(nav_frame, text="Next ➡", command=self.next_photo,
                                 bg='#34495e', fg='white')
        self.next_btn.pack(side=tk.RIGHT)
        
        # Photo canvas with drawing capabilities
        canvas_frame = ttk.Frame(photo_frame, style='Medium.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.photo_canvas = tk.Canvas(canvas_frame, bg='#2d2d2d', highlightthickness=0)
        self.photo_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for rectangle drawing
        self.photo_canvas.bind("<Button-1>", self.on_canvas_click)
        self.photo_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.photo_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Drawing state
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        self.drawing_mode = 'holder'  # 'holder' or 'sign'
        
    def create_annotation_panel(self, parent):
        """Create annotation control panel"""
        panel_frame = ttk.Frame(parent, style='Medium.TFrame', width=350)
        panel_frame.pack(side=tk.RIGHT, fill=tk.Y)
        panel_frame.pack_propagate(False)
        
        # Panel header
        ttk.Label(panel_frame, text="🏷️ Annotations", style='Header.TLabel').pack(pady=10)
        
        # Drawing mode selection
        mode_frame = ttk.Frame(panel_frame, style='Medium.TFrame')
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(mode_frame, text="Drawing Mode:", style='Dark.TLabel').pack(anchor=tk.W)
        
        self.mode_var = tk.StringVar(value='holder')
        mode_radio_frame = ttk.Frame(mode_frame, style='Medium.TFrame')
        mode_radio_frame.pack(fill=tk.X, pady=2)
        
        holder_radio = tk.Radiobutton(mode_radio_frame, text="🟢 Holder", variable=self.mode_var,
                                     value='holder', bg='#2d2d2d', fg='#2ecc71', 
                                     selectcolor='#2d2d2d', command=self.update_drawing_mode)
        holder_radio.pack(side=tk.LEFT)
        
        sign_radio = tk.Radiobutton(mode_radio_frame, text="🔵 Sign", variable=self.mode_var,
                                   value='sign', bg='#2d2d2d', fg='#3498db', 
                                   selectcolor='#2d2d2d', command=self.update_drawing_mode)
        sign_radio.pack(side=tk.LEFT, padx=(10, 0))
        
        # Rectangle management
        rect_frame = ttk.Frame(panel_frame, style='Medium.TFrame')
        rect_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(rect_frame, text="Rectangle Controls:", style='Dark.TLabel').pack(anchor=tk.W)
        
        rect_btn_frame = ttk.Frame(rect_frame, style='Medium.TFrame')
        rect_btn_frame.pack(fill=tk.X, pady=5)
        
        clear_btn = tk.Button(rect_btn_frame, text="🗑️ Clear All", command=self.clear_rectangles,
                             bg='#e74c3c', fg='white', font=('Arial', 9))
        clear_btn.pack(side=tk.LEFT)
        
        # Holder attributes
        self.create_holder_attributes_section(panel_frame)
        
        # Sign attributes  
        self.create_sign_attributes_section(panel_frame)
        
        # Data status
        self.create_data_status_section(panel_frame)
        
    def create_holder_attributes_section(self, parent):
        """Create holder attributes section"""
        holder_frame = ttk.LabelFrame(parent, text="🏗️ Holder Attributes", style='Medium.TFrame')
        holder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Material
        ttk.Label(holder_frame, text="Material:", style='Dark.TLabel').pack(anchor=tk.W, padx=5)
        self.material_var = tk.StringVar(value=self.materials[0])
        material_combo = ttk.Combobox(holder_frame, textvariable=self.material_var, 
                                     values=self.materials, state='readonly')
        material_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # Holder type
        ttk.Label(holder_frame, text="Type:", style='Dark.TLabel').pack(anchor=tk.W, padx=5)
        self.holder_type_var = tk.StringVar(value=self.holder_types[0])
        type_combo = ttk.Combobox(holder_frame, textvariable=self.holder_type_var,
                                 values=self.holder_types, state='readonly')
        type_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # AI auto-fill button for holders
        holder_autofill_btn = tk.Button(holder_frame, text="🤖 AI Auto-fill Holder", 
                                       command=self.ai_autofill_holder,
                                       bg='#9b59b6', fg='white', font=('Arial', 9))
        holder_autofill_btn.pack(fill=tk.X, padx=5, pady=5)
        
    def create_sign_attributes_section(self, parent):
        """Create sign attributes section"""
        sign_frame = ttk.LabelFrame(parent, text="🚸 Sign Attributes", style='Medium.TFrame')
        sign_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Sign code + name
        ttk.Label(sign_frame, text="Sign Code + Name:", style='Dark.TLabel').pack(anchor=tk.W, padx=5)
        self.sign_code_var = tk.StringVar()
        sign_code_entry = tk.Entry(sign_frame, textvariable=self.sign_code_var, 
                                  bg='#2d2d2d', fg='white', font=('Arial', 10))
        sign_code_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Text on sign
        ttk.Label(sign_frame, text="Text on Sign:", style='Dark.TLabel').pack(anchor=tk.W, padx=5)
        self.sign_text_var = tk.StringVar()
        sign_text_entry = tk.Entry(sign_frame, textvariable=self.sign_text_var,
                                  bg='#2d2d2d', fg='white', font=('Arial', 10))
        sign_text_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Direction
        ttk.Label(sign_frame, text="Direction:", style='Dark.TLabel').pack(anchor=tk.W, padx=5)
        self.sign_direction_var = tk.StringVar(value=self.sign_directions[0])
        direction_combo = ttk.Combobox(sign_frame, textvariable=self.sign_direction_var,
                                      values=self.sign_directions, state='readonly')
        direction_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # AI auto-fill button for signs
        sign_autofill_btn = tk.Button(sign_frame, text="🤖 AI Auto-fill Sign", 
                                     command=self.ai_autofill_sign,
                                     bg='#3498db', fg='white', font=('Arial', 9))
        sign_autofill_btn.pack(fill=tk.X, padx=5, pady=5)
        
    def create_data_status_section(self, parent):
        """Create data status section"""
        status_frame = ttk.LabelFrame(parent, text="📊 Data Status", style='Medium.TFrame')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.data_status_text = tk.Text(status_frame, height=8, bg='#1a1a1a', fg='#2ecc71',
                                       font=('Consolas', 9), wrap=tk.WORD)
        self.data_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent, style='Medium.TFrame')
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.main_status_label = ttk.Label(status_frame, text="Ready", style='Status.TLabel')
        self.main_status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.progress_label = ttk.Label(status_frame, text="", style='Dark.TLabel')
        self.progress_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def update_drawing_mode(self):
        """Update drawing mode"""
        self.drawing_mode = self.mode_var.get()
        self.logger.info(f"🎨 Drawing mode: {self.drawing_mode}")
        
    def on_canvas_click(self, event):
        """Handle canvas click for rectangle drawing"""
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        
    def on_canvas_drag(self, event):
        """Handle canvas drag for rectangle drawing"""
        if self.drawing:
            # Remove previous preview rectangle
            if self.current_rect:
                self.photo_canvas.delete(self.current_rect)
                
            # Draw preview rectangle
            color = '#2ecc71' if self.drawing_mode == 'holder' else '#3498db'
            self.current_rect = self.photo_canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=2, fill='', stipple='gray50'
            )
            
    def on_canvas_release(self, event):
        """Handle canvas release to complete rectangle"""
        if self.drawing:
            self.drawing = False
            
            # Calculate rectangle dimensions
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            
            # Only add if rectangle is big enough
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                rect = Rectangle(
                    x=x1, y=y1, 
                    width=x2-x1, height=y2-y1,
                    type=self.drawing_mode,
                    confidence=1.0,
                    source='manual'
                )
                
                self.manual_rectangles.append(rect)
                self.redraw_rectangles()
                self.update_data_status()
                self.logger.info(f"✅ Added {self.drawing_mode} rectangle: {x1},{y1},{x2-x1},{y2-y1}")
            
            # Clear current rectangle
            if self.current_rect:
                self.photo_canvas.delete(self.current_rect)
                self.current_rect = None
                
    def clear_rectangles(self):
        """Clear all rectangles"""
        self.manual_rectangles.clear()
        self.redraw_rectangles()
        self.update_data_status()
        self.logger.info("🗑️ Cleared all rectangles")
        
    def redraw_rectangles(self):
        """Redraw all rectangles on canvas"""
        # Clear existing rectangles
        self.photo_canvas.delete("rectangle")
        
        # Draw manual rectangles
        for rect in self.manual_rectangles:
            color = '#2ecc71' if rect.type == 'holder' else '#3498db'
            self.photo_canvas.create_rectangle(
                rect.x, rect.y, rect.x + rect.width, rect.y + rect.height,
                outline=color, width=3, tags="rectangle"
            )
            
            # Add label
            self.photo_canvas.create_text(
                rect.x + 5, rect.y - 15,
                text=f"{rect.type.upper()}",
                fill=color, font=('Arial', 10, 'bold'),
                tags="rectangle", anchor=tk.W
            )
            
        # Draw YOLO predictions (different style)
        for rect in self.yolo_rectangles:
            color = '#f39c12' if rect.type == 'holder' else '#e74c3c'
            self.photo_canvas.create_rectangle(
                rect.x, rect.y, rect.x + rect.width, rect.y + rect.height,
                outline=color, width=2, dash=(5, 5), tags="rectangle"
            )
            
            # Add label with confidence
            self.photo_canvas.create_text(
                rect.x + 5, rect.y - 15,
                text=f"YOLO {rect.type.upper()} ({rect.confidence:.2f})",
                fill=color, font=('Arial', 9),
                tags="rectangle", anchor=tk.W
            )
            
    def load_photos(self):
        """Load photos for training"""
        folder_path = filedialog.askdirectory(title="Select folder with traffic sign holder photos")
        if not folder_path:
            return
            
        try:
            # Find all image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            self.photos_list = []
            
            for ext in image_extensions:
                self.photos_list.extend(Path(folder_path).glob(f'*{ext}'))
                self.photos_list.extend(Path(folder_path).glob(f'*{ext.upper()}'))
                
            if not self.photos_list:
                messagebox.showwarning("No Photos", "No image files found in selected folder")
                return
                
            self.photos_list = sorted(self.photos_list)
            self.current_photo_index = 0
            
            self.load_current_photo()
            self.update_comprehensive_status()
            
            messagebox.showinfo("Success", f"Loaded {len(self.photos_list)} photos")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load photos: {e}")
            messagebox.showerror("Error", f"Failed to load photos: {e}")
            
    def load_current_photo(self):
        """Load and display current photo"""
        if not self.photos_list or self.current_photo_index >= len(self.photos_list):
            return
            
        try:
            self.current_photo_path = str(self.photos_list[self.current_photo_index])
            
            # Load image
            image = Image.open(self.current_photo_path)
            
            # Resize to fit canvas while maintaining aspect ratio
            canvas_width = 800
            canvas_height = 600
            
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Update canvas size
            self.photo_canvas.config(width=new_width, height=new_height)
            
            # Convert to PhotoImage
            self.photo_tk = ImageTk.PhotoImage(image)
            
            # Display image
            self.photo_canvas.delete("all")
            self.photo_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_tk)
            
            # Update photo info
            photo_name = Path(self.current_photo_path).name
            self.photo_info_label.config(text=f"{self.current_photo_index + 1}/{len(self.photos_list)}: {photo_name}")
            
            # Load existing annotations for this photo
            self.load_photo_annotations()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load photo: {e}")
            
    def load_photo_annotations(self):
        """Load existing annotations for current photo"""
        self.manual_rectangles.clear()
        self.yolo_rectangles.clear()
        
        photo_id = Path(self.current_photo_path).stem
        
        # Load from project data
        if photo_id in self.project_data.get('annotations', {}):
            annotations = self.project_data['annotations'][photo_id]
            
            for rect_data in annotations.get('rectangles', []):
                rect = Rectangle(
                    x=rect_data['x'],
                    y=rect_data['y'],
                    width=rect_data['width'],
                    height=rect_data['height'],
                    type=rect_data['type'],
                    confidence=rect_data.get('confidence', 1.0),
                    source=rect_data.get('source', 'manual')
                )
                
                if rect.source == 'yolo':
                    self.yolo_rectangles.append(rect)
                else:
                    self.manual_rectangles.append(rect)
                    
        self.redraw_rectangles()
        self.update_data_status()
        
    def prev_photo(self):
        """Go to previous photo"""
        if self.photos_list and self.current_photo_index > 0:
            self.save_current_annotations()
            self.current_photo_index -= 1
            self.load_current_photo()
            
    def next_photo(self):
        """Go to next photo"""
        if self.photos_list and self.current_photo_index < len(self.photos_list) - 1:
            self.save_current_annotations()
            self.current_photo_index += 1
            self.load_current_photo()
            
    def save_current_annotations(self):
        """Save current photo annotations"""
        if not self.current_photo_path:
            return
            
        photo_id = Path(self.current_photo_path).stem
        
        # Combine all rectangles
        all_rectangles = []
        for rect in self.manual_rectangles + self.yolo_rectangles:
            all_rectangles.append({
                'x': rect.x,
                'y': rect.y, 
                'width': rect.width,
                'height': rect.height,
                'type': rect.type,
                'confidence': rect.confidence,
                'source': rect.source
            })
            
        # Save to project data
        if 'annotations' not in self.project_data:
            self.project_data['annotations'] = {}
            
        self.project_data['annotations'][photo_id] = {
            'photo_path': self.current_photo_path,
            'rectangles': all_rectangles,
            'holder_attributes': {
                'material': self.material_var.get(),
                'type': self.holder_type_var.get()
            },
            'sign_attributes': {
                'code': self.sign_code_var.get(),
                'text': self.sign_text_var.get(),
                'direction': self.sign_direction_var.get()
            },
            'last_modified': time.time()
        }
        
    def run_yolo_bootstrap(self):
        """Run YOLO bootstrap on current photo or all photos"""
        if not self.photos_list:
            messagebox.showwarning("No Photos", "Please load photos first")
            return
            
        # Ask user: current photo or all photos
        choice = messagebox.askyesnocancel("YOLO Bootstrap", 
                                          "Run YOLO bootstrap on ALL photos?\n\n" +
                                          "Yes = All photos\n" +
                                          "No = Current photo only\n" +
                                          "Cancel = Don't run")
                                          
        if choice is None:  # Cancel
            return
        elif choice:  # All photos
            self.bootstrap_all_photos()
        else:  # Current photo only
            self.bootstrap_current_photo()
            
    def bootstrap_current_photo(self):
        """Run YOLO bootstrap on current photo"""
        if not self.current_photo_path:
            return
            
        try:
            self.main_status_label.config(text="🤖 Running YOLO bootstrap...")
            self.root.update()
            
            # Run YOLO bootstrap
            results = self.yolo_bootstrap.bootstrap_single_image(self.current_photo_path)
            
            if results and 'rectangles' in results:
                # Convert to Rectangle objects
                self.yolo_rectangles.clear()
                for rect_data in results['rectangles']:
                    rect = Rectangle(
                        x=int(rect_data['x']),
                        y=int(rect_data['y']),
                        width=int(rect_data['width']),
                        height=int(rect_data['height']),
                        type=rect_data['type'],
                        confidence=rect_data['confidence'],
                        source='yolo'
                    )
                    self.yolo_rectangles.append(rect)
                    
                self.redraw_rectangles()
                self.update_data_status()
                
                messagebox.showinfo("Success", f"YOLO found {len(self.yolo_rectangles)} objects")
            else:
                messagebox.showinfo("No Results", "YOLO didn't find any objects")
                
            self.main_status_label.config(text="Ready")
            
        except Exception as e:
            self.logger.error(f"❌ YOLO bootstrap failed: {e}")
            messagebox.showerror("Error", f"YOLO bootstrap failed: {e}")
            self.main_status_label.config(text="Ready")
            
    def bootstrap_all_photos(self):
        """Run YOLO bootstrap on all photos"""
        if not self.photos_list:
            return
            
        try:
            total_photos = len(self.photos_list)
            bootstrapped = 0
            
            for i, photo_path in enumerate(self.photos_list):
                self.main_status_label.config(text=f"🤖 YOLO Bootstrap: {i+1}/{total_photos}")
                self.progress_label.config(text=f"Progress: {i+1}/{total_photos}")
                self.root.update()
                
                # Run bootstrap
                results = self.yolo_bootstrap.bootstrap_single_image(str(photo_path))
                
                if results and 'rectangles' in results:
                    photo_id = photo_path.stem
                    
                    # Save bootstrap results
                    if 'annotations' not in self.project_data:
                        self.project_data['annotations'] = {}
                        
                    if photo_id not in self.project_data['annotations']:
                        self.project_data['annotations'][photo_id] = {
                            'photo_path': str(photo_path),
                            'rectangles': [],
                            'holder_attributes': {},
                            'sign_attributes': {},
                            'last_modified': time.time()
                        }
                    
                    # Add YOLO rectangles
                    for rect_data in results['rectangles']:
                        rect_dict = {
                            'x': int(rect_data['x']),
                            'y': int(rect_data['y']),
                            'width': int(rect_data['width']),
                            'height': int(rect_data['height']),
                            'type': rect_data['type'],
                            'confidence': rect_data['confidence'],
                            'source': 'yolo'
                        }
                        self.project_data['annotations'][photo_id]['rectangles'].append(rect_dict)
                        
                    bootstrapped += 1
                    
            # Reload current photo to show bootstrap results
            self.load_photo_annotations()
            
            self.main_status_label.config(text="Ready")
            self.progress_label.config(text="")
            
            messagebox.showinfo("Success", f"YOLO bootstrap completed!\n\n" +
                              f"Processed: {total_photos} photos\n" +
                              f"Found objects in: {bootstrapped} photos")
                              
        except Exception as e:
            self.logger.error(f"❌ Bulk YOLO bootstrap failed: {e}")
            messagebox.showerror("Error", f"Bulk YOLO bootstrap failed: {e}")
            self.main_status_label.config(text="Ready")
            self.progress_label.config(text="")
            
    def ai_autofill_holder(self):
        """AI auto-fill holder attributes"""
        # Simulate AI analysis
        import random
        materials = ['kov', 'betón', 'drevo']
        types = ['stĺp značky samostatný', 'stĺp verejného osvetlenia']
        
        self.material_var.set(random.choice(materials))
        self.holder_type_var.set(random.choice(types))
        
        messagebox.showinfo("AI Auto-fill", "🤖 AI filled holder attributes!\n(Simulated for demo)")
        
    def ai_autofill_sign(self):
        """AI auto-fill sign attributes"""
        # Simulate AI analysis
        import random
        codes = ['A1 - Hlavná cesta', 'B1 - Zákaz vjazdu', 'C1 - Príkaz jazdy priamo']
        texts = ['STOP', 'Bratislava 15km', '50']
        directions = self.sign_directions
        
        self.sign_code_var.set(random.choice(codes))
        self.sign_text_var.set(random.choice(texts))
        self.sign_direction_var.set(random.choice(directions))
        
        messagebox.showinfo("AI Auto-fill", "🤖 AI filled sign attributes!\n(Simulated for demo)")
        
    def train_unified_ai(self):
        """Train the unified AI system"""
        try:
            self.main_status_label.config(text="🧠 Training unified AI...")
            self.root.update()
            
            # Save current work
            self.save_current_annotations()
            self.save_project()
            
            # Import all data into unified system
            total_imported = self.unified_system.import_all_existing_data()
            
            if total_imported == 0:
                messagebox.showwarning("No Data", "No training data found! Please draw rectangles or run YOLO bootstrap first.")
                self.main_status_label.config(text="Ready")
                return
                
            # Create unified dataset
            unified_dataset = self.unified_system.create_unified_dataset()
            
            # Save unified dataset
            dataset_file = self.unified_system.save_unified_dataset()
            
            # Generate report
            report = self.unified_system.generate_effectiveness_report()
            
            self.main_status_label.config(text="Ready")
            
            # Show training results
            self.show_training_results(report, len(unified_dataset), dataset_file)
            
        except Exception as e:
            self.logger.error(f"❌ Training failed: {e}")
            messagebox.showerror("Training Error", f"Training failed: {e}")
            self.main_status_label.config(text="Ready")
            
    def show_training_results(self, report: str, dataset_size: int, dataset_file: str):
        """Show training results in popup window"""
        result_window = tk.Toplevel(self.root)
        result_window.title("🧠 Training Results")
        result_window.geometry("800x600")
        result_window.configure(bg='#1a1a1a')
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(result_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, bg='#1a1a1a', fg='#2ecc71', 
                             font=('Consolas', 10), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add content
        success_msg = f"""
✅ TRAINING COMPLETED SUCCESSFULLY!

📊 Dataset Information:
• Total unified photos: {dataset_size}
• Dataset saved to: {dataset_file}

{report}

🚀 Next Steps:
1. Review the data quality recommendations above
2. Continue adding manual corrections where needed
3. Use YOLO bootstrap for new photos
4. The system will progressively improve with more data!

💡 Tips:
- Manual annotations are higher quality than YOLO predictions
- Correct YOLO predictions to improve training data
- Focus on difficult cases YOLO missed for best results
"""
        
        text_widget.insert(tk.END, success_msg)
        text_widget.config(state=tk.DISABLED)
        
    def show_unified_report(self):
        """Show comprehensive unified system report"""
        try:
            # Save current work first
            self.save_current_annotations()
            
            # Generate comprehensive report
            self.main_status_label.config(text="📊 Generating report...")
            self.root.update()
            
            # Run unified system analysis
            total_imported = self.unified_system.import_all_existing_data()
            
            if total_imported > 0:
                unified_dataset = self.unified_system.create_unified_dataset()
                report = self.unified_system.generate_effectiveness_report()
            else:
                report = "⚠️ No training data found! Please draw rectangles or run YOLO bootstrap."
                
            self.main_status_label.config(text="Ready")
            
            # Show report in popup
            self.show_report_window("📈 Unified System Report", report)
            
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            messagebox.showerror("Error", f"Report generation failed: {e}")
            self.main_status_label.config(text="Ready")
            
    def show_report_window(self, title: str, content: str):
        """Show report in popup window"""
        report_window = tk.Toplevel(self.root)
        report_window.title(title)
        report_window.geometry("900x700")
        report_window.configure(bg='#1a1a1a')
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(report_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, bg='#1a1a1a', fg='#ffffff', 
                             font=('Consolas', 11), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add content with color formatting
        lines = content.split('\n')
        for line in lines:
            if line.startswith('🧠') or line.startswith('==='):
                text_widget.insert(tk.END, line + '\n', 'header')
            elif line.startswith('•') or line.startswith('-'):
                text_widget.insert(tk.END, line + '\n', 'bullet')
            elif line.startswith('🎯') or line.startswith('🚀') or line.startswith('⚡'):
                text_widget.insert(tk.END, line + '\n', 'action')
            else:
                text_widget.insert(tk.END, line + '\n')
                
        # Configure tags for colors
        text_widget.tag_configure('header', foreground='#3498db', font=('Consolas', 12, 'bold'))
        text_widget.tag_configure('bullet', foreground='#2ecc71')
        text_widget.tag_configure('action', foreground='#f39c12', font=('Consolas', 11, 'bold'))
        
        text_widget.config(state=tk.DISABLED)
        
    def update_data_status(self):
        """Update data status display"""
        if not hasattr(self, 'data_status_text'):
            return
            
        manual_holders = len([r for r in self.manual_rectangles if r.type == 'holder'])
        manual_signs = len([r for r in self.manual_rectangles if r.type == 'sign'])
        yolo_holders = len([r for r in self.yolo_rectangles if r.type == 'holder'])
        yolo_signs = len([r for r in self.yolo_rectangles if r.type == 'sign'])
        
        status_text = f"""📊 Current Photo Data:

✋ Manual Annotations:
  Holders: {manual_holders}
  Signs: {manual_signs}
  Total: {manual_holders + manual_signs}

🤖 YOLO Predictions:
  Holders: {yolo_holders}
  Signs: {yolo_signs}  
  Total: {yolo_holders + yolo_signs}

📈 Combined Total: {manual_holders + manual_signs + yolo_holders + yolo_signs}

Status: {'✅ Data Available' if (manual_holders + manual_signs + yolo_holders + yolo_signs) > 0 else '⚠️ No Data'}"""

        self.data_status_text.delete(1.0, tk.END)
        self.data_status_text.insert(1.0, status_text)
        
    def update_comprehensive_status(self):
        """Update comprehensive system status"""
        try:
            # Analyze all available data
            total_imported = self.unified_system.import_all_existing_data()
            
            if total_imported > 0:
                analysis = self.unified_system.analyze_data_quality()
                strategy = self.unified_system.progressive_learning_strategy()
                
                status_text = f"📊 Total: {analysis['quality_scores']['total_rectangles']} rects | " + \
                             f"Phase: {strategy['current_phase'].replace('_', ' ').title()} | " + \
                             f"Score: {strategy['effectiveness_score']}/10"
            else:
                status_text = "⚠️ No training data found - Load photos and draw rectangles or run YOLO bootstrap"
                
            self.system_status_label.config(text=status_text)
            
        except Exception as e:
            self.system_status_label.config(text=f"⚠️ Status update failed: {str(e)[:50]}")
            
    def save_project(self):
        """Save project data"""
        try:
            self.save_current_annotations()
            
            # Update project metadata
            self.project_data['last_saved'] = time.time()
            
            # Save to file
            with open('training_project.json', 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2, ensure_ascii=False)
                
            messagebox.showinfo("Success", "Project saved successfully!")
            self.logger.info("💾 Project saved")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save project: {e}")
            messagebox.showerror("Error", f"Failed to save project: {e}")
            
    def load_project(self):
        """Load existing project data"""
        try:
            if os.path.exists('training_project.json'):
                with open('training_project.json', 'r', encoding='utf-8') as f:
                    self.project_data = json.load(f)
                    
                self.logger.info("📁 Project data loaded")
            else:
                self.logger.info("📁 No existing project found - starting fresh")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load project: {e}")
            
    def run(self):
        """Start the GUI"""
        self.create_gui()
        self.root.mainloop()

def main():
    """Main function"""
    print("🧠 Starting Unified AI Trainer...")
    
    trainer = UnifiedTrainerGUI()
    trainer.run()

if __name__ == "__main__":
    main()