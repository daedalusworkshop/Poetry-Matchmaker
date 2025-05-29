import pandas as pd
from poetry_db import PoetryDatabase

print('Loading CSV file...')
df = pd.read_csv('PoetryFoundationData.csv')
poems = df['Poem'].dropna().tolist()
print(f'Found {len(poems)} poems in CSV')

# Take just the first 10 poems for testing
test_poems = poems[:10]
print(f'Using first {len(test_poems)} poems for testing')

print('Initializing database...')
db = PoetryDatabase('chroma_poetry_db')

print('Adding test poems to database (should be quick)...')
db.add_poems(test_poems)

print(f'Successfully added {len(test_poems)} poems to database!')
print('Test database is ready - try your web interface now!') 