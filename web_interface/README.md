# Poetry Matchmaker Web Interface

A beautiful web interface for the Poetry Matchmaker that combines the elegant design from `temp_interface` with the full functionality of `main.py`.

## Features

- **Dual Input Modes**: Switch between microphone and keyboard input
- **Beautiful UI**: Elegant design with mouse attraction effects and smooth animations
- **Voice Recognition**: Record your thoughts and have them transcribed using OpenAI Whisper
- **AI-Powered Matching**: Uses embeddings and LLM evaluation to find the perfect poem
- **Responsive Design**: Works on desktop and mobile devices

## Setup

1. **Install Dependencies**:
   ```bash
   cd web_interface
   pip install flask flask-cors
   ```
   
   Or install all project dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Ensure Configuration**:
   Make sure your `config.py` file in the parent directory has your OpenAI API key set up.

3. **Database Setup**:
   Ensure your poetry database is set up by running the main script at least once:
   ```bash
   cd ..
   python main.py
   ```

## Running the Application

### Option 1: Using the run script
```bash
python run.py
```

### Option 2: Direct Flask run
```bash
python app.py
```

Then open your browser to: http://localhost:5000

## Usage

1. **Choose Input Mode**: Use the mode switcher in the top-right to choose between microphone and keyboard input

2. **Microphone Mode**:
   - Click "Speak your truth" to start recording
   - Speak your thoughts, feelings, or what kind of poetry you're looking for
   - Click the recording button again to stop and process

3. **Keyboard Mode**:
   - Click "Type your truth" to expand the text area
   - Type your thoughts and feelings
   - Click "Submit" to process

4. **View Results**: The app will find and display your perfect poem match with metadata about why it was selected

## Technical Details

- **Backend**: Flask with Python integration to `main.py`
- **Frontend**: Vanilla JavaScript with GSAP for animations
- **Audio Processing**: Web Audio API for recording, OpenAI Whisper for transcription
- **AI Processing**: ChromaDB for embeddings, GPT-4 for evaluation
- **Design**: Responsive CSS with Georgia serif font and dark theme

## API Endpoints

- `GET /` - Main interface
- `GET /result` - Results page
- `POST /api/process_text` - Process text input
- `POST /api/process_audio` - Process audio input

## Files

- `app.py` - Flask backend server
- `run.py` - Startup script
- `frontend/index.html` - Main interface page
- `frontend/result.html` - Results display page 