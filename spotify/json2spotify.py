import json
from os import environ

import spotipy
from spotipy.oauth2 import SpotifyOAuth


def init_spotify():
    spotify = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-public",
            client_id=environ["SPOTIFY_CLIENT_ID"],
            client_secret=environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri="http://localhost",
            username=environ["SPOTIFY_USER_ID"],
        )
    )
    return spotify


def get_artist_dict():
    with open("artists_setlists_cleaned.json", "r") as input:
        json_artists = json.load(input)
        return json_artists


def create_playlists(json_artists: dict):
    user_id = environ["SPOTIFY_USER_ID"]
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
