#!/usr/bin/env python
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    
    # Load test environment variables
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    # Set environment variables if not already set
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/webhook_service_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    
    # Add the current directory to PYTHONPATH
    os.environ["PYTHONPATH"] = f"{os.environ.get('PYTHONPATH', '')}:{script_dir}"
    
    # Install the package in development mode
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
    
    # Run pytest with coverage
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
        "--asyncio-mode=auto"
    ])
    
    # Print result
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main() 