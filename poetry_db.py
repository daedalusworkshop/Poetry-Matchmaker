import chromadb

class PoetryDatabase:
    def __init__(self, db_path="./chroma_poetry_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("poems")
    
    def add_poems(self, poems, batch_size=10):
        ids = [f"poem{i}" for i in range(len(poems))]
        
        for start in range(0, len(poems), batch_size):
            end = start + batch_size
            batch_poems = poems[start:end]
            batch_ids = ids[start:end]
            self.collection.add(documents=batch_poems, ids=batch_ids)
            print(f"Added poems {start} to {end-1}")
    
    def get_count(self):
        return self.collection.count()
    
    def query_poems(self, query_text, n_results=4):
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

    def get_embedding_by_title(self, title, df):
        # Find the index of the poem with the given title
        idx = df[df['Title'].str.strip() == title.strip()].index
        if len(idx) == 0:
            raise ValueError(f"Poem with title '{title}' not found.")
        poem_id = f"poem{idx[0]}"
        # Query ChromaDB for the embedding
        result = self.collection.get(ids=[poem_id], include=["embeddings"])
        return result["embeddings"][0]

    def get_all_embeddings_and_ids(self):
        # Get all embeddings and their IDs from the collection
        # ChromaDB collections support .get with no ids to get all
        result = self.collection.get(include=["embeddings"])
        return result["ids"], result["embeddings"] 