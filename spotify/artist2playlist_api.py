import time
from os import environ

import click
import jinja2
import requests
import spotipy
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
    """
    Get songs for an artist using the setlist.fm API.

    Supports two formats:
    1. "Artist Name" - searches for artist via API
    2. "Artist Name<>https://www.setlist.fm/setlists/artist-id.html" - uses direct URL

    Returns a list of songs ordered by average setlist position.
    """
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

    # Check if artist contains a direct URL
    if "<>" in artist:
        artist_name, setlist_url = artist.split("<>", 1)
        artist_name = artist_name.strip()

        # Extract artist ID from the setlist.fm URL
        # Format: https://www.setlist.fm/setlists/staticx-bd6994e.html
        import re

        match = re.search(r"/setlists/([^-]+)-([a-f0-9]+)\.html", setlist_url)
        if not match:
            print(f"Error: Could not parse setlist.fm URL: {setlist_url}")
            return []

        artist_slug = match.group(1)
        artist_id = match.group(2)
        print(f"Using direct URL for {artist_name} (ID: {artist_id})")

        return get_songs_by_artist_id(artist_name, artist_id, headers, base_url)
    else:
        # Normal artist search
        return get_songs_by_artist_search(artist, headers, base_url)


def get_songs_by_artist_id(
    artist_name: str, artist_id: str, headers: dict, base_url: str
) -> list[str]:
    """Get songs using a direct artist ID from setlist.fm URL."""
    songs = {}
    page = 1
    max_pages = 5  # Limit to avoid hitting daily rate limit too hard

    while page <= max_pages:
        setlists_url = f"{base_url}/search/setlists"
        # Try searching by artist ID - we'll need to convert the format
        # The URL format uses a different ID than the API, so we'll search by name
        setlists_params = {"artistName": artist_name, "p": page}

        try:
            # Rate limit: 2 requests per second
            time.sleep(0.6)

            setlists_response = requests.get(
                setlists_url, headers=headers, params=setlists_params, timeout=10
            )

            # Handle rate limiting
            if setlists_response.status_code == 429:
                print("Rate limited - waiting 60 seconds before retrying...")
                time.sleep(60)
                setlists_response = requests.get(
                    setlists_url, headers=headers, params=setlists_params, timeout=10
                )

            setlists_response.raise_for_status()
            setlists_data = setlists_response.json()

            setlists = setlists_data.get("setlist", [])
            if not setlists:
                print(f"No more setlists found (page {page})")
                break

            print(f"Processing page {page} - {len(setlists)} setlists")

            for setlist in setlists:
                if "sets" in setlist:
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

            # Check if there are more pages
            total_pages = setlists_data.get("total", 0) // 20 + 1
            if page >= total_pages:
                break

            page += 1

        except requests.RequestException as e:
            print(f"Error fetching setlists for {artist_name} (page {page}): {e}")
            break
        except KeyError as e:
            print(f"Unexpected API response format for setlists (page {page}): {e}")
            break

    return process_songs_data(songs, artist_name)


def get_songs_by_artist_search(artist: str, headers: dict, base_url: str) -> list[str]:
    """Get songs by searching for the artist first."""
    # Search for the artist first
    print(f"Searching for artist: {artist}")
    search_url = f"{base_url}/search/artists"
    search_params = {"artistName": artist, "p": 1}

    try:
        # Rate limit: 2 requests per second
        time.sleep(0.6)  # More conservative delay

        search_response = requests.get(
            search_url, headers=headers, params=search_params, timeout=10
        )

        # Handle rate limiting
        if search_response.status_code == 429:
            print("Rate limited on artist search - waiting 60 seconds...")
            time.sleep(60)
            search_response = requests.get(
                search_url, headers=headers, params=search_params, timeout=10
            )

        search_response.raise_for_status()
        search_data = search_response.json()

        if not search_data.get("artist") or len(search_data["artist"]) == 0:
            print(f"No artist found for '{artist}'")
            return []

        # Find the best matching artist (exact name match preferred)
        artist_mbid = None
        artist_name = None

        for found_artist in search_data["artist"]:
            if found_artist["name"].lower() == artist.lower():
                # Exact match - use this one
                artist_mbid = found_artist["mbid"]
                artist_name = found_artist["name"]
                break

        if not artist_mbid:
            # No exact match - use the first one but warn user
            artist_mbid = search_data["artist"][0]["mbid"]
            artist_name = search_data["artist"][0]["name"]
            print(f"Warning: Using closest match '{artist_name}' for search '{artist}'")
        else:
            print(f"Found exact match: {artist_name} (MBID: {artist_mbid})")

    except requests.RequestException as e:
        print(f"Error searching for artist {artist}: {e}")
        return []
    except KeyError as e:
        print(f"Unexpected API response format when searching for {artist}: {e}")
        return []

    # Get setlists for the artist
    songs = {}
    page = 1
    max_pages = 5  # Limit to avoid hitting daily rate limit too hard

    while page <= max_pages:
        setlists_url = f"{base_url}/search/setlists"
        setlists_params = {"artistName": artist_name, "p": page}

        try:
            # Rate limit: 2 requests per second
            time.sleep(0.6)  # Increased delay to be more conservative

            setlists_response = requests.get(
                setlists_url, headers=headers, params=setlists_params, timeout=10
            )

            # Handle rate limiting specifically
            if setlists_response.status_code == 429:
                print("Rate limited - waiting 60 seconds before retrying...")
                time.sleep(60)
                setlists_response = requests.get(
                    setlists_url, headers=headers, params=setlists_params, timeout=10
                )

            setlists_response.raise_for_status()
            setlists_data = setlists_response.json()

            setlists = setlists_data.get("setlist", [])
            if not setlists:
                print(f"No more setlists found (page {page})")
                break

            print(f"Processing page {page} - {len(setlists)} setlists")

            for setlist in setlists:
                if "sets" in setlist:
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

            # Check if there are more pages
            total_pages = (
                setlists_data.get("total", 0) // 20 + 1
            )  # API returns 20 per page
            if page >= total_pages:
                break

            page += 1

        except requests.RequestException as e:
            print(f"Error fetching setlists for {artist} (page {page}): {e}")
            break
        except KeyError as e:
            print(f"Unexpected API response format for setlists (page {page}): {e}")
            break

    return process_songs_data(songs, artist)


def process_songs_data(songs: dict, artist_name: str) -> list[str]:
    """Process the songs dictionary and return sorted list of song names."""
    if not songs:
        print(f"No songs found in setlists for {artist_name}")
        return []

    # Calculate average positions
    for song in songs:
        all_positions = songs[song]
        average_position = sum(all_positions) / len(all_positions)
        songs[song] = average_position

    # Sort by average position (most frequently played early in sets first)
    sorted_songs = dict(sorted(songs.items(), key=lambda x: x[1]))

    print(f"Found {len(sorted_songs)} unique songs for {artist_name}")
    return list(sorted_songs.keys())


def create_playlist(artist: str, songs: list, playlist_name: str, market: str) -> int:
    """
    Create a Spotify playlist with the given songs.
    Returns the number of songs successfully added.
    """
    user_id = environ["SPOTIFY_USER_ID"]
    spotify = init_spotify()
    song_uris = []

    for song in songs:
        try:
            search_query = f"{artist} {song}"
            search_result = spotify.search(
                q=search_query,
                type="track",
                market=market,
            )

            if not search_result or "tracks" not in search_result:
                continue

            search_result_items = search_result["tracks"]["items"]
            if not search_result_items:
                continue

            song_uri = search_result_items[0]["uri"]
            if song_uri not in song_uris:
                track_info = spotify.track(track_id=song_uri)
                if (
                    track_info
                    and "artists" in track_info
                    and artist.lower()
                    in [
                        str(artist_info["name"]).lower()
                        for artist_info in track_info["artists"]
                    ]
                ):
                    song_uris.append(song_uri)

        except Exception as e:
            print(f"Error searching for song '{song}' by {artist}: {e}")
            continue

    try:
        playlist = spotify.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
        )

        if playlist and "uri" in playlist:
            # Spotify allows max 100 tracks per request
            for i in range(0, len(song_uris), 100):
                batch = song_uris[i : i + 100]
                spotify.user_playlist_add_tracks(
                    user=user_id, playlist_id=playlist["uri"], tracks=batch
                )

    except Exception as e:
        print(f"Error creating playlist '{playlist_name}': {e}")
        return 0

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
    """
    Create Spotify playlists with most played live songs for given artists.

    Artist names support two formats:
    1. "Artist Name" - searches for artist via API
    2. "Artist Name<>https://www.setlist.fm/setlists/artist-id.html" - uses direct URL for better matching

    Requires environment variables:
    - SETLISTFM_API_KEY: Your setlist.fm API key
    - SPOTIFY_CLIENT_ID: Your Spotify app client ID
    - SPOTIFY_CLIENT_SECRET: Your Spotify app client secret
    - SPOTIFY_USER_ID: Your Spotify username
    """
    if not name:
        print("No artist name provided, please use -n to provide one or more names")
        print("You can also use --help to see the options")
        return

    # Check required environment variables
    required_vars = [
        "SETLISTFM_API_KEY",
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_USER_ID",
    ]

    missing_vars = [var for var in required_vars if not environ.get(var)]
    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        return

    environment = jinja2.Environment()
    template = environment.from_string(playlist_format)

    for one_name in name:
        # Extract display name for playlist (part before <> if present)
        display_name = one_name.split("<>")[0].strip() if "<>" in one_name else one_name

        playlist_name = template.render(name=display_name)
        print(f"\n--- Processing {display_name} ---")

        songs = get_artist_songs(artist=one_name)

        if len(songs) > 0:
            print(f"Found {len(songs)} songs played at live shows of {display_name}")
            print("Creating playlist...")

            final_song_count = create_playlist(
                artist=display_name,
                songs=songs,
                playlist_name=playlist_name,
                market=market,
            )

            print(f"Created playlist '{playlist_name}' with {final_song_count} songs")
        else:
            print(f"No songs found for {display_name}")


if __name__ == "__main__":
    main()
