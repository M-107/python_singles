from waxsreaders import *
import tkinter as tk
from tkinter.filedialog import askopenfilenames

FORMATS = {
    "asc" : get_xy_asc,
    "itx" : get_xy_itx,
    "ras" : get_xy_ras,
    "scn" : get_xy_scn,
    "xrdml" : get_xy_xrdml,
}

print("Select the files with RTG data\n")

root = tk.Tk()
root.withdraw()
files = askopenfilenames(
    title="Select the files with RTG data",
    filetypes=[("RTG data files", ".asc .itx .ras .scn .xrdml")],
)

for file in files:
    print(f"Working on file: {file}")
    new_file = ".".join(file.split(".")[:-1]) + ".txt"
    filetype = file.split(".")[-1].lower()
    try:
        x_list, y_list = FORMATS[filetype](file)
    except ValueError:
        print(" Couldn't read file. Skipping to next one.")
        continue
    x_math_list = []
    for x in x_list:
        formatted = "{:.14E}".format(x)
        parts = formatted.split("E+")
        number = parts[0]
        exponent = parts[1]
        new_exponent = exponent.rjust(4, "0")
        new_x = f"{number}E+{new_exponent}"
        x_math_list.append(new_x)
    xy_list = list(zip(x_math_list, y_list))
    with open(new_file, 'w') as f:
        for pair in xy_list:
            x, y = pair
            line = f"{x}  {y}\n"
            f.write(line)

print("\nDone\nPress any key to exit")
input()
