#!/usr/bin/env python3
"""
Simple launcher script for development testing
"""

import sys
import os
import subprocess

def main():
    """Launch the theme monitor application"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'main.py')

    if not os.path.exists(main_script):
        print("Error: main.py not found in current directory")
        return 1

    try:
        # Launch the main application
        subprocess.run([sys.executable, main_script], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error launching application: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0

if __name__ == "__main__":
    sys.exit(main())
