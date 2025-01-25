*A collection of somewhat usable Python scripts for automating various data collection tasks in mostly polymer materials research or made just for fun.*

## Lab Stuff

[**asc2png**](lab/asc2png.py) - Converts text files with data measured with Wide Angle Xray Spectroscopy (WAXS) into graphs comparing the X-Ray source position to the radiation intensity.

[**pb_blends**](lab/pb_blends.py) - Analyzes how the properties of polymers measured via WAXS change over time. Multiple plot options.

[**waxs2text**](lab/waxs2text.py) - Converts WAXS data in various formats into a unified TXT format for further processing.

[**waxsreader**](lab/waxsreaders.py) - Utility functions for the other WAXS scripts. Readers of multiple formats for various WAXS machines.

[**dsc_eval**](lab/dsc_eval.py) - Evaluates melting and crystalization temperatures of polymers measured with Differential Scanning Calorimetry.

[**cti2xlsx**](lab/cti2xlsx.py) - Converts measurements of material transmissivity and emissivity into Excel sheets.

[**density_one_year**](lab/density_one_year.py) - Visualises the density of polymers based on their irradiation dose in a graph form.


## Spotify Stuff

[**spotify_playlist_to_json**](spotify/spotipy_playlist_to_json.py) - Converts a Spotify playlist with all available information for each track into a JSON file.

[**setlist2json**](spotify/setlist2json.py) - Takes the bands from a list and generates a JSON file with their most played songs at shows, according to setlist.fm. The JSON might need some cleanup, for example with foreign characters.

[**json2spotify**](spotify/json2spotify.py) - Takes the JSON created by previous script and creates Spotify playlists out of it.

[**artist2playlist**](spotify/artist2playlist.py) - Combination of the previous two scripts. Asks for a name and generates a playlist with the most played songs at live shows from an artist (or multiple artists at once).


## Reddit Stuff

[**reddit_thread_activity**](reddit/reddit_thread_acitivity.py) - Measures how active a specific reddit thread is over time (how many new comments appear each 'x' seconds).

[**subreddit_top_post_users_to_json**](reddit/subreddit_top_post_users_to_json.py) - Takes the top posts from a selected subreddit and saves their info and info about their comments into a JSON file for further processing.


## Random Stuff

[**ab2data**](random/ab2data.py) - Tool for transforming bank statements from AirBank to usable data formats (CSV, JSON, JSONL), as the bank only supplies them as PDFs to regular account holders.

[**abdata_viz**](random/abdata_viz.py) - Uses the jsonl output of ab2data to get some basic information and graphs the daily changes and total account balance. Can be extended.

[**clickhash**](random/clickhash.py) - Simple CLI tool that hashes and unhashes strings or files.

[**sudoku_solver**](random/sudoku_solver.py) - Bruteforce Sudoku solver. Initial state can be entered manually. The solution progress is visualised, which can be turned off for increased performance.

[**key_distance**](random/key_distance.py) - Measures how "long" and "pointy" words are when typed on a keyboard with set dimensions.

[**pyxel_pong**](random/pyxel_pong.py) - Pong clone utilizing the Pyxel library.

[**asyncio_test**](random/asyncio_test.py) - Test script for trying out async downloading.

[**make_random_map**](random/make_random_map.py) - Make a 2D map using and properly arranging sprites matching a randomly generated matrix.

[**playfair_cypher**](random/playfair_cipher.py) - Implementation for encoding and decoding text using the Playfair cipher.

[**sreality_scraper**](random/sreality_scraper.py) - Scrapes the Sreality website for house prices and saves the output to a CSV file.

[**vscht_book_downloader**](random/vscht_book_downloader.py) - Tool for downloading books in PDF form from the VSCHT website, which only serves one page at a time.
