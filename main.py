import os
# Set environment variable to avoid tokenizer warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pandas as pd
from poetry_db import PoetryDatabase
from poem_formatter import PoemFormatter
from config import OPENAI_API_KEY, DB_PATH, POETRY_DATA_FILE

def main():
    # Load the Poetry Foundation CSV
    df = pd.read_csv(POETRY_DATA_FILE)
    poems = df["Poem"].dropna().tolist()

    # Initialize components
    db = PoetryDatabase(DB_PATH)
    formatter = PoemFormatter(OPENAI_API_KEY)

    # Check sizes
    csv_size = len(poems)
    db_size = db.get_count()
    # print(f"Number of poems in CSV: {csv_size}")
    # print(f"Number of poems in database: {db_size}")
    
    # Only add poems if database is empty
    if db_size == 0:
        print("Database is empty, adding poems...")
        db.add_poems(poems)

    # Get query from user
    print("\nEnter your thoughts, feelings, or theme to find matching poems.")
    print("(Write a few sentences about what's on your mind or what kind of poetry you're looking for)")
    query = input("> ")

    # Get number of results
    print("\nHow many poems would you like to see? (default: 3)")
    try:
        n_results = int(input("> "))
    except:
        n_results = 3

    print("\nSearching for matching poems...\n")
    results = db.query_poems(query, n_results=n_results)

    # Format and display results
    for poem_id in results["ids"][0]:
        formatter.format_poem(df.iloc[int(poem_id[4:])])

if __name__ == "__main__":
    main() 