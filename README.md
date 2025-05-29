# Poetry Matchmaker

A Python application that uses semantic search and AI to find and format poetry that matches your thoughts and feelings.

## Project Structure
- `main.py`: Main application script
- `poetry_db.py`: Database operations for poem storage and retrieval
- `poem_formatter.py`: Handles poem formatting using OpenAI
- `config.py`: Configuration settings
- `requirements.txt`: Project dependencies

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the following files:
- `PoetryFoundationData.csv`: Your poetry dataset
- Valid OpenAI API key in `config.py`

## Usage
1. Run the main script:
```bash
python main.py
```

2. To add poems to the database, uncomment the `db.add_poems(poems)` line in `main.py`

## Features
- Semantic search for poems using ChromaDB
- AI-powered poem formatting
- Clean separation of concerns with modular design 