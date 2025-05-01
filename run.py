#!/usr/bin/env python3
"""
Run script for the Cognitive Email Ecosystem demonstration
"""

from email_interface import app

if __name__ == "__main__":
    print("Starting Cognitive Email Ecosystem web interface...")
    print("Open your browser and navigate to: http://localhost:5000")
    app.run(debug=True) 