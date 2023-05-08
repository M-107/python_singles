import json
import yaml
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

D_KEYS = {
    -1: "Not identified",
    0: "C",
    1: "C#/Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "F#/Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "Cb/B",
}
D_MODE = {
    0: "Minor",
    1: "Major",
}
D_TSIG = {
    1: "Not identified",
    3: "3/4",
    4: "4/4",
    5: "5/4",
    6: "6/4",
    7: "7/4",
}


def init_spotify():
    with open(".credentials.yaml", "r") as f:
        credentials = yaml.safe_load(f)
    spotify = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=credentials["spotify"]["client_id"],
            client_secret=credentials["spotify"]["client_secret"],
        )
    )
    return spotify


def get_playlist_data(spotify, playlist_link):
    while True:
        try:
            playlist = spotify.playlist(playlist_link)
            playlist_name = playlist["name"]
            print(f"\nPlaylist found: {playlist_name}")
            break
        except spotipy.exceptions.SpotifyException:
            print("\nCouldn't find a playlist with the input link.")
            print("The link should look like:")
            print("https://open.spotify.com/playlist/abcd1234\n")

    track_urls = []
    offset = 0
    while True:
        tracks = spotify.playlist_tracks(playlist_link, offset=offset)
        if not tracks['items']:
            break
        for item in tracks['items']:
            track_link = item['track']['external_urls']['spotify']
            track_urls.append(track_link)
        offset += len(tracks['items'])

    track_dict_list = []
    for enum, track_id in enumerate(track_urls, 1):
        print(f"    Working on track {enum}/{len(track_urls)}")

        track_info = spotify.track(track_id=track_id)
        track_name = track_info["name"]
        track_artists = [artist["name"] for artist in track_info["artists"]]
        track_album = track_info["album"]["name"]
        track_album_art = track_info["album"]["images"][0]["url"]
        album_genres = spotify.album(track_info["album"]["id"])["genres"]
        artists_genres = [genre for artist_genres in [spotify.artist(artist_id)["genres"] for artist_id in [artist["id"] for artist in track_info["artists"]]] if artist_genres for genre in artist_genres]
        track_genres = album_genres if album_genres else list(set(artists_genres)) if artists_genres else []

        audio_features = spotify.audio_features(track_id)
        track = audio_features[0]
        dance = int(round(track["danceability"] * 100, 0))
        energy = int(round(track["energy"] * 100, 0))
        key_val = track["key"]
        key = D_KEYS[key_val]
        loud = round(track["loudness"], 1)
        mode_val = track["mode"]
        mode = D_MODE[mode_val]
        speech = int(round(track["speechiness"] * 100, 0))
        acoust = int(round(track["acousticness"] * 100, 0))
        instr = int(round(track["instrumentalness"] * 100, 0))
        live = int(round(track["liveness"] * 100, 0))
        vale = int(round(track["valence"] * 100, 0))
        tempo = int(round(track["tempo"], 0))
        durs = int(track["duration_ms"] / 1000)
        timesig_val = track["time_signature"]
        timesig = D_TSIG[timesig_val]

        dict_transformed = {
            "artist": track_artists,
            "track_album": track_album,
            "track_album_art": track_album_art,
            "track_name": track_name,
            "track_genres": track_genres,
            "danceability": dance,
            "energy": energy,
            "key_val": key_val,
            "key": key,
            "loudness": loud,
            "mode_val": mode_val,
            "mode": mode,
            "speechiness": speech,
            "acousticness": acoust,
            "instrumentalness": instr,
            "liveness": live,
            "valence": vale,
            "tempo": tempo,
            "duration": durs,
            "timesig_val": timesig_val,
            "timesig": timesig,
        }
        track_dict_list.append(dict_transformed)
    return track_dict_list, playlist_name


def dump_info(track_info, out_file):
    with open(out_file, "w") as f:
        json.dump(track_info, f, indent=3)
    print(f"\nDone\nTrack info saved to {out_file}")


def main():
    playlist_link = input("Enter a link to a Spotify playlist:\n")
    spotify = init_spotify()
    track_info, playlist_name = get_playlist_data(spotify, playlist_link)
    dump_info(track_info, f"track_info_{playlist_name}.json")


if __name__ == "__main__":
    main()
