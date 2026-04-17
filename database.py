import sqlite3
import json
import requests

DB = "cards_oracle.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id TEXT PRIMARY KEY,
        name TEXT,
        type_line TEXT,
        oracle_text TEXT,
        mana_cost TEXT,
        cmc REAL,
        rarity TEXT,
        set_code TEXT,
        set_name TEXT,
        released_at TEXT,
        colors TEXT,
        color_identity TEXT,
        image_small TEXT,
        image_normal TEXT,
        raw_json TEXT
    )
    """)
    conn.commit()

def insert_card(card):
    cur.execute("""
        INSERT OR REPLACE INTO cards (
            id, name, type_line, oracle_text,
            mana_cost, cmc, rarity,
            set_code, set_name, released_at,
            colors, color_identity,
            image_small, image_normal,
            raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        card["id"],
        card["name"],
        card.get("type_line"),
        card.get("oracle_text"),
        card.get("mana_cost"),
        card.get("cmc"),
        card.get("rarity"),
        card.get("set"),
        card.get("set_name"),
        card.get("released_at"),
        json.dumps(card.get("colors")),
        json.dumps(card.get("color_identity")),
        card.get("image_uris", {}).get("small"),
        card.get("image_uris", {}).get("normal"),
        json.dumps(card)
    ))

def fetch_cards():
    meta_url = "https://api.scryfall.com/bulk-data/oracle-cards"
    meta = requests.get(meta_url).json()

    download_url = meta["download_uri"]
    print("Downloading:", download_url)

    data = requests.get(download_url).json()
    return data

init_db()

cards = fetch_cards()

for card in cards:
    insert_card(card)

conn.commit()
conn.close()
