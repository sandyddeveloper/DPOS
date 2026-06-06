"""
Build script to package DPOS as a standalone desktop application.
"""
import os
import sys
import subprocess

def ensure_valid_ico():
    """Generates a premium concentric circle app logo dynamically if icons are missing or 0 bytes."""
    from PIL import Image, ImageDraw
    import os
    
    png_path = os.path.join("assets", "icons", "tray_icon.png")
    ico_path = os.path.join("assets", "icons", "app_icon.ico")
    
    # Create directory if not exists
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    
    # Check if files are missing or empty
    need_generation = (
        not os.path.exists(png_path) or os.path.getsize(png_path) == 0 or
        not os.path.exists(ico_path) or os.path.getsize(ico_path) == 0
    )
    
    if need_generation:
        try:
            print("Generating a premium concentric circle app logo dynamically...")
            # Create a 256x256 image with a dark space-blue background
            img = Image.new("RGBA", (256, 256), (30, 30, 46, 255))
            draw = ImageDraw.Draw(img)

            # Draw a beautiful neon-cyan circle
            draw.ellipse((20, 20, 236, 236), fill=(0, 229, 255, 255), outline=None)

            # Draw a dark space-blue inner circle to make it look like a sleek OS ring logo
            draw.ellipse((65, 65, 191, 191), fill=(30, 30, 46, 255), outline=None)
            
            # Draw a central cyan dot
            draw.ellipse((105, 105, 151, 151), fill=(0, 229, 255, 255), outline=None)

            # Save PNG and multi-size ICO
            img.save(png_path, format="PNG")
            img.save(
                ico_path, 
                format="ICO", 
                sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
            )
            print("Successfully generated valid tray_icon.png and app_icon.ico.")
        except Exception as e:
            print(f"Error generating icon: {e}")

def main():
    print("Compiling DPOS into a standalone desktop application...")
    ensure_valid_ico()
    
    # Path to virtual env python and pyinstaller
    venv_pyinstaller = os.path.join(".venv", "Scripts", "pyinstaller.exe")
    if not os.path.exists(venv_pyinstaller):
        venv_pyinstaller = "pyinstaller"  # Fallback to system pyinstaller
        
    cmd = [
        venv_pyinstaller,
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon=assets/icons/app_icon.ico",
        "--name=DPOS",
        "--add-data=assets;assets",
        "--add-data=modules/workspace/templates;modules/workspace/templates",
        "main.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        
        # Run registration steps on local system immediately
        print("\nConfiguring Windows shortcuts, Task Scheduler, and Registry entries...")
        try:
            # Temporarily add current path to resolve app.py imports
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from app import register_windows_daily_scan_task, create_desktop_shortcut, register_windows_uninstall_entry
            register_windows_daily_scan_task()
            create_desktop_shortcut()
            register_windows_uninstall_entry()
            print("System integration configuration complete!")
        except Exception as ex:
            print(f"Warning: Local system registration skipped or failed: {ex}")
            
        print("\n" + "="*50)
        print("Success! Desktop application compiled successfully.")
        print("You can find the packaged application in: dist/DPOS")
        print("Execute dist/DPOS/DPOS.exe to run the application.")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
