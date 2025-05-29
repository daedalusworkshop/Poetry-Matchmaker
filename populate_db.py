import pandas as pd
from poetry_db import PoetryDatabase

print('Loading CSV file...')
df = pd.read_csv('PoetryFoundationData.csv')
poems = df['Poem'].dropna().tolist()
print(f'Found {len(poems)} poems in CSV')

print('Initializing database...')
db = PoetryDatabase('chroma_poetry_db')

print('Adding poems to database (this will take a few minutes)...')
print('This process creates embeddings for each poem, so it takes time.')

db.add_poems(poems)

print(f'Successfully added {len(poems)} poems to database!')
print('Database is now ready for poetry matching!') 