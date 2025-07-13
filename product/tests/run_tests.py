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
        print("  integration            - Run integration tests only")
        print("  infrastructure         - Run infrastructure layer tests")
        print("  infrastructure-database-conn - Run infrastructure database connection tests")
        print("  infrastructure-database-query - Run infrastructure database query tests")
        print("  infrastructure-database-write - Run infrastructure database write tests")
        print("  infrastructure-cache-conn - Run infrastructure cache connection tests")
        print("  infrastructure-cache-ops - Run infrastructure cache operations tests")
        print("  infrastructure-data-access - Run infrastructure data access tests")
        print("  database            - Run database manager tests")
        print("  database-conn       - Run database connection tests")
        print("  database-query      - Run database query tests")
        print("  database-write      - Run database write tests")
        print("  cache               - Run cache manager tests")
        print("  cache-conn          - Run cache connection tests")
        print("  cache-ops           - Run cache operations tests")
        print("  data-access         - Run data access layer tests")
        print("  data-access-init    - Run data access initialization tests")
        print("  data-access-products - Run data access product tests")
        print("  data-access-votes   - Run data access vote tests")
        print("  core                - Run core layer tests")
        print("  core-services       - Run core services tests")
        print("  core-product        - Run core product service tests")
        print("  core-vote           - Run core vote service tests")
        print("  core-system         - Run core system service tests")
        print("  api                 - Run API layer tests")
        print("  api-products        - Run API product endpoint tests")
        print("  api-votes           - Run API vote endpoint tests")
        print("  api-system          - Run API system endpoint tests")
        print("  api-frontend        - Run API frontend endpoint tests")
        print("  api-dependencies    - Run API dependencies tests")
        print("  api-middleware      - Run API middleware tests")
        print("  all                 - Run all tests")
        print("  coverage            - Run tests with coverage report")
        print("  fast                - Run tests in parallel (fast)")
        print("  install             - Install test dependencies")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    match command:
        case "install":
            success = run_command(
                ["pip", "install", "-r", "requirements-test.txt"],
                "Installing test dependencies",
            )
        case "unit":
            success = run_command(
                ["pytest", "-m", "unit", "-v"],
                "Unit tests",
            )
        case "integration":
            success = run_command(
                ["pytest", "-m", "integration", "-v"],
                "Integration tests",
            )
        case "infrastructure":
            success = run_command(
                ["pytest", "unit/infrastructure/", "-v"],
                "Infrastructure layer tests",
            )
        case "infrastructure-database":
            success = run_command(
                ["pytest", "unit/infrastructure/database/", "-v"],
                "Infrastructure database tests",
            )
        case "infrastructure-cache":
            success = run_command(
                ["pytest", "unit/infrastructure/cache/", "-v"],
                "Infrastructure cache tests",
            )
        case "infrastructure-data-access":
            success = run_command(
                ["pytest", "unit/infrastructure/data_access/", "-v"],
                "Infrastructure data access tests",
            )
        case "database":
            success = run_command(
                ["pytest", "unit/infrastructure/database/", "-v"],
                "Database manager tests",
            )
        case "database-conn":
            success = run_command(
                ["pytest", "unit/infrastructure/database/test_connection_management.py", "-v"],
                "Database connection tests",
            )
        case "database-query":
            success = run_command(
                ["pytest", "unit/infrastructure/database/test_query_operations.py", "-v"],
                "Database query tests",
            )
        case "database-write":
            success = run_command(
                ["pytest", "unit/infrastructure/database/test_write_operations.py", "-v"],
                "Database write tests",
            )
        case "cache":
            success = run_command(
                ["pytest", "unit/infrastructure/cache/", "-v"],
                "Cache manager tests",
            )
        case "cache-conn":
            success = run_command(
                ["pytest", "unit/infrastructure/cache/test_connection_management.py", "-v"],
                "Cache connection tests",
            )
        case "cache-ops":
            success = run_command(
                ["pytest", "unit/infrastructure/cache/test_cache_operations.py", "-v"],
                "Cache operations tests",
            )
        case "data-access":
            success = run_command(
                ["pytest", "unit/infrastructure/data_access/", "-v"],
                "Data access layer tests",
            )
        case "data-access-init":
            success = run_command(
                ["pytest", "unit/infrastructure/data_access/test_initialization.py", "-v"],
                "Data access initialization tests",
            )
        case "data-access-products":
            success = run_command(
                ["pytest", "unit/infrastructure/data_access/test_product_operations.py", "-v"],
                "Data access product tests",
            )
        case "data-access-votes":
            success = run_command(
                ["pytest", "unit/infrastructure/data_access/test_vote_operations.py", "-v"],
                "Data access vote tests",
            )
        case "core":
            success = run_command(
                ["pytest", "unit/core/", "-v"],
                "Core layer tests",
            )
        case "core-services":
            success = run_command(
                ["pytest", "unit/core/services/", "-v"],
                "Core services tests",
            )
        case "core-product":
            success = run_command(
                ["pytest", "unit/core/services/test_product_service.py", "-v"],
                "Core product service tests",
            )
        case "core-vote":
            success = run_command(
                ["pytest", "unit/core/services/test_vote_service.py", "-v"],
                "Core vote service tests",
            )
        case "core-system":
            success = run_command(
                ["pytest", "unit/core/services/test_system_service.py", "-v"],
                "Core system service tests",
            )
        case "api":
            success = run_command(
                ["pytest", "unit/api/", "-v"],
                "API layer tests",
            )
        case "api-products":
            success = run_command(
                ["pytest", "unit/api/routes/test_products.py", "-v"],
                "API product endpoint tests",
            )
        case "api-votes":
            success = run_command(
                ["pytest", "unit/api/routes/test_votes.py", "-v"],
                "API vote endpoint tests",
            )
        case "api-system":
            success = run_command(
                ["pytest", "unit/api/routes/test_system.py", "-v"],
                "API system endpoint tests",
            )
        case "api-frontend":
            success = run_command(
                ["pytest", "unit/api/routes/test_frontend.py", "-v"],
                "API frontend endpoint tests",
            )
        case "api-dependencies":
            success = run_command(
                ["pytest", "unit/api/test_dependencies.py", "-v"],
                "API dependencies tests",
            )
        case "api-middleware":
            success = run_command(
                ["pytest", "unit/api/test_middleware.py", "-v"],
                "API middleware tests",
            )
        case "all":
            success = run_command(
                ["pytest", "-v"],
                "All tests",
            )
        case "coverage":
            success = run_command(
                ["pytest", "--cov=app", "--cov-report=html", "--cov-report=term-missing", "-v"],
                "Tests with coverage",
            )
        case "fast":
            success = run_command(
                ["pytest", "-n", "auto", "-v"],
                "Tests in parallel",
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
