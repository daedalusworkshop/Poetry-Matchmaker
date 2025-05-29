#!/bin/bash

# Poetry Matchmaker Setup Script
# This script automates the setup process for the Poetry Matchmaker

echo "🎭 Poetry Matchmaker Setup Script"
echo "================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment file
if [ ! -f .env ]; then
    echo "⚙️  Setting up environment configuration..."
    cp .env.example .env
    echo "📝 Please edit the .env file with your API keys:"
    echo "   - OpenAI API key from https://platform.openai.com/api-keys"
    echo "   - Google AI API key from https://makersuite.google.com/app/apikey"
    echo
    echo "🔧 Opening .env file for editing..."
    
    # Try to open with common editors
    if command -v code &> /dev/null; then
        code .env
    elif command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    else
        echo "Please manually edit the .env file with your API keys"
    fi
else
    echo "⚙️  Environment file already exists"
fi

echo
echo "🚀 Setup complete! Next steps:"
echo
echo "1. Make sure your API keys are set in the .env file"
echo "2. Initialize the database:"
echo "   python populate_db.py"
echo
echo "3. Run the application:"
echo "   Web interface:     cd web_interface && python app.py"
echo "   Command line:      python main.py"
echo "   Voice input:       python main.py --audio audio_file.wav"
echo
echo "🌐 Web interface will be available at: http://localhost:8080"
echo
echo "💡 Need help? Check the README.md file for detailed instructions" 