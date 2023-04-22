import os
import sys
import shutil
import urllib.request
from PIL import Image


def main():
    print("VSCHT Book Downloader\n")
    print("This tool downloads and merges books from the VSCHT website.")
    print("The expected URL format is 'https://vydavatelstvi.vscht.cz/katalog/publikace?uid=uid_isbn-XXX-XX-XXXX-XXX-X'\n")
    # Example (62 pages)
    # https://vydavatelstvi.vscht.cz/katalog/publikace?uid=uid_isbn-978-80-7592-112-3
    url_base = input("URL: ")
    url = f"https://vydavatelstvi-old.vscht.cz/knihy/uid_isbn-{url_base[-17:]}/img/"
    name = input("Name of the book: ")
    save_path = f"{os.path.join(os.getenv('USERPROFILE'), 'Downloads')}"
    temp_dir = f"{save_path}\{name}_temp"
    os.mkdir(temp_dir)
    counter = 1
    while True:
        current_url = f"{url}{counter:0>3}.png"
        current_dir = f"{temp_dir}\{counter:0>3}.png"
        try:
            urllib.request.urlretrieve(current_url, current_dir)
            print(f"Downloading page {counter}", end="\r")
        except:
            # yeah yeah i know
            break
        counter += 1
    image_list = []
    for image in os.listdir(temp_dir):
        image_path = os.path.join(temp_dir, image)
        if image == "001.png":
            first_open = Image.open(image_path)
            first_rgb = first_open.convert("RGB")
        else:
            image_open = Image.open(image_path)
            image_rgb = image_open.convert("RGB")
            image_list.append(image_rgb)
    first_rgb.save(f"{save_path}\{name}.pdf", save_all=True, append_images=image_list)
    shutil.rmtree(temp_dir)
    os.startfile(save_path)
    sys.exit()


if __name__ == "__main__":
    main()
