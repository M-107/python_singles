import os
import time
from pathlib import Path

import numpy as np


class Letter:
    def __init__(self, sym: str, x: int, y: int) -> None:
        self.sym = sym
        self.x = x
        self.y = y

    def __repr__(self):
        return f"{self.sym} [{self.x}:{self.y}]"


class LetterBox:
    def __init__(self, letters: list[Letter], width: int, height: int) -> None:
        self.letters = letters
        self.width = width
        self.height = height
        self.array = [[" " for i in range(self.width)] for j in range(self.height)]

    def fill_array(self):
        for letter in self.letters:
            self.array[letter.y][letter.x] = letter.sym

    def reset_array(self):
        for row_n, row in enumerate(self.array):
            for column_n, _ in enumerate(row):
                self.array[row_n][column_n] = " "

    def print_array(self):
        for row in self.array:
            one_row = []
            if row:
                for letter in row:
                    if letter:
                        one_row.append(letter)
                    else:
                        one_row.append(" ")
                print("".join(one_row))
            else:
                print("")
        print("\033[A" * self.height)

    def fall_step(self):
        for letter in self.letters:
            if not letter.y == self.height - 1:
                letter.y += 1
        self.reset_array()
        self.fill_array()


text_file = r"C:\Users\marti\Documents\text.txt"
if Path(text_file).exists():
    with open(text_file, "r") as file:
        text = file.read()
else:
    print("Please enter a path to an existing text file.")

t_size = os.get_terminal_size()
width = t_size.columns
height = t_size.lines - 1
letters = []

current_x = 0
current_y = 0

for char in text:
    byte = bytes(str(char), "ascii")
    if byte == b"\n":
        current_y += 1
        current_x = 0
    else:
        if current_x > width:
            current_x = 0
        decoded = byte.decode()
        if decoded != " ":
            letters.append(Letter(decoded, current_x, current_y))
        current_x += 1
print("")
letterbox = LetterBox(letters, width, height)
letterbox.fill_array()
for i in range(200):
    letterbox.print_array()
    letterbox.fall_step()
    time.sleep(0.1)
