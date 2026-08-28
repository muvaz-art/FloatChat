import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.streamlit_app import main

if __name__ == "__main__":
    main()
