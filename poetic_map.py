import os
import pandas as pd
import numpy as np
from poetry_db import PoetryDatabase
from config import DB_PATH, POETRY_DATA_FILE, OPENAI_API_KEY
from sklearn.metrics.pairwise import cosine_similarity
import umap
import plotly.express as px
from poem_formatter import PoemFormatter

# Helper: find poem index by body (exact or partial match)
def find_poem_index_by_body(df, snippet):
    # Try exact match first
    matches = df[df['Poem'].str.strip() == snippet.strip()]
    if len(matches) == 1:
        return matches.index[0]
    # Try partial match (case-insensitive)
    matches = df[df['Poem'].str.contains(snippet.strip(), case=False, na=False)]
    if len(matches) == 1:
        return matches.index[0]
    elif len(matches) > 1:
        print(f"Found multiple matches for snippet. Please select:")
        for i, (idx, row) in enumerate(matches.iterrows()):
            print(f"[{i}] {row['Title']} by {row['Poet']}\n{row['Poem'][:100]}...\n")
        sel = int(input("Enter the number of the correct poem: "))
        return matches.index[sel]
    else:
        raise ValueError("No poem found with that body or snippet.")

# Helper: Generate embedding for arbitrary text using the same model as ChromaDB
def generate_embedding(db, text):
    # Access the underlying embedding function from ChromaDB
    embedding_function = db.collection._embedding_function
    # Generate embedding for the text
    embeddings = embedding_function([text])
    return embeddings[0]

def read_poems_from_directory(poems_dir="poems"):
    """Read all poems from the poems directory."""
    poems = []
    if not os.path.exists(poems_dir):
        os.makedirs(poems_dir)
        print(f"Created {poems_dir} directory. Add your poems there!")
        return []
    
    for filename in os.listdir(poems_dir):
        if filename.endswith('.txt'):
            with open(os.path.join(poems_dir, filename), 'r') as f:
                poem_text = f.read().strip()
                if poem_text:  # Only add non-empty poems
                    poems.append({
                        'filename': filename,
                        'text': poem_text
                    })
    
    if not poems:
        print(f"No poems found in {poems_dir}. Add .txt files containing your poems!")
    else:
        print(f"Found {len(poems)} poems in {poems_dir}")
    
    return poems

def get_poem_metadata(row):
    """Extract and format metadata from a poem row."""
    return {
        'Title': row['Title'],
        'Poet': row['Poet'],
        'Poem': row['Poem'],
        'Year': row.get('Year', 'Unknown'),
        'Region': row.get('Region', 'Unknown'),
        'Theme': row.get('Theme', 'Unknown'),
        'Form': row.get('Form', 'Unknown'),
        'Lines': len(row['Poem'].split('\n')),
        'Words': len(row['Poem'].split()),
        'Characters': len(row['Poem']),
        'Similarity Score': f"{row['kasra_score']:.4f}"
    }

def main():
    # Load data and DB
    print("Loading poetry database...")
    df = pd.read_csv(POETRY_DATA_FILE)
    db = PoetryDatabase(DB_PATH)
    
    # Initialize poem formatter with API key from config
    formatter = PoemFormatter(OPENAI_API_KEY)

    # Read poems from directory
    input_poems = read_poems_from_directory()
    if not input_poems:
        print("No poems found in the poems directory. Add some .txt files and try again!")
        return

    print("\nProcessing your poems:")
    fav_embs = []
    for poem in input_poems:
        print(f"\nProcessing: {poem['filename']}")
        try:
            idx = find_poem_index_by_body(df, poem['text'])
            poem_id = f"poem{idx}"
            result = db.collection.get(ids=[poem_id], include=["embeddings"])
            fav_embs.append(result["embeddings"][0])
            print(f"✓ Found matching poem in database!")
        except Exception as e:
            print(f"→ Generating new embedding...")
            try:
                embedding = generate_embedding(db, poem['text'])
                fav_embs.append(embedding)
                print(f"✓ Successfully generated embedding")
            except Exception as e2:
                print(f"✗ Could not generate embedding: {e2}")
    
    if not fav_embs:
        print("\nNo valid poems found. Check the contents of your poem files.")
        return

    print("\nAnalyzing poetic style...")
    # Compute style vector and similarities
    style_vec = np.mean(np.array(fav_embs, dtype=np.float32), axis=0)
    all_ids, all_embs = db.get_all_embeddings_and_ids()
    all_embs = np.array(all_embs, dtype=np.float32)
    similarity_scores = cosine_similarity([style_vec], all_embs)[0]
    
    # Add scores to DataFrame
    df['kasra_score'] = 0.0
    for pid, score in zip(all_ids, similarity_scores):
        idx = int(pid[4:])
        df.at[idx, 'kasra_score'] = score

    # Get top matches first
    print("\nFinding most similar poems...")
    top_matches = df.nlargest(10, 'kasra_score')
    
    # Format only the top matches
    print("\nFormatting top matches...")
    formatted_poems = []
    for i, row in top_matches.iterrows():
        metadata = get_poem_metadata(row)
        formatted_text = formatter.format_poem(metadata, idx=i+1)
        formatted_poems.append({
            'metadata': metadata,
            'formatted_text': formatted_text
        })

    # UMAP visualization
    print("\nGenerating visualization...")
    reducer = umap.UMAP(
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42
    )
    umap_coords = reducer.fit_transform(all_embs)
    df['umap_x'] = umap_coords[:,0]
    df['umap_y'] = umap_coords[:,1]

    # Create hover text only for points that need it
    df['hover_text'] = df.apply(lambda row: f"Title: {row['Title']}\nPoet: {row['Poet']}\nSimilarity: {row['kasra_score']:.3f}", axis=1)

    # Enhanced Plotly visualization
    fig = px.scatter(
        df, 
        x='umap_x', 
        y='umap_y',
        color='kasra_score',
        hover_data={
            'Title': True,
            'Poet': True,
            'kasra_score': ':.3f',
            'umap_x': False,
            'umap_y': False,
            'hover_text': True
        },
        color_continuous_scale='Viridis',
        title='Poetic Map: Similarity to Your Style',
        labels={
            'umap_x': 'Poetic Space X',
            'umap_y': 'Poetic Space Y',
            'kasra_score': 'Similarity Score'
        }
    )
    
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="monospace"
        ),
        plot_bgcolor='white'
    )
    
    # Show visualization
    fig.show()

    # Print detailed analysis of top matches
    print("\n=== Top 10 Most Similar Poems ===")
    print("\nDetailed Analysis:")
    for poem in formatted_poems:
        metadata = poem['metadata']
        print("\n" + "="*50)
        print(f"Title: {metadata['Title']}")
        print(f"Poet: {metadata['Poet']}")
        print(f"Similarity Score: {metadata['Similarity Score']}")
        print(f"Year: {metadata['Year']}")
        print(f"Region: {metadata['Region']}")
        print(f"Theme: {metadata['Theme']}")
        print(f"Form: {metadata['Form']}")
        print(f"Statistics:")
        print(f"  - Lines: {metadata['Lines']}")
        print(f"  - Words: {metadata['Words']}")
        print(f"  - Characters: {metadata['Characters']}")
        print("\nPoem:")
        print(poem['formatted_text'])

if __name__ == "__main__":
    main() 