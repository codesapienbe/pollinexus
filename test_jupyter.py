#!/usr/bin/env python3
"""
Test script to verify Jupyter installation and configuration.
"""

import sys
import subprocess
import os
from pathlib import Path

def test_jupyter_installation():
    """Test if Jupyter is properly installed."""
    print("Testing Jupyter installation...")
    
    try:
        # Test if jupyter is available
        result = subprocess.run([sys.executable, "-m", "jupyter", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ Jupyter version: {result.stdout.strip()}")
        else:
            print(f"✗ Jupyter not found: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error testing Jupyter: {e}")
        return False
    
    try:
        # Test if jupyter lab is available
        result = subprocess.run([sys.executable, "-m", "jupyter", "lab", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ JupyterLab version: {result.stdout.strip()}")
        else:
            print(f"✗ JupyterLab not found: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error testing JupyterLab: {e}")
        return False
    
    return True

def test_notebook_directory():
    """Test if notebook directory exists and is accessible."""
    print("\nTesting notebook directory...")
    
    notebook_dir = Path("notebooks")
    if notebook_dir.exists():
        print(f"✓ Notebook directory exists: {notebook_dir.absolute()}")
        
        # List notebook files
        notebook_files = list(notebook_dir.glob("*.ipynb"))
        if notebook_files:
            print(f"✓ Found {len(notebook_files)} notebook files:")
            for nb in notebook_files:
                print(f"  - {nb.name}")
        else:
            print("⚠ No .ipynb files found in notebooks directory")
    else:
        print(f"✗ Notebook directory not found: {notebook_dir.absolute()}")
        return False
    
    return True

def test_port_availability():
    """Test if ports 8000 and 8888 are available."""
    print("\nTesting port availability...")
    
    import socket
    
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    ports_to_test = [8000, 8888]
    for port in ports_to_test:
        if is_port_available(port):
            print(f"✓ Port {port} is available")
        else:
            print(f"✗ Port {port} is already in use")
            return False
    
    return True

def main():
    """Run all tests."""
    print("Jupyter Setup Test")
    print("=" * 50)
    
    tests = [
        ("Jupyter Installation", test_jupyter_installation),
        ("Notebook Directory", test_notebook_directory),
        ("Port Availability", test_port_availability),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Error in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! Jupyter should work correctly.")
        print("\nTo start Jupyter Lab manually:")
        print("  uv run jupyter lab --no-browser --ip=0.0.0.0 --port=8888 --notebook-dir=notebooks")
    else:
        print("✗ Some tests failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 