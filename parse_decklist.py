import json
import time
import requests

import os

url = "https://api.scryfall.com/cards/collection"


def parse_decklist(deck):
    deck_dir=deck.split(".")[0]

    os.makedirs(deck_dir, exist_ok=True)

    f=open(deck, 'r')
    datavec = []

    for line in f:
        if line== '\n':
            continue 
        split= line.split(' ', 1)
        if int(split[0]) ==1:
            data= {
                'name': split[1].rstrip('\n') 
                }
            datavec.append(data)
        else:
            number= int(split[0])
            for i in range(number):
                data= {
                    'name': split[1].rstrip('\n') 
                }
                datavec.append(data)
    print(datavec)
    return datavec

def parse_response(datavec):
    list_c= [datavec[i:i+75] for i in range(0, len(datavec), 75)]
    print(f"len of datavec{len(datavec)}")
    jsonvec=[]
    for list in list_c:
        payload = {
            "identifiers":
                list
        }
        response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        jsonvec.append(data)
        for card in data["data"]:
            name = card["name"]
    # some cards (like double-faced) don't have image_uris at top level
            if "image_uris" in card:
                img_url = card["image_uris"]["normal"]
            else:
        # fallback for double-faced cards
                img_url = card["card_faces"][0]["image_uris"]["small"]

            filename = name.replace(" ", "_").replace(",", "").replace("/", "_") + ".png"
            filepath = os.path.join(deck_dir, filename)

            img_data = requests.get(img_url).content

            with open(filepath, "wb") as f:
                f.write(img_data)

            print(f"saved {filename}")    
    elif response.status_code == 429:
        time.sleep(31)
        print("rate limited")
    else:
        print("error:", response.status_code, response.text)

    time.sleep(.51)
    result = {k: v for d in jsonvec for k, v in d.items()} 
