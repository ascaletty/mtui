import sqlite3

conn = sqlite3.connect("cards.db")
cur = conn.cursor()

cur.execute("SELECT id, name FROM cards")
rows = cur.fetchall()

# separate for convenience
ids = [r[0] for r in rows]
names = [r[1] for r in rows]
from rapidfuzz import process

def search(query, limit=5):
    results = process.extract(query, names, limit=limit)
    
    # map back to IDs
    output = []
    for match_name, score, index in results:
        output.append({
            "id": ids[index],
            "name": match_name,
            "score": score
        })
    
    return output

search_i= input("your search")
print(search(search_i))
