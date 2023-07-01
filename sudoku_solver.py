import numpy as np

class Sudoku():
    def __init__(self) -> None:
        self.array = np.zeros([9,9])
        self.init_array = np.zeros([9,9])
        self.WHITE = "\033[0m"
        self.RED = "\033[91m"
        self.GREEN = "\033[92m"
        self.BLUE = "\033[94m"

    def __repr__(self):
        rows, cols = self.array.shape
        output = ""
        output += f"┌{'─'*7}┬{'─'*7}┬{'─'*7}┐" + "\n"
        for i in range(rows):
            if i % 3 == 0 and i != 0:
                output += f"├{'─'*7}┼{'─'*7}┼{'─'*7}┤" + "\n"
            output += "│ "
            for j in range(cols):
                if j % 3 == 0 and j != 0:
                    output += "│ "
                if self.init_array[i][j] == 0 and not self.array[i][j] == 0:
                    output += self.GREEN + str(int(self.array[i][j])).replace("0", "_") + self.WHITE + " "
                else:
                    output += str(int(self.array[i][j])).replace("0", "_") + " "
            output += "│\n"
        output += f"└{'─'*7}┴{'─'*7}┴{'─'*7}┘" + "\n"
        return output

    def print_me(self, current_x, current_y):
        rows, cols = self.array.shape
        output = ""
        output += f"┌{'─'*7}┬{'─'*7}┬{'─'*7}┐" + "\n"
        for i in range(rows):
            if i % 3 == 0 and i != 0:
                output += f"├{'─'*7}┼{'─'*7}┼{'─'*7}┤" + "\n"
            output += "│ "
            for j in range(cols):
                if j % 3 == 0 and j != 0:
                    output += "│ "
                if i == current_x and j == current_y:
                    output += self.BLUE + str(int(self.array[i][j])).replace("0", "_") + self.WHITE + " "
                elif self.init_array[i][j] == 0 and self.array[i][j] == 0:
                    output += self.RED + str(int(self.array[i][j])).replace("0", "_") + self.WHITE + " "
                elif self.init_array[i][j] == 0:
                    output += self.GREEN + str(int(self.array[i][j])).replace("0", "_") + self.WHITE + " "
                else:
                    output += str(int(self.array[i][j])).replace("0", "_") + " "
            output += "│\n"
        output += f"└{'─'*7}┴{'─'*7}┴{'─'*7}┘" + "\n"
        return output

    def set_state(self, input: list):
        if len(input) != 9:
            raise ValueError("Input list should contain 9 lists.")
        for i in range(len(input)):
            row = input[i]
            if len(row) != 9:
                raise ValueError("Each inner list should contain 9 elements.")
            for j in range(len(row)):
                value = row[j]
                if value is None:
                    self.array[i][j] = 0
                    self.init_array[i][j] = 0
                elif isinstance(value, int) and 1 <= value <= 9:
                    self.array[i][j] = value
                    self.init_array[i][j] = value
                else:
                    raise ValueError(f"Invalid value found in input list: {value} at R{i+1} C{j+1}")

    def check(self):
        for i in range(9):
            row_values = [value for value in self.array[i] if value != 0]
            col_values = [value for value in self.array[:, i] if value != 0]
            if len(row_values) != len(set(row_values)):
                return False
            if len(col_values) != len(set(col_values)):
                return False
        for i in range(0, 9, 3):
            for j in range(0, 9, 3):
                subgrid_values = [
                    value
                    for value in self.array[i:i+3, j:j+3].flatten()
                    if value != 0
                ]
                if len(subgrid_values) != len(set(subgrid_values)):
                    return False
        return True

    def solve(self, printout=False):
        if printout:
            print("  Solving the sudoku...")
        if not self.check():
            return False
        return self._solve(printout)

    def _solve(self, printout):
        for i in range(9):
            for j in range(9):
                if self.array[i][j] == 0 and self.init_array[i][j] == 0:
                    for num in range(1, 10):
                        self.array[i][j] = num
                        if printout:
                            print(self.print_me(i, j), end="\033[F" * 13)
                        if self.check():
                            if self._solve(printout):
                                return True
                    self.array[i][j] = 0
                    return False
        return True


def main():
    sudoku = Sudoku()
    initial_state = [
        [5, 3, None, None, 7, None, None, None, None],
        [6, None, None, 1, 9, 5, None, None, None],
        [None, 9, 8, None, None, None, None, 6, None],
        [8, None, None, None, 6, None, None, None, 3],
        [4, None, None, 8, None, 3, None, None, 1],
        [7, None, None, None, 2, None, None, None, 6],
        [None, 6, None, None, None, None, 2, 8, None],
        [None, None, None, 4, 1, 9, None, None, 5],
        [None, None, None, None, 8, None, None, 7, 9]
    ]
    sudoku.set_state(initial_state)
    print("\n      Initial State      ")
    print(sudoku)
    if sudoku.solve(True):
        print("\033[F"*2)
        print("       Solved  State      ")
        print(sudoku)
    else:
        print("This sudoku has no solution")
        print("\n" * 10)

if __name__ == "__main__":
    main()
