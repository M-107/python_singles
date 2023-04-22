import os
import tkinter as tk
from tkinter.filedialog import askopenfilenames
from matplotlib import pyplot as plt
import seaborn as sns


def makeXY(file):
    lines = []
    with open(file, "r") as f:
        for line in f:
            y = line.split()
            lines.append(y)
    lines = lines[:-1]
    for j in lines:
        number = float(j[0][:-6])
        exponent = int(j[0][-1])
        newNumber = number * 10 ** exponent
        j[0] = newNumber
        j[1] = int(j[1])
    x = [x[0] for x in lines]
    y = [x[1] for x in lines]
    return x, y


def main():
    root = tk.Tk()
    root.withdraw()
    files = askopenfilenames(title="Select the ASC files with RTG data.",
                             filetypes=[("ASC files", ".asc")])

    # Make a simple graphs from asc data
    for iNum, file in enumerate(files, 1):
        print(f"Working on file {iNum} out of {len(files)}")
        x, y = makeXY(file)
        sns.set_theme()
        sns.set_style("whitegrid")
        plt.plot(x, y, "k")
        plt.xlim(min(x), max(x))
        plt.ylim(min(y), max(y))
        plt.title(os.path.split(file)[1][:-4])
        plt.xlabel("2Θ")
        plt.ylabel("intensity")
        # mng = plt.get_current_fig_manager()
        # mng.window.state("zoomed")
        # plt.show()
        plt.gcf().set_size_inches(16, 9)
        plt.savefig(f"{file[:-3]}png", dpi=300)
        plt.close()


if __name__ == "__main__":
    main()
