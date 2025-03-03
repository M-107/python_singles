from os import environ

import click
import jinja2
import requests
import spotipy
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth


def init_spotify() -> spotipy.Spotify:
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


def get_artist_songs(artist: str) -> list[str]:
    search_query = artist.lower().replace(" ", "+")
    page_url = f"https://www.setlist.fm/search?query={search_query}"
    page_response = requests.get(page_url)
    page_soup = BeautifulSoup(page_response.content, "html.parser")
    results = page_soup.find_all("div", {"class": "col-xs-12 setlistPreview"})
    songs = {}
    for result in results:
        anchor = result.find("a")
        href = anchor["href"]
        setlist_url = f"https://www.setlist.fm/{href}"
        setlist_response = requests.get(setlist_url)
        setlist_soup = BeautifulSoup(setlist_response.content, "html.parser")
        song_list = setlist_soup.find_all("li", {"class": "setlistParts song"})
        for position, song in enumerate(song_list, start=1):
            song_name = song.find("a", {"class": "songLabel"})
            if song_name:
                song_name_string = song_name.get_text()
                if song_name_string in songs:
                    songs[song_name_string].append(position)
                else:
                    songs[song_name_string] = [position]
    for song in songs:
        all_positions = songs[song]
        average_postion = sum(all_positions) / len(all_positions)
        songs[song] = average_postion
    sorted_songs = dict(sorted(songs.items(), key=lambda x: x[1]))
    return list(sorted_songs.keys())


def create_playlist(artist: str, songs: list, playlist_name: str, market: str) -> int:
    user_id = environ["SPOTIFY_USER_ID"]
    spotify = init_spotify()
    song_uris = []
    for song in songs:
        search_query = f"{artist} {song}"
        search_result = spotify.search(
            q=search_query,
            type="track",
            market=market,
        )
        search_result_items = search_result["tracks"]["items"]
        song_uri = search_result_items[0]["uri"]
        if song_uri not in song_uris and artist.lower() in [
            str(artist["name"]).lower()
            for artist in spotify.track(track_id=song_uri)["artists"]
        ]:
            song_uris.append(song_uri)
    playlist = spotify.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=True,
    )
    spotify.user_playlist_add_tracks(
        user=user_id, playlist_id=playlist["uri"], tracks=song_uris
    )
    return len(song_uris)


@click.command()
@click.option(
    "-n",
    "--name",
    help="Name of the artist (can be provided multiple times)",
    multiple=True,
)
@click.option(
    "-pf",
    "--playlist-format",
    default="{{name}} - Most Played Live",
    help="Playlist name format. Use {{name}} to use the entered artist name. Default is: {{name}} - Most Played Live",
)
@click.option(
    "-m", "--market", default="CZ", help="Market for Spotify search. Default is CZ"
)
def main(name, playlist_format, market):
    if not name:
        print("No artist name provided, please use -n to provide one or more names")
        print("You can also use --help to see the options")
    environment = jinja2.Environment()
    template = environment.from_string(playlist_format)
    for one_name in name:
        playlist_name = template.render(name=one_name)
        print(f"Searching for songs by {one_name}...")
        songs = get_artist_songs(artist=one_name)
        if len(songs) > 0:
            print(f"Found {len(songs)} songs played at live shows of {one_name}")
            print("Creating playlist...")
            final_song_count = create_playlist(
                artist=one_name, songs=songs, playlist_name=playlist_name, market=market
            )
            print(f"Created playlist '{playlist_name}' with {final_song_count} songs")
        else:
            print(
                f"No songs found for {one_name}There are either no published setlists or a typo in the artist name."
            )


if __name__ == "__main__":
    main()
