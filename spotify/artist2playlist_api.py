import time
from datetime import datetime, timedelta
from os import environ

import click
import jinja2
import requests
import spotipy
from requests.adapters import HTTPAdapter
from spotipy.oauth2 import SpotifyOAuth
from urllib3.util import Retry


def init_spotify() -> spotipy.Spotify:
    spotify = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-public",
            client_id=environ["SPOTIFY_CLIENT_ID"],
            client_secret=environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri="http://127.0.0.1:8888/callback",
            username=environ["SPOTIFY_USER_ID"],
        )
    )
    return spotify


def get_artist_songs(artist: str, max_age: int) -> list[str]:
    api_key = environ.get("SETLISTFM_API_KEY")
    if not api_key:
        print("Error: SETLISTFM_API_KEY environment variable not set")
        return []
    base_url = "https://api.setlist.fm/rest/1.0"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "User-Agent": "artist2playlist/1.0 (https://github.com/M-107/python_singles)",
    }
    return get_songs_by_artist_search(artist, headers, base_url, max_age)


def make_setlistfm_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


SETLISTFM_SESSION = make_setlistfm_session()


def make_api_request(url: str, headers: dict, params: dict, timeout: int = 10) -> dict | None:
    time.sleep(0.6)
    try:
        response = SETLISTFM_SESSION.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request to {url}: {e}")
        return None


def find_artist_data(artist: str, headers: dict, base_url: str) -> tuple[str | None, str | None]:
    print(f"Searching for artist: {artist}")
    search_url = f"{base_url}/search/artists"
    search_params = {"artistName": artist, "p": 1}
    search_data = make_api_request(search_url, headers, search_params)
    if not search_data or not search_data.get("artist"):
        print(f"No artist found for '{artist}'")
        return None, None
    for found_artist in search_data["artist"]:
        if found_artist["name"].lower() == artist.lower():
            print(f"Found exact match: {found_artist['name']} (MBID: {found_artist['mbid']})")
            return found_artist["mbid"], found_artist["name"]
    closest = search_data["artist"][0]
    print(f"Warning: Using closest match '{closest['name']}' for search '{artist}'")
    return closest["mbid"], closest["name"]


def extract_songs_from_setlists(setlists: list, max_age: int) -> tuple[dict[str, list[int]], bool]:
    songs = {}
    cutoff_date = datetime.now() - timedelta(days=max_age)
    found_old = False
    for setlist in setlists:
        try:
            set_date = datetime.strptime(setlist["eventDate"], "%d-%m-%Y")
            if set_date < cutoff_date:
                found_old = True
                break
            if "sets" not in setlist:
                continue
            position = 1
            for set_data in setlist["sets"]["set"]:
                if "song" in set_data:
                    for song in set_data["song"]:
                        if "name" in song:
                            song_name = song["name"]
                            if song_name in songs:
                                songs[song_name].append(position)
                            else:
                                songs[song_name] = [position]
                            position += 1
        except (KeyError, ValueError):
            continue
    return songs, found_old


def get_songs_by_artist_search(artist: str, headers: dict, base_url: str, max_age: int) -> list[str]:
    _, artist_name = find_artist_data(artist, headers, base_url)
    if not artist_name:
        return []
    all_songs = {}
    page = 1
    max_pages = 5
    print("Processing setlists...")
    while page <= max_pages:
        setlists_url = f"{base_url}/search/setlists"
        setlists_params = {"artistName": artist_name, "p": page}
        setlists_data = make_api_request(setlists_url, headers, setlists_params)
        if not setlists_data:
            break
        setlists = setlists_data.get("setlist", [])
        if not setlists:
            break
        page_songs, found_old = extract_songs_from_setlists(setlists, max_age)
        for song_name, positions in page_songs.items():
            if song_name in all_songs:
                all_songs[song_name].extend(positions)
            else:
                all_songs[song_name] = positions
        if found_old:
            break
        total_pages = setlists_data.get("total", 0) // 20 + 1
        if page >= total_pages or page >= max_pages:
            break
        page += 1
    return process_songs_data(all_songs, artist)


def process_songs_data(songs: dict[str, list[int]], artist_name: str) -> list[str]:
    if not songs:
        print(f"No songs found in setlists for {artist_name}")
        return []
    song_averages = {song: sum(positions) / len(positions) for song, positions in songs.items()}
    return [song for song, _ in sorted(song_averages.items(), key=lambda x: x[1])]


def find_spotify_track(spotify: spotipy.Spotify, artist: str, song: str, market: str) -> str | None:
    try:
        search_query = f"{artist} {song}"
        search_result = spotify.search(q=search_query, type="track", market=market)
        if not search_result or "tracks" not in search_result:
            return None
        items = search_result["tracks"]["items"]
        if not items:
            return None
        song_uri = items[0]["uri"]
        track_info = spotify.track(track_id=song_uri)
        if track_info and "artists" in track_info:
            artist_names = [a["name"].lower() for a in track_info["artists"]]
            if artist.lower() in artist_names:
                return song_uri
        return None
    except Exception as e:
        print(f"Error searching for song '{song}' by {artist}: {e}")
        return None


def create_playlist(artist: str, songs: list, playlist_name: str, market: str) -> int:
    user_id = environ["SPOTIFY_USER_ID"]
    spotify = init_spotify()
    song_uris = []
    for song in songs:
        uri = find_spotify_track(spotify, artist, song, market)
        if uri and uri not in song_uris:
            song_uris.append(uri)
    if not song_uris:
        print("No matching tracks found on Spotify")
        return 0
    try:
        playlist = spotify.user_playlist_create(user=user_id, name=playlist_name, public=True)
        if not playlist or "uri" not in playlist:
            print(f"Error creating playlist '{playlist_name}'")
            return 0
        for i in range(0, len(song_uris), 100):
            batch = song_uris[i : i + 100]
            spotify.user_playlist_add_tracks(user=user_id, playlist_id=playlist["uri"], tracks=batch)
        return len(song_uris)
    except Exception as e:
        print(f"Error creating playlist '{playlist_name}': {e}")
        return 0


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
@click.option("-m", "--market", default="CZ", help="Market for Spotify search. Default is CZ")
@click.option(
    "-ma",
    "--max-age",
    default=365,
    help="Maximum age of setlists in days to consider. Default is 365 days.",
)
def main(name, playlist_format, market, max_age):
    if not name:
        print("No artist name provided, please use -n to provide one or more names")
        print("You can also use --help to see the options")
        return
    required_vars = [
        "SETLISTFM_API_KEY",
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_USER_ID",
    ]
    missing_vars = [var for var in required_vars if not environ.get(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return
    environment = jinja2.Environment()
    template = environment.from_string(playlist_format)
    for one_name in name:
        playlist_name = template.render(name=one_name)
        print(f"\n--- Processing {one_name} ---")
        songs = get_artist_songs(artist=one_name, max_age=max_age)
        if len(songs) > 0:
            print(f"Found {len(songs)} unique songs for {one_name} that were played less than {max_age} days ago")
            print("Creating playlist...")
            final_song_count = create_playlist(
                artist=one_name,
                songs=songs,
                playlist_name=playlist_name,
                market=market,
            )
            print(f"Created playlist '{playlist_name}' with {final_song_count} songs")
        else:
            print(f"No songs found for {one_name}")


if __name__ == "__main__":
    main()
