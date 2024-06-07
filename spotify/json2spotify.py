import json

import spotipy
import yaml
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


def get_artist_dict():
    with open("artists_setlists_cleaned.json", "r") as input:
        json_artists = json.load(input)
        return json_artists


def create_playlists(json_artists: dict):
    user_id = get_spotify_user_id()
    spotify = init_spotify()

    for artist in json_artists:
        playlist_name = f"{artist} - Most played live"
        song_uris = []
        for song in json_artists[artist]:
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
    artist_dict = get_artist_dict()
    create_playlists(artist_dict)


if __name__ == "__main__":
    main()
