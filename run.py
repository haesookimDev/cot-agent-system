#!/usr/bin/env python3
"""
Simple runner script for CoT Agent System.

This script provides an easy way to run the CoT Agent System without
needing to install it as a package first.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the CLI
try:
    from cot_agent_system.cli import cli
    
    if __name__ == "__main__":
        cli()
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n💡 Solutions:")
    print("1. Run setup first: ./setup.sh")
    print("2. Activate virtual environment: source .venv/bin/activate")
    print("3. Install dependencies: pip install -e .")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)