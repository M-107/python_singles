import requests
import spotipy
import yaml
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_user_id():
    with open("./.credentials.yaml", "r") as f:
        credentials = yaml.safe_load(f)
        user_id = credentials["spotify"]["user_id"]
    return user_id


def init_spotify():
    with open(".credentials.yaml", "r") as f:
        credentials = yaml.safe_load(f)
    spotify = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-public",
            client_id=credentials["spotify"]["client_id"],
            client_secret=credentials["spotify"]["client_secret"],
            redirect_uri="http://localhost",
            username=credentials["spotify"]["user_id"],
        )
    )
    return spotify


def get_artist_songs(artist: str):
    print(f"Searching for {artist}...")
    search_query = artist.lower().replace(" ", "+")
    page_url = f"https://www.setlist.fm/search?query={search_query}"
    page_response = requests.get(page_url)
    page_soup = BeautifulSoup(page_response.content, "html.parser")
    results = page_soup.find_all("div", {"class": "col-xs-12 setlistPreview"})
    print(f"    Found {len(results)} setlists")
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
    print(f"    Found {len(songs)} songs played live by this artist")
    return songs


def get_sorted_song_list(songs: dict):
    sorted_songs = dict(sorted(songs.items(), key=lambda x: x[1], reverse=True))
    return list(sorted_songs.keys())


def create_playlist(artist: str, songs: list):
    user_id = get_spotify_user_id()
    spotify = init_spotify()

    playlist_name = f"{artist} - Most played live"
    song_uris = []
    for song in songs:
        search_query = f"{artist} {song}"
        search_result = spotify.search(
            q=search_query,
            type="track",
            market="CZ",
        )
        search_result_items = search_result["tracks"]["items"]
        song_uri = search_result_items[0]["uri"]
        song_uris.append(song_uri)

    playlist = spotify.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=True,
    )
    playlist_id = playlist["uri"]

    spotify.user_playlist_add_tracks(
        user=user_id, playlist_id=playlist_id, tracks=song_uris
    )
    print(f"Created playlist {playlist_name} with {len(song_uris)} songs")


def main():
    artist_name = input("Artist Name: ")
    songs = get_artist_songs(artist=artist_name)
    if len(songs) > 0:
        songs_sorted = get_sorted_song_list(songs=songs)
        create_playlist(artist=artist_name, songs=songs_sorted)
    else:
        print(f"No songs found for {artist_name}")
        print(
            "    There are either no published setlists or a typo in the artist name."
        )


if __name__ == "__main__":
    main()
