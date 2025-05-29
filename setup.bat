@echo off
echo 🎭 Poetry Matchmaker Setup Script (Windows)
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Set up environment file
if not exist .env (
    echo ⚙️  Setting up environment configuration...
    copy .env.example .env
    echo 📝 Please edit the .env file with your API keys:
    echo    - OpenAI API key from https://platform.openai.com/api-keys
    echo    - Google AI API key from https://makersuite.google.com/app/apikey
    echo.
    echo 🔧 Opening .env file for editing...
    notepad .env
) else (
    echo ⚙️  Environment file already exists
)

echo.
echo 🚀 Setup complete! Next steps:
echo.
echo 1. Make sure your API keys are set in the .env file
echo 2. Initialize the database:
echo    python populate_db.py
echo.
echo 3. Run the application:
echo    Web interface:     cd web_interface ^&^& python app.py
echo    Command line:      python main.py
echo    Voice input:       python main.py --audio audio_file.wav
echo.
echo 🌐 Web interface will be available at: http://localhost:8080
echo.
echo 💡 Need help? Check the README.md file for detailed instructions
pause 