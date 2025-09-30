#!/usr/bin/env python3
"""
🔧 EXE Builder for SmartMap Automation Suite
============================================
Creates a standalone Windows EXE from the GUI application

This will create:
- SmartMapBot.exe - Standalone executable
- No Python installation required to run
- All dependencies included
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages for building EXE"""
    print("📦 Installing build requirements...")
    
    packages = [
        'pyinstaller',
        'selenium', 
        'webdriver-manager',
        'python-dotenv',
        'loguru',
        'openai',
        'requests',
        'pillow'
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                      capture_output=True, text=True)
    
    print("✅ All packages installed!")

def build_exe():
    """Build the EXE using PyInstaller"""
    print("🔨 Building SmartMapBot.exe...")
    
    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # Single EXE file
        '--windowed',                   # No console window
        '--name=SmartMapBot',           # EXE name
        '--add-data=.env;.',           # Include .env file if exists
        '--add-data=*.json;.',         # Include JSON databases if exist
        '--hidden-import=selenium',
        '--hidden-import=openai',
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
        'SmartMapBot_GUI.py'
    ]
    
    # Remove data files that don't exist
    if not os.path.exists('.env'):
        cmd = [c for c in cmd if not c.startswith('--add-data=.env')]
    if not any(os.path.exists(f) for f in ['*.json']):
        cmd = [c for c in cmd if not c.startswith('--add-data=*.json')]
        
    try:           
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("🎉 EXE built successfully!")
            print("📁 Location: dist/SmartMapBot.exe")
            print("📊 File size: ~50-100MB (includes Python + all libraries)")
            print()
            print("✅ You can now distribute SmartMapBot.exe to any Windows computer!")
            print("✅ No Python installation required on target machines!")
        else:
            print(f"❌ Build failed: {result.stderr}")
            print(f"Output: {result.stdout}")
            
    except Exception as e:
        print(f"❌ Error running PyInstaller: {e}")

def create_installer_script():
    """Create an NSIS installer script"""
    nsis_script = '''
; SmartMapBot Installer Script
!define APPNAME "SmartMap Automation Suite"
!define COMPANYNAME "SmartMap Tools"
!define DESCRIPTION "Automated holder and sign processing for SmartMap"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://github.com/DMNDLR/HOLDERBOT"
!define UPDATEURL "https://github.com/DMNDLR/SIGNBOT"
!define ABOUTURL "https://github.com/DMNDLR"

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${APPNAME}"
Name "${APPNAME}"
OutFile "SmartMapBot_Installer.exe"

Page directory
Page instfiles

Section "install"
    SetOutPath $INSTDIR
    File "dist\\SmartMapBot.exe"
    
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    CreateDirectory "$SMPROGRAMS\\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\SmartMapBot.exe"
    CreateShortcut "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    
    CreateShortcut "$DESKTOP\\SmartMapBot.lnk" "$INSTDIR\\SmartMapBot.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "QuietUninstallString" "$INSTDIR\\uninstall.exe /S"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\SmartMapBot.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoRepair" 1
    
SectionEnd

Section "uninstall"
    Delete "$INSTDIR\\SmartMapBot.exe"
    Delete "$INSTDIR\\uninstall.exe"
    
    Delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\${APPNAME}"
    
    Delete "$DESKTOP\\SmartMapBot.lnk"
    
    RMDir "$INSTDIR"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
SectionEnd
'''
    
    with open('SmartMapBot_Installer.nsi', 'w') as f:
        f.write(nsis_script)
        
    print("📦 NSIS installer script created: SmartMapBot_Installer.nsi")
    print("💡 To create installer: Install NSIS and run: makensis SmartMapBot_Installer.nsi")

def main():
    print("🔧 SmartMapBot EXE Builder")
    print("=" * 40)
    print()
    
    choice = input("What would you like to do?\n1. Build EXE only\n2. Install requirements first, then build\n3. Create installer script\nChoice (1-3): ").strip()
    
    if choice == '2':
        install_requirements()
        print()
        
    if choice in ['1', '2']:
        build_exe()
        print()
        print("🚀 Next steps:")
        print("1. Test dist/SmartMapBot.exe")
        print("2. Distribute to users")
        print("3. Optional: Create installer with choice 3")
        
    elif choice == '3':
        create_installer_script()
        
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
