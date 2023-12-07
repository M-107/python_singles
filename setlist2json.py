import json

import requests
from bs4 import BeautifulSoup

artists_to_find = [
    "Bring Me The horizon",
    "The Offspring",
    "Avril Lavigne",
    "Corey Taylor",
    "Pendulum",
    "Parkway Drive",
    "Against The Current",
    "Alpha Wolf",
    "Aneta Langerová",
    "Bitter Season",
    "Body Count",
    "Crystal Lake",
    "Dead Pony",
    "La Dispute",
    "Dmitrievna",
    "Dogstar",
    "The Ecstasy Of Saint Theresa",
    "Enter Shikari",
    "Hanabie",
    "Hoobstank",
    "Hot Milk",
    "J.A.R.",
    "John Wolfhooker",
    "Kaizers Orchestra",
    "Missio",
    "Neck Deep",
    "Shadow Of Intent",
    "Sum 41",
    "58G",
]


artists = {}
for artist in artists_to_find:
    print(f"Searching for {artist}...", end="   ")
    search_query = artist.lower().replace(" ", "+")
    page_url = f"https://www.setlist.fm/search?query={search_query}"
    page_response = requests.get(page_url)
    page_soup = BeautifulSoup(page_response.content, "html.parser")
    results = page_soup.find_all("div", {"class": "col-xs-12 setlistPreview"})
    print(f"Found {len(results)} setlists.")
    songs = {}
    for result in results:
        anchor = result.find("a")
        href = anchor["href"]
        setlist_url = f"https://www.setlist.fm/{href}"
        setlist_response = requests.get(setlist_url)
        setlist_soup = BeautifulSoup(setlist_response.content, "html.parser")
        song_list = setlist_soup.find_all("li", {"class": "setlistParts song"})
        for song in song_list:
            song_name = song.find("a", {"class": "songLabel"})
            if song_name:
                song_name_string = song_name.get_text()
                if song_name_string in songs:
                    songs[song_name_string] += 1
                else:
                    songs[song_name_string] = 1
    artists[artist] = songs

with open("artists_setlists.json", "w") as output:
    json.dump(artists, output)
