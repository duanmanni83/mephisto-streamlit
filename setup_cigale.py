#!/usr/bin/env python3
"""
CIGALE Auto-installer for Streamlit Cloud
在 Streamlit 启动前自动安装 CIGALE
"""

import subprocess
import sys
import os

def install_cigale():
    """Install CIGALE from source if not already installed."""
    try:
        import pcigale
        print("CIGALE already installed.")
        return True
    except ImportError:
        print("CIGALE not found. Installing from source...")

    # Clone and install CIGALE
    cigale_dir = "/tmp/cigale-v2025.0"

    if not os.path.exists(cigale_dir):
        print("Cloning CIGALE repository...")
        result = subprocess.run(
            ["git", "clone", "https://gitlab.lam.fr/cigale/cigale.git", cigale_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"Failed to clone CIGALE: {result.stderr}")
            return False

    print("Building CIGALE database...")
    result = subprocess.run(
        ["python", "setup.py", "build"],
        cwd=cigale_dir,
        capture_output=True,
        text=True,
        timeout=300
    )

    print("Installing CIGALE...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", cigale_dir],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode == 0:
        print("CIGALE installed successfully!")
        return True
    else:
        print(f"Failed to install CIGALE: {result.stderr}")
        return False

if __name__ == "__main__":
    success = install_cigale()
    sys.exit(0 if success else 1)
