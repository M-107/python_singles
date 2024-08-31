import json
from os import environ

from steam import Steam


def main():
    steam = Steam(environ["STEAM_API_KEY"])
    my_id = environ["STEAM_MY_ID"]
    my_games = steam.users.get_owned_games(steam_id=my_id)
    print(f"Found {my_games['game_count']} games")
    game_dict = my_games["games"]
    results_list = []
    for game_num in range(0, len(game_dict)):
        print(f"Working on game {game_num:>4}", end="\r")
        appid = game_dict[game_num]["appid"]
        details = steam.apps.get_app_details(
            app_id=appid, filters="basic,genres,fullgame"
        )
        results_list.append(details)
    print("Saving game info")
    with open("game_info.json", "w") as output:
        json.dump(results_list, output)


if __name__ == "__main__":
    main()
