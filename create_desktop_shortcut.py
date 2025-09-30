#!/usr/bin/env python3
"""
Create Desktop Shortcut for SmartMap Automation Suite
====================================================
This script creates a Windows desktop shortcut (.lnk) file that points to 
the SmartMapBot GUI and uses the proper square logo icon.

Updated version includes:
- Clean interface without 'Available Data' sections
- Nuclear fix for photo ID 7 classification
- Advanced multi-crop majority voting analysis
- Colorful accent line animations
- Professional dark theme design
"""

import os
import sys
from pathlib import Path

def create_desktop_shortcut():
    """Create a Windows desktop shortcut for the SmartMap GUI"""
    
    try:
        # Try to use win32com.client for proper .lnk creation
        import win32com.client
        
        # Get paths
        desktop_path = Path.home() / "Desktop"
        script_dir = Path(__file__).parent.absolute()
        gui_script = script_dir / "SmartMapBot_GUI.py"
        icon_file = script_dir / "smartmap_suite.ico"
        
        # Create Windows shortcut object
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut_path = desktop_path / "SM HOLDERBOT.lnk"
        shortcut = shell.CreateShortCut(str(shortcut_path))
        
        # Configure shortcut properties
        shortcut.Targetpath = sys.executable  # Python executable
        shortcut.Arguments = f'"{gui_script}"'  # Path to our GUI script
        shortcut.WorkingDirectory = str(script_dir)  # Set working directory
        shortcut.WindowStyle = 1  # Normal window
        
        # Set icon if available
        if icon_file.exists():
            shortcut.IconLocation = f"{icon_file},0"  # Use our square logo icon
            print(f"✅ Using square logo icon: {icon_file}")
        else:
            print("⚠️ Square logo icon not found, using default")
        
        # Set description
        shortcut.Description = "SM HOLDERBOT v1.0 - AI-Powered Traffic Management Suite"
        
        # Save the shortcut
        shortcut.save()
        print(f"✅ Desktop shortcut created successfully!")
        print(f"📍 Shortcut location: {shortcut_path}")
        print(f"🎯 Target: Python {gui_script}")
        print(f"📁 Working directory: {script_dir}")
        
        return True
        
    except ImportError:
        print("❌ win32com.client not available. Installing pywin32...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
            print("✅ pywin32 installed successfully!")
            print("🔄 Please run this script again to create the desktop shortcut.")
            return False
        except Exception as e:
            print(f"❌ Failed to install pywin32: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Failed to create desktop shortcut: {e}")
        return False

def create_simple_batch_file():
    """Create a simple .bat file as fallback if .lnk creation fails"""
    try:
        desktop_path = Path.home() / "Desktop"
        script_dir = Path(__file__).parent.absolute()
        gui_script = script_dir / "SmartMapBot_GUI.py"
        
        batch_file = desktop_path / "SM HOLDERBOT.bat"
        
        batch_content = f'''@echo off
cd /d "{script_dir}"
python "{gui_script}"
pause
'''
        
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"✅ Backup batch file created: {batch_file}")
        print("📝 You can double-click this .bat file to run the GUI")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create batch file: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating desktop shortcut for SM HOLDERBOT...")
    print("=" * 60)
    
    # Try to create proper .lnk shortcut first
    success = create_desktop_shortcut()
    
    if not success:
        print("\n🔄 Trying alternative batch file method...")
        create_simple_batch_file()
    
    print("\n" + "=" * 60)
    print("✨ Shortcut creation process completed!")
    print("\n📋 How to use:")
    print("1. Look for 'SM HOLDERBOT' on your desktop")
    print("2. Double-click to launch the updated GUI (without 'Available Data' sections)")
    print("3. The GUI features AI-powered holder analysis and sign detection")
    print("4. Includes nuclear fix for photo ID 7 classification issues")
    print("5. Clean interface with colorful accent animations")
    
    input("\nPress Enter to exit...")
