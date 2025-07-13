#!/usr/bin/env python3
"""
Test runner script for the Product Service.

This script provides convenient commands to run different types of tests.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found. Make sure pytest is installed.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in {description}: {e}")
        return False

def main():
    """Main test runner function."""
    # Change to the product directory
    os.chdir(Path(__file__).parent)
    
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <command>")
        print("\nAvailable commands:")
        print("  unit                   - Run unit tests only")
        print("  infra                  - Run infrastructure layer tests")
        print("  core                   - Run core layer tests")
        print("  api                    - Run API layer tests")
        print("  all                    - Run all tests")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    match command:
        case "all":
            success = run_command(
                ["pytest", "unit/", "-v"],
                "All tests",
            )
        case "api":
            success = run_command(
                ["pytest", "unit/api/", "-v"],
                "API layer tests",
            )
        case "core":
            success = run_command(
                ["pytest", "unit/core/", "-v"],
                "Core layer tests",
            )
        case "infra":
            success = run_command(
                ["pytest", "unit/infrastructure/", "-v"],
                "Infrastructure layer tests",
            )
        case "unit":
            success = run_command(
                ["pytest", "-m", "unit", "-v"],
                "Unit tests",
            )
        case _:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
    
    if success:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
