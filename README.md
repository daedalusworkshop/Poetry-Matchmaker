# Poetry Matchmaker

A Python application that uses semantic search and AI to find and format poetry that matches your thoughts and feelings.

## 🚀 Quick Setup (Recommended)

### Automated Setup Scripts

**For macOS/Linux:**
```bash
git clone https://github.com/daedalusworkshop/Poetry-Matchmaker.git
cd Poetry-Matchmaker
./setup.sh
```

**For Windows:**
```cmd
git clone https://github.com/daedalusworkshop/Poetry-Matchmaker.git
cd Poetry-Matchmaker
setup.bat
```

The setup scripts will automatically:
- Create a virtual environment
- Install all dependencies
- Set up environment configuration
- Guide you through API key setup

## Quick Start with GitHub

### Deploy to Another Folder/Machine

1. **Clone the repository:**
   ```bash
   git clone https://github.com/daedalusworkshop/Poetry-Matchmaker.git
   cd Poetry-Matchmaker
   ```

2. **Set up Python environment:**
   ```bash
   # Create virtual environment (recommended)
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file with your actual API keys
   # You need:
   # - OpenAI API key from https://platform.openai.com/api-keys
   # - Google AI API key from https://makersuite.google.com/app/apikey
   ```

5. **Initialize the database:**
   ```bash
   # Run the population script to set up the poetry database
   python populate_db.py
   ```

6. **Run the application:**
   
   **Option A: Web Interface (Recommended)**
   ```bash
   cd web_interface
   python app.py
   ```
   Then open http://localhost:8080 in your browser

   **Option B: Command Line Interface**
   ```bash
   python main.py
   ```

   **Option C: Voice Input**
   ```bash
   python main.py --audio path/to/audio/file.wav
   ```

## Project Structure
- `main.py`: Command-line application script
- `web_interface/`: Modern web interface with real-time AI processing
- `poetry_db.py`: Database operations for poem storage and retrieval
- `poem_formatter.py`: Handles poem formatting using OpenAI
- `config.py`: Configuration settings
- `requirements.txt`: Project dependencies
- `PoetryFoundationData.csv`: Poetry dataset
- `.env.example`: Template for environment variables

## Features
- 🎯 **Semantic Search**: Uses ChromaDB for finding poems by meaning, not just keywords
- 🤖 **AI-Powered Matching**: GPT-4.1 evaluates and selects the perfect poem for your mood
- 🎨 **Beautiful Web Interface**: Modern, responsive design with dark/light themes
- 🎤 **Voice Input**: Upload audio recordings to find poems based on spoken thoughts
- 📱 **Mobile Friendly**: Works seamlessly on all devices
- ⚡ **Real-time Processing**: Watch AI analyze and score poems in real-time

## API Keys Required

1. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
   - Used for poem formatting and AI evaluation
   - Make sure you have credits in your OpenAI account

2. **Google AI API Key**: Get from https://makersuite.google.com/app/apikey
   - Used for Gemini AI features
   - Free tier available

## Troubleshooting

- **Database issues**: Delete the `chroma_poetry_db` folder and run `python populate_db.py` again
- **Missing poems**: Ensure `PoetryFoundationData.csv` is in the root directory
- **API errors**: Check that your API keys are valid and have sufficient credits
- **Port conflicts**: The web app runs on port 8080 by default

## Security Note
Never commit your `.env` file or expose your API keys. The `.env` file is already in `.gitignore`.

## Development
- Python 3.8+ required
- Uses Flask for web interface
- ChromaDB for vector storage
- OpenAI GPT-4.1 for AI evaluation 