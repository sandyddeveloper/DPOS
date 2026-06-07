"""
Global constants, paths, env config.
"""
import os
import sys

# Support PyInstaller frozen desktop application path resolution
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    BASE_DIR = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(RESOURCE_DIR)  # Project root directory

DATA_DIR = os.path.join(BASE_DIR, "data")
