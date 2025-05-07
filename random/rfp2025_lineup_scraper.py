from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

STAGE_NAMES = {
    "stage-3": "KB Stage",
    "stage-4": "Tesco Stage",
    "stage-5": "E2 Stage",
    "stage-6": "ČT Art Stage",
    "stage-7": "Conference Stage",
    "stage-8": "Solar Stage",
    "stage-74": "Karaoke Stage",
    "stage-75": "Petr Svoboda Stage",
}

EVENT_TYPES = {
    "lineup": "concert",
    "program": "other",
}

DAY_MAP = {
    "Středa 11. 6.": datetime(2025, 6, 11).date(),
    "Čtvrtek 12. 6.": datetime(2025, 6, 12).date(),
    "Pátek 13. 6.": datetime(2025, 6, 13).date(),
    "Sobota 14. 6.": datetime(2025, 6, 14).date(),
    "Neděle 15. 6.": datetime(2025, 6, 15).date(),
}


@dataclass
class Show:
    name: str
    day: datetime
    start_time: datetime
    end_time: datetime
    stage_name: str
    type: str

    def __str__(self) -> str:
        return f"{self.name} - {self.day} {self.start_time} - {self.end_time} ({self.stage_name}) [{self.type}]"

    @property
    def duration(self) -> int:
        return int(
            (
                datetime.combine(self.day, self.end_time)
                - datetime.combine(self.day, self.start_time)
            ).seconds
            / 60
        )


def download_page() -> Path:
    snapshot_path = Path("snapshot.html")
    target_url = "https://rockforpeople.cz/harmonogram/"
    if not snapshot_path.exists():
        response = requests.get(target_url)
        if response.status_code == 200:
            with open(snapshot_path, "w", encoding="utf-8") as file:
                file.write(response.text)
        else:
            raise Exception(
                f"Failed to retrieve the page. Status code: {response.status_code}"
            )
    return snapshot_path


def parse_page(snapshot_path: Path) -> list[Show]:
    all_shows: list[Show] = []
    with open(snapshot_path, "r", encoding="utf-8") as file:
        page_content = file.read()
    soup = BeautifulSoup(page_content, "html.parser")
    schedule_table = soup.find("div", class_="block-harmonogram")
    days = schedule_table.find_all("div", class_="timetable__day")
    for day in days:
        day_name = day.find("h2").text.strip()
        stages = day.find_all("div", class_="timetable__stagetime")
        for stage in stages:
            stage_name = stage["data-stage"]
            events = stage.find_all("div", class_="timetable__entry")
            for event in events:
                name = event.find("span", class_="name").text.strip()
                time = event.find("span", class_="time").text.strip()
                event_type = event["data-type"]
                start_time_str, end_time_str = time.split(" – ")
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
                show = Show(
                    name=name,
                    day=DAY_MAP[day_name],
                    start_time=start_time,
                    end_time=end_time,
                    stage_name=STAGE_NAMES[stage_name],
                    type=EVENT_TYPES[event_type],
                )
                all_shows.append(show)
    return all_shows


def print_shows(all_shows: list[Show]) -> None:
    for show in all_shows:
        print(show)


def save_csv(all_shows: list[Show]) -> None:
    with open("shows.csv", "w", encoding="utf-8") as file:
        file.write("name,day,start_time,end_time,duration,stage_name,type\n")
        for show in all_shows:
            file.write(
                f"{show.name},{show.day},{show.start_time.strftime("%H:%M")},{show.end_time.strftime("%H:%M")},{show.duration},{show.stage_name},{show.type}\n"
            )


if __name__ == "__main__":
    snapshot = download_page()
    shows = parse_page(snapshot)
    print_shows(shows)
    save_csv(shows)
