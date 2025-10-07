"""
Setup script for E-Modal Management System
This script helps initialize the system
"""

import os
import sys
import subprocess

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed!")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.9+"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 9:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.9+ is required")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    return run_command(
        "pip install -r requirements.txt",
        "Installing Python packages"
    )

def check_postgresql():
    """Check if PostgreSQL is accessible"""
    print_header("Checking PostgreSQL")
    result = run_command(
        "psql --version",
        "Checking PostgreSQL installation"
    )
    if result:
        print("✅ PostgreSQL is installed")
    else:
        print("⚠️  PostgreSQL not found in PATH")
        print("Please ensure PostgreSQL is installed and accessible")
    return result

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    directories = ['storage', 'storage/users', 'logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created {directory}")
        else:
            print(f"ℹ️  {directory} already exists")
    
    return True

def check_env_file():
    """Check if .env file exists"""
    print_header("Checking Environment Configuration")
    
    if os.path.exists('.env'):
        print("✅ .env file exists")
        print("\n⚠️  Please verify your .env configuration:")
        print("   - SECRET_KEY")
        print("   - ADMIN_SECRET_KEY")
        print("   - DATABASE_URL")
        print("   - EMODAL_API_URL")
        return True
    else:
        print("❌ .env file not found")
        print("\nPlease create a .env file with the following variables:")
        print("   - SECRET_KEY")
        print("   - ADMIN_SECRET_KEY")
        print("   - DATABASE_URL")
        print("   - EMODAL_API_URL")
        return False

def initialize_database():
    """Initialize Flask-Migrate and create database tables"""
    print_header("Initializing Database")
    
    # Check if migrations folder exists
    if os.path.exists('migrations'):
        print("ℹ️  Migrations folder already exists")
        user_input = input("Reinitialize migrations? (y/n): ")
        if user_input.lower() == 'y':
            import shutil
            shutil.rmtree('migrations')
            print("🗑️  Removed existing migrations")
    
    if not os.path.exists('migrations'):
        if not run_command("flask db init", "Initializing Flask-Migrate"):
            return False
    
    if not run_command("flask db migrate -m 'Initial migration'", "Creating migration"):
        return False
    
    if not run_command("flask db upgrade", "Applying migration"):
        return False
    
    print("✅ Database initialized successfully")
    return True

def main():
    """Main setup function"""
    print_header("E-Modal Management System - Setup")
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Check environment file
    if not check_env_file():
        print("\n⚠️  Setup cannot continue without .env file")
        sys.exit(1)
    
    # Step 4: Install dependencies
    if not install_dependencies():
        print("\n⚠️  Failed to install dependencies")
        sys.exit(1)
    
    # Step 5: Check PostgreSQL
    check_postgresql()
    
    # Step 6: Initialize database
    print("\n⚠️  Database initialization requires:")
    print("   1. PostgreSQL is running")
    print("   2. Database exists (or you have permission to create it)")
    print("   3. DATABASE_URL in .env is correct")
    
    user_input = input("\nInitialize database now? (y/n): ")
    if user_input.lower() == 'y':
        if initialize_database():
            print("\n✅ Database setup complete!")
        else:
            print("\n⚠️  Database setup failed. Please check your configuration.")
    
    # Final message
    print_header("Setup Complete!")
    print("✅ System is ready to run!")
    print("\nNext steps:")
    print("1. Verify .env configuration")
    print("2. Ensure PostgreSQL database exists")
    print("3. Start the server: python app.py")
    print("4. Run tests: python test_system.py")
    print("\nFor detailed instructions, see QUICKSTART.md")

if __name__ == '__main__':
    main()

