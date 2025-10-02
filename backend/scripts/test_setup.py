#!/usr/bin/env python3
"""
HR Agent Backend Setup Test Script

This script tests the basic setup and configuration of the HR Agent Backend.
"""

import sys
import os
from pathlib import Path
import asyncio
import importlib

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    required_modules = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'alembic',
        'pydantic',
        'asyncpg',
        'redis',
        'langchain',
        'openai',
        'multipart',
        'jose',
        'passlib',
        'bcrypt',
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        print("Please install missing dependencies with: pip install -r requirements.txt")
        return False
    
    print("All required modules imported successfully!")
    return True


def test_app_imports():
    """Test if application modules can be imported"""
    print("\nTesting application imports...")
    
    app_modules = [
        'app.core.config',
        'app.core.database',
        'app.core.security',
        'app.models.base',
        'app.models.user',
        'app.schemas.user',
        'app.api.v1.api',
        'app.services.llm_service',
        'app.utils.file_utils',
    ]
    
    failed_imports = []
    
    for module in app_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import application modules: {', '.join(failed_imports)}")
        return False
    
    print("All application modules imported successfully!")
    return True


def test_configuration():
    """Test application configuration"""
    print("\nTesting configuration...")
    
    try:
        from app.core.config import settings
        
        # Test basic settings
        assert settings.PROJECT_NAME, "PROJECT_NAME not set"
        assert settings.VERSION, "VERSION not set"
        assert settings.API_V1_STR, "API_V1_STR not set"
        
        print(f"✓ Project Name: {settings.PROJECT_NAME}")
        print(f"✓ Version: {settings.VERSION}")
        print(f"✓ API Prefix: {settings.API_V1_STR}")
        print(f"✓ Debug Mode: {settings.DEBUG}")
        print(f"✓ Host: {settings.HOST}")
        print(f"✓ Port: {settings.PORT}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


async def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from app.core.database import get_async_engine
        from app.core.config import settings
        
        engine = get_async_engine()
        
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            assert result.scalar() == 1
        
        await engine.dispose()
        
        print("✓ Database connection successful")
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False


def test_fastapi_app():
    """Test FastAPI application creation"""
    print("\nTesting FastAPI application...")
    
    try:
        from main import create_application
        
        app = create_application()
        
        assert app.title, "App title not set"
        assert app.version, "App version not set"
        
        print(f"✓ FastAPI app created: {app.title} v{app.version}")
        return True
        
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        return False


def test_file_structure():
    """Test if required files and directories exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'alembic.ini',
        '.env.example',
        'app/__init__.py',
        'app/core/config.py',
        'app/core/database.py',
        'app/models/__init__.py',
        'app/schemas/__init__.py',
        'app/api/__init__.py',
        'app/services/__init__.py',
        'app/utils/__init__.py',
    ]
    
    required_dirs = [
        'app',
        'app/core',
        'app/models',
        'app/schemas',
        'app/api',
        'app/api/v1',
        'app/services',
        'app/utils',
        'alembic',
        'alembic/versions',
        'scripts',
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not (backend_dir / file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    for dir_path in required_dirs:
        if not (backend_dir / dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✓ {dir_path}/")
    
    if missing_files or missing_dirs:
        if missing_files:
            print(f"\nMissing files: {', '.join(missing_files)}")
        if missing_dirs:
            print(f"Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("All required files and directories exist!")
    return True


async def main():
    """Run all tests"""
    print("HR Agent Backend Setup Test")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_imports),
        ("Application Imports", test_app_imports),
        ("Configuration", test_configuration),
        ("FastAPI App", test_fastapi_app),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your HR Agent Backend is ready to run.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and update the values")
        print("2. Set up your database: python scripts/db_manager.py init")
        print("3. Start the application: python scripts/start.py dev")
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please fix the issues before running the application.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())