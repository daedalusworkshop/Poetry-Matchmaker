import os
# Set environment variable to avoid tokenizer warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pandas as pd
from poetry_db import PoetryDatabase
from poem_formatter import PoemFormatter
from config import OPENAI_API_KEY, DB_PATH, POETRY_DATA_FILE
from evaluation import PoetryEvaluator
import sys
import openai
import argparse
import tempfile
import subprocess

def transcribe_audio(audio_path):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    try:
        # Check if the file is webm and convert to wav if needed
        if audio_path.endswith('.webm'):
            # Create a temporary wav file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                temp_wav_path = temp_wav.name
            
            try:
                # Try ffmpeg first
                try:
                    subprocess.run([
                        'ffmpeg', '-i', audio_path, 
                        '-acodec', 'pcm_s16le', 
                        '-ar', '16000', 
                        '-ac', '1',  # mono
                        '-y',  # overwrite output file
                        temp_wav_path
                    ], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback to pydub if ffmpeg fails
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(audio_path, format="webm")
                    audio = audio.set_frame_rate(16000).set_channels(1)
                    audio.export(temp_wav_path, format="wav")
                
                # Use the converted wav file for transcription
                with open(temp_wav_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return transcript.text
            finally:
                # Clean up the temporary wav file
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
        else:
            # For other formats, use directly
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        raise e

def llm_best_match_process(query=None):
    # Load the Poetry Foundation CSV
    df = pd.read_csv(POETRY_DATA_FILE)
    db = PoetryDatabase(DB_PATH)
    formatter = PoemFormatter(OPENAI_API_KEY)
    evaluator = PoetryEvaluator()

    if query is None:
        print("\nEnter your thoughts, feelings, or theme to find the single best-matching poem (LLM-evaluated).\n(Write a few sentences about what's on your mind or what kind of poetry you're looking for)")
        query = input("> ")

    n_results = 22
    if not query:
        return "No input provided"
        
    print(f"\nSearching for the top {n_results} matching poems...\n")
    results = db.query_poems(query, n_results=n_results)
    poem_indices = [int(pid[4:]) for pid in results["ids"][0]]
    poems = []
    for idx in poem_indices:
        row = df.iloc[idx]
        poems.append({
            'title': row['Title'].strip(),
            'author': row['Poet'].strip(),
            'text': row['Poem']
        })

    # Get the model name based on which one we're using
    model_name = "gpt-4.1"  # Now using GPT-4.1 exclusively
    print(f"\nScoring poems for relevance using LLM (model: {model_name})...\n")
    
    # Score poems individually with real-time progress (original working method)
    llm_scores = []
    last_line_len = 0
    for i, poem in enumerate(poems):
        # Score this poem
        score_result = evaluator.llm_evaluate(query, [poem])[0]
        llm_scores.append(score_result)
        # Prepare progress string
        progress_str = f"Scoring poem {i+1}/{n_results}: '{poem['title']}' -> {score_result['score']}   "
        pad = max(0, last_line_len - len(progress_str))
        # Move cursor up and clear line (ANSI escape)
        sys.stdout.write("\033[F\033[K" if i > 0 else "")
        sys.stdout.write(f"{progress_str}{' ' * pad}\n")
        sys.stdout.flush()
        last_line_len = len(progress_str)
    print()  # Newline after all are done

    # Find the highest scoring poem
    best_idx = max(range(len(llm_scores)), key=lambda i: llm_scores[i]['score'])
    best_poem = poems[best_idx]
    best_score = llm_scores[best_idx]['score']
    best_explanation = llm_scores[best_idx]['explanation']

    result = f"\nBest match (LLM score: {best_score}/10): {best_explanation}\n"
    result += f"Selected poem # {best_idx+1} out of {n_results} (1 = most embedding-similar)\n"
    result += f"LLM model used for scoring: {model_name}\n\n"
    
    # Prepare for formatter
    poem_data = {
        'Title': best_poem['title'],
        'Poet': best_poem['author'],
        'Poem': best_poem['text']
    }
    formatted_poem = formatter.format_poem(poem_data, return_string=True)
    result += formatted_poem
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio', type=str, help='Path to audio file to transcribe')
    args = parser.parse_args()

    if args.audio:
        # Handle audio input
        query = transcribe_audio(args.audio)
        print(f"Transcription: {query}\n")  # Print the transcription before poem search
        result = llm_best_match_process(query)
        print(result)
    else:
        # Handle text input
        result = llm_best_match_process()
        print(result)

if __name__ == "__main__":
    main() 