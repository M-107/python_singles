import aiohttp
import asyncio
import requests
import time
from pathlib import Path


VIDEO_LINK = "https://file-examples.com/wp-content/storage/2017/04/file_example_MP4_1920_18MG.mp4"
WORKDIR = Path.home() / "test_downloads"
BLUE = "\033[94m"
WHITE = "\033[0m"


class FolderClass():
    def __init__(self, workdir, path, link):
        self.workdir = workdir
        self.path = path
        self.link = link

    @property
    def path_absolute(self):
        return Path(self.workdir / self.path)

    def download_prep(self):
        file_path = Path(self.path_absolute) / "video.mp4"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path

    def download(self):
        file_path = self.download_prep()
        response = requests.get(self.link, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)

    async def download_async(self, session):
        file_path = self.download_prep()
        async with session.get(self.link) as response:
            response.raise_for_status()
            with open(file_path, "wb") as file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    file.write(chunk)


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"    Function {BLUE}{func.__name__}{WHITE} executed in {BLUE}{round(execution_time, 3)}{WHITE} seconds")
        return result
    return wrapper


def create_objects(subfolder_name, num_objects):
    c_list = [FolderClass(WORKDIR, f"{subfolder_name}/vid_{i}", VIDEO_LINK) for i in range(num_objects)]
    return c_list


@timer
def download_synchronous(c_list):
    for c in c_list:
        c.download()


async def async_download(c_list):
    async with aiohttp.ClientSession() as session:
        tasks = [c.download_async(session) for c in c_list]
        await asyncio.gather(*tasks)


@timer
def download_asynchronous(c_list):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_download(c_list))
    loop.close()


def main():
    test_number = 30
    print(f"Downloading {test_number} test files into {WORKDIR}")
    download_synchronous(create_objects("synchronous", test_number))
    download_asynchronous(create_objects("asynchronous", test_number))


if __name__ == "__main__":
    main()
