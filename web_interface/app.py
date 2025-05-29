import os
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
import tempfile
import json
import re
import time
import threading
import queue

# Add parent directory to path to import main.py modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import transcribe_audio
# We'll import the streaming version functions separately
import pandas as pd
from poetry_db import PoetryDatabase
from poem_formatter import PoemFormatter
from config import OPENAI_API_KEY, DB_PATH, POETRY_DATA_FILE
from evaluation import PoetryEvaluator

app = Flask(__name__, template_folder='frontend', static_folder='frontend')
CORS(app)

def llm_best_match_process_streaming(query, progress_callback=None):
    """Modified version that sends progress updates via callback"""
    # Load the Poetry Foundation CSV
    df = pd.read_csv(POETRY_DATA_FILE)
    db = PoetryDatabase(DB_PATH)
    formatter = PoemFormatter(OPENAI_API_KEY)
    evaluator = PoetryEvaluator()

    n_results = 22
    if not query:
        return "No input provided"
    
    if progress_callback:
        progress_callback("status", "Searching for the top matching poems...")
        
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
    model_name = "gpt-4.1"
    
    if progress_callback:
        progress_callback("status", f"Scoring poems for relevance using {model_name}...")
    
    # Score poems individually with real-time progress
    llm_scores = []
    for i, poem in enumerate(poems):
        if progress_callback:
            progress_callback("scoring", f"Scoring poem {i+1}/{n_results}: '{poem['title']}' by {poem['author']}")
        
        # Score this poem
        score_result = evaluator.llm_evaluate(query, [poem])[0]
        llm_scores.append(score_result)
        
        if progress_callback:
            progress_callback("score", f"'{poem['title']}' -> {score_result['score']}")

    if progress_callback:
        progress_callback("status", "Selecting the perfect poem...")

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
    
    if progress_callback:
        progress_callback("status", "Formatting your poem...")
    
    formatted_poem = formatter.format_poem(poem_data, return_string=True)
    result += formatted_poem
    return result

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/result')
def result():
    return send_from_directory('frontend', 'result.html')

@app.route('/api/process_text_stream')
def process_text_stream():
    """Server-Sent Events endpoint for streaming progress"""
    query = request.args.get('query', '')
    
    if not query.strip():
        return jsonify({'error': 'No query provided'}), 400
    
    def generate():
        progress_queue = queue.Queue()
        result_data = {}
        
        def progress_callback(msg_type, message):
            progress_queue.put((msg_type, message))
        
        def process_in_background():
            try:
                result = llm_best_match_process_streaming(query, progress_callback)
                
                # Parse the result to extract components
                lines = result.split('\n')
                best_match_line = next((line for line in lines if line.startswith('Best match')), '')
                selected_poem_line = next((line for line in lines if line.startswith('Selected poem')), '')
                llm_model_line = next((line for line in lines if line.startswith('LLM model')), '')
                
                # Find the poem header line (format: "---  Title by Author ---")
                poem_header_idx = -1
                title = 'Unknown Title'
                author = 'Unknown Author'
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('---') and ' by ' in line and line.strip().endswith('---'):
                        poem_header_idx = i
                        # Extract title and author from header
                        header_content = line.strip()[3:-3].strip()  # Remove "---" from both ends
                        if ' by ' in header_content:
                            title_part, author_part = header_content.split(' by ', 1)
                            title = title_part.strip()
                            author = author_part.strip()
                        break
                
                # Extract poem text (starts after the header line)
                poem_text = ''
                if poem_header_idx != -1:
                    poem_lines = []
                    for i in range(poem_header_idx + 1, len(lines)):
                        line = lines[i]
                        # Skip the emoji line if present
                        if line.strip().startswith('✨'):
                            continue
                        # Add non-empty lines to poem
                        if line.strip():
                            poem_lines.append(line.rstrip())
                        elif poem_lines:  # Keep empty lines within the poem
                            poem_lines.append('')
                    poem_text = '\n'.join(poem_lines).strip()
                
                # Extract qualia explanation and remove score if present
                qualia_explanation = ''
                if best_match_line:
                    # Remove 'Best match (LLM score: ...): ' prefix
                    if ': ' in best_match_line:
                        qualia_explanation = best_match_line.split(': ', 1)[1].strip()
                        # Remove leading score if present (e.g., '8.6/10): ...')
                        qualia_explanation = re.sub(r'^\d+(\.\d+)?/10\):\s*', '', qualia_explanation)
                    else:
                        qualia_explanation = best_match_line.strip()
                
                result_data['success'] = True
                result_data['title'] = title
                result_data['author'] = author
                result_data['poem_text'] = poem_text
                result_data['metadata'] = {
                    'qualia': qualia_explanation,
                    'selected_poem': selected_poem_line,
                    'llm_model': llm_model_line
                }
                result_data['raw_result'] = result
                
                progress_queue.put(('complete', json.dumps(result_data)))
                
            except Exception as e:
                progress_queue.put(('error', str(e)))
        
        # Start background processing
        thread = threading.Thread(target=process_in_background)
        thread.start()
        
        # Stream progress updates
        while True:
            try:
                msg_type, message = progress_queue.get(timeout=1)
                yield f"data: {json.dumps({'type': msg_type, 'message': message})}\n\n"
                
                if msg_type in ['complete', 'error']:
                    break
                    
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/process_audio_stream')
def process_audio_stream():
    """Server-Sent Events endpoint for streaming audio processing progress"""
    # For audio, we need to handle file upload differently
    # This endpoint will be called after audio is uploaded
    query = request.args.get('query', '')
    
    if not query.strip():
        return jsonify({'error': 'No transcribed query provided'}), 400
    
    def generate():
        progress_queue = queue.Queue()
        result_data = {}
        
        def progress_callback(msg_type, message):
            progress_queue.put((msg_type, message))
        
        def process_in_background():
            try:
                result = llm_best_match_process_streaming(query, progress_callback)
                
                # Parse the result (same logic as text processing)
                lines = result.split('\n')
                best_match_line = next((line for line in lines if line.startswith('Best match')), '')
                selected_poem_line = next((line for line in lines if line.startswith('Selected poem')), '')
                llm_model_line = next((line for line in lines if line.startswith('LLM model')), '')
                
                poem_header_idx = -1
                title = 'Unknown Title'
                author = 'Unknown Author'
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('---') and ' by ' in line and line.strip().endswith('---'):
                        poem_header_idx = i
                        header_content = line.strip()[3:-3].strip()
                        if ' by ' in header_content:
                            title_part, author_part = header_content.split(' by ', 1)
                            title = title_part.strip()
                            author = author_part.strip()
                        break
                
                poem_text = ''
                if poem_header_idx != -1:
                    poem_lines = []
                    for i in range(poem_header_idx + 1, len(lines)):
                        line = lines[i]
                        if line.strip().startswith('✨'):
                            continue
                        if line.strip():
                            poem_lines.append(line.rstrip())
                        elif poem_lines:
                            poem_lines.append('')
                    poem_text = '\n'.join(poem_lines).strip()
                
                qualia_explanation = ''
                if best_match_line:
                    if ': ' in best_match_line:
                        qualia_explanation = best_match_line.split(': ', 1)[1].strip()
                        qualia_explanation = re.sub(r'^\d+(\.\d+)?/10\):\s*', '', qualia_explanation)
                    else:
                        qualia_explanation = best_match_line.strip()
                
                result_data['success'] = True
                result_data['title'] = title
                result_data['author'] = author
                result_data['poem_text'] = poem_text
                result_data['metadata'] = {
                    'qualia': qualia_explanation,
                    'selected_poem': selected_poem_line,
                    'llm_model': llm_model_line
                }
                result_data['raw_result'] = result
                
                progress_queue.put(('complete', json.dumps(result_data)))
                
            except Exception as e:
                progress_queue.put(('error', str(e)))
        
        thread = threading.Thread(target=process_in_background)
        thread.start()
        
        while True:
            try:
                msg_type, message = progress_queue.get(timeout=1)
                yield f"data: {json.dumps({'type': msg_type, 'message': message})}\n\n"
                
                if msg_type in ['complete', 'error']:
                    break
                    
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/transcribe_audio', methods=['POST'])
def transcribe_audio_endpoint():
    """Separate endpoint for audio transcription"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save the audio file temporarily with .webm extension
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Transcribe the audio
            query = transcribe_audio(temp_path)
            
            if not query or not query.strip():
                return jsonify({'error': 'No speech detected in audio'}), 400
            
            # Print the transcription to the terminal console
            print(f"Transcription: {query}\n")
            
            return jsonify({
                'success': True,
                'transcription': query
            })
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Keep the original endpoints for backward compatibility
@app.route('/api/process_text', methods=['POST'])
def process_text():
    """Fallback to original endpoint for compatibility"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query.strip():
            return jsonify({'error': 'No query provided'}), 400
        
        # Import the original function
        from main import llm_best_match_process
        result = llm_best_match_process(query)
        
        # Parse the result to extract components (same as before)
        lines = result.split('\n')
        best_match_line = next((line for line in lines if line.startswith('Best match')), '')
        selected_poem_line = next((line for line in lines if line.startswith('Selected poem')), '')
        llm_model_line = next((line for line in lines if line.startswith('LLM model')), '')
        
        poem_header_idx = -1
        title = 'Unknown Title'
        author = 'Unknown Author'
        
        for i, line in enumerate(lines):
            if line.strip().startswith('---') and ' by ' in line and line.strip().endswith('---'):
                poem_header_idx = i
                header_content = line.strip()[3:-3].strip()
                if ' by ' in header_content:
                    title_part, author_part = header_content.split(' by ', 1)
                    title = title_part.strip()
                    author = author_part.strip()
                break
        
        poem_text = ''
        if poem_header_idx != -1:
            poem_lines = []
            for i in range(poem_header_idx + 1, len(lines)):
                line = lines[i]
                if line.strip().startswith('✨'):
                    continue
                if line.strip():
                    poem_lines.append(line.rstrip())
                elif poem_lines:
                    poem_lines.append('')
            poem_text = '\n'.join(poem_lines).strip()
        
        qualia_explanation = ''
        if best_match_line:
            if ': ' in best_match_line:
                qualia_explanation = best_match_line.split(': ', 1)[1].strip()
                qualia_explanation = re.sub(r'^\d+(\.\d+)?/10\):\s*', '', qualia_explanation)
            else:
                qualia_explanation = best_match_line.strip()
        
        return jsonify({
            'success': True,
            'title': title,
            'author': author,
            'poem_text': poem_text,
            'metadata': {
                'qualia': qualia_explanation,
                'selected_poem': selected_poem_line,
                'llm_model': llm_model_line
            },
            'raw_result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_audio', methods=['POST'])
def process_audio():
    """Fallback to original audio endpoint for compatibility"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            query = transcribe_audio(temp_path)
            
            if not query or not query.strip():
                return jsonify({'error': 'No speech detected in audio'}), 400
            
            print(f"Transcription: {query}\n")
            
            from main import llm_best_match_process
            result = llm_best_match_process(query)
            
            # Parse the result (same logic as text processing)
            lines = result.split('\n')
            best_match_line = next((line for line in lines if line.startswith('Best match')), '')
            selected_poem_line = next((line for line in lines if line.startswith('Selected poem')), '')
            llm_model_line = next((line for line in lines if line.startswith('LLM model')), '')
            
            poem_header_idx = -1
            title = 'Unknown Title'
            author = 'Unknown Author'
            
            for i, line in enumerate(lines):
                if line.strip().startswith('---') and ' by ' in line and line.strip().endswith('---'):
                    poem_header_idx = i
                    header_content = line.strip()[3:-3].strip()
                    if ' by ' in header_content:
                        title_part, author_part = header_content.split(' by ', 1)
                        title = title_part.strip()
                        author = author_part.strip()
                    break
            
            poem_text = ''
            if poem_header_idx != -1:
                poem_lines = []
                for i in range(poem_header_idx + 1, len(lines)):
                    line = lines[i]
                    if line.strip().startswith('✨'):
                        continue
                    if line.strip():
                        poem_lines.append(line.rstrip())
                    elif poem_lines:
                        poem_lines.append('')
                poem_text = '\n'.join(poem_lines).strip()
            
            qualia_explanation = ''
            if best_match_line:
                if ': ' in best_match_line:
                    qualia_explanation = best_match_line.split(': ', 1)[1].strip()
                    qualia_explanation = re.sub(r'^\d+(\.\d+)?/10\):\s*', '', qualia_explanation)
                else:
                    qualia_explanation = best_match_line.strip()
            
            return jsonify({
                'success': True,
                'transcription': query,
                'title': title,
                'author': author,
                'poem_text': poem_text,
                'metadata': {
                    'qualia': qualia_explanation,
                    'selected_poem': selected_poem_line,
                    'llm_model': llm_model_line
                },
                'raw_result': result
            })
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080) 