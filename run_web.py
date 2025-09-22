#!/usr/bin/env python3
"""
Team Velocity Cycling Dashboard - Web Application Launcher

This script launches the Flask web application for the cycling performance dashboard.
It provides a professional website similar to UCI Kigali 2025 for cycling team management.
"""

import os
import sys
import webbrowser
from threading import Timer

def open_browser():
    """Open the web browser after a short delay"""
    webbrowser.open('http://localhost:5000')

def main():
    """Main function to launch the web application"""
    print("🚴‍♂️ Team Velocity Cycling Dashboard")
    print("=" * 50)
    print("Starting the web application...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🏁 Race results at: http://localhost:5000/results")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    # Open browser after 2 seconds
    Timer(2.0, open_browser).start()
    
    # Import and run the Flask app
    try:
        from app_web import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Error importing Flask app: {e}")
        print("Make sure you have installed the requirements:")
        print("pip install -r requirements_web.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
