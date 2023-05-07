def get_xy_asc(path: str):
    lines = []
    with open(path, "r") as f:
        for line in f:
            l_split = line.split()
            lines.append(l_split)
    lines = lines[:-1]
    for j in lines:
        number = float(j[0][:-6])
        exponent = int(j[0][-1])
        new_number = number * 10**exponent
        j[0] = new_number
        j[1] = int(j[1])
    x = [round(x[0], 3) for x in lines]
    y = [x[1] for x in lines]
    return x, y


def get_xy_itx(path: str):
    lines = []
    with open(path, "r") as f:
        for line in f:
            lines.append(line)
    lines = lines[3:-13]
    x_raw = [i.split(" ")[0] for i in lines]
    y_raw = [i.split(" ")[1] for i in lines]
    x = []
    y = []
    for j in range(0, len(x_raw)):
        x_number = float(x_raw[j][:8])
        x_exponent = int(x_raw[j][-1])
        y_number = float(y_raw[j][:8])
        y_exponent = int(y_raw[j][-1])
        x_new_format = round(x_number * 10**x_exponent, 2)
        y_new_format = round(y_number * 10**y_exponent, 10)
        x.append(x_new_format)
        y.append(y_new_format)
    return x, y


def get_xy_scn(path: str):
    x = []
    y = []
    with open(path, "r") as f:
        for line in f:
            if len(line.split()) == 2:
                one_x = float(line.split()[0])
                one_y = float(line.split()[1])
                x.append(one_x)
                y.append(one_y)
    return x, y


def get_xy_xrdml(path: str):
    lines = []
    with open(path, "r") as f:
        for line in f:
            lines.append(line)
    for num, line in enumerate(lines):
        if '<positions axis="2Theta" unit="deg">' in line:
            x_start_line = lines[num+1]
            x_start = float(x_start_line[x_start_line.find(">") + 1:x_start_line.find("</")])
            x_end_line = lines[num+2]
            x_end = float(x_end_line[x_end_line.find(">") + 1:x_end_line.find("</")])
        if '<intensities unit="counts">' in line:
            y_line = lines[num]
            intensities_string = y_line.split('<intensities unit="counts">')[1].split("</intensities>")[0]
            y = [int(x) for x in intensities_string.split()]
    x = [x_start + i * (x_end - x_start) / (len(y) - 1) for i in range(len(y))]
    return x, y
