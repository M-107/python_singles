import math
from cmath import sqrt

# https://youtu.be/Mf2H9WZSIyw

KEYS = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Z", "X", "C", "V", "B", "N", "M"],
]
# Legion Y520 values
DIST = 19
SHIFT = [0, 7, 16]


def key_pos(key):
    for x, i in enumerate(KEYS):
        if key.upper() in i:
            key_row = x
            key_col = i.index(key.upper())
    key_x = SHIFT[key_row] + DIST * key_col
    key_Y = key_row * DIST
    return [key_x, key_Y]


def key_dist(key_1, key_2):
    delta_x = abs(key_pos(key_1)[0] - key_pos(key_2)[0])
    delta_y = abs(key_pos(key_1)[1] - key_pos(key_2)[1])
    key_dist = round(sqrt(delta_x**2 + delta_y**2).real, 2)
    return key_dist


def key_angle(key_1, key_2, key3):
    angle = math.degrees(
        math.atan2(
            key_pos(key3)[1] - key_pos(key_2)[1], key_pos(key3)[0] - key_pos(key_2)[0]
        )
        - math.atan2(
            key_pos(key_1)[1] - key_pos(key_2)[1], key_pos(key_1)[0] - key_pos(key_2)[0]
        )
    )
    return angle + 360 if angle < 0 else angle


def word_length(word):
    length = 0.0
    for i in range(0, len(word[:-1])):
        length += key_dist(word[i], word[i + 1])
    return round(length, 2)


def word_angle(word):
    angle = 0.0
    for i in range(0, len(word[:-2])):
        angle += key_angle(word[i], word[i + 1], word[i + 2])
    return round(angle, 2)


def main():
    while True:
        word = input("Please input a word: ")
        if word.isalpha():
            w_out = word.lower()
            w_len = word_length(word)
            w_ang = word_angle(word)
            print(f"\nWord to check: {w_out}")
            print(f"    Length: {w_len} mm")
            print(f"    Angle:  {w_ang} °\n")
        else:
            print("Please input only a signle word using the english alphabet.\n")


if __name__ == "__main__":
    main()
