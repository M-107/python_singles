import numpy as np
from PIL import Image, ImageDraw

BLOCKS_HORIZONTAL = 20
BLOCKS_VERTICAL = 20
# land modifier 0 - only water, 100 - only land (apart from borders)
LAND_MODIFIER = 65
STYLE = 2

# water must be twice bigger than the corner blocks in both dimensions
BLOCK_WATER = Image.open(rf"blocks/{STYLE}/BLOCK_WATER.png")
BLOCK_SIZE = BLOCK_WATER.size[0]
# All land
BLOCK_CORNR = Image.open(rf"blocks/{STYLE}/BLOCK_CORNR.png")
# land on the right side
BLOCK_CRHAL = Image.open(rf"blocks/{STYLE}/BLOCK_CRHAL.png")
# land in bottom right corner
BLOCK_CRQUA = Image.open(rf"blocks/{STYLE}/BLOCK_CRQUA.png")
# Water in top left corner
BLOCK_CR3QA = Image.open(rf"blocks/{STYLE}/BLOCK_CR3QA.png")
# make array with random numbers of the block size
LAYOUT_BORDERLESS = np.random.rand(BLOCKS_VERTICAL - 2, BLOCKS_HORIZONTAL - 2)
# turn the nice 0-100 land modifier number into actually usable one
LAND_MODIF_REAL = (LAND_MODIFIER - 50) / 100
# edit the array with the just created usable land modifier number
LAYOUT_BORDERLESS += LAND_MODIF_REAL
# turn the random numbers into integers, either 1s or 0s in this case
LAYOUT_BORDERLESS = np.rint(LAYOUT_BORDERLESS)
# add water (0s) around the whole array
LAYOUT = np.pad(LAYOUT_BORDERLESS, [1])
# print(LAYOUT)
# Prepare an empty image of the desired size
WIDTH = int(BLOCKS_HORIZONTAL * BLOCK_SIZE)
HEIGHT = int(BLOCKS_VERTICAL * BLOCK_SIZE)


# Check the value of a specific int in the 2d array and the ones around it
# Decide what picture should be used in its place
def make_block(array, x, y, img):
    pos = (x * BLOCK_SIZE, y * BLOCK_SIZE)
    half_block = int(BLOCK_SIZE / 2)
    temp_img = Image.new("RGB", (BLOCK_SIZE, BLOCK_SIZE), (0, 255, 0))
    rect = ImageDraw.Draw(temp_img)
    rect.rectangle([(1, 1), (38, 38)], fill=(255, 0, 100))
    # Edges
    if array[y][x - 1] == 0:
        temp_img.paste(BLOCK_CRHAL, (0, 0))
        temp_img.paste(BLOCK_CRHAL, (0, half_block))
    if array[y + 1][x] == 0:
        temp_img.paste(BLOCK_CRHAL.rotate(90), (0, half_block))
        temp_img.paste(BLOCK_CRHAL.rotate(90), (half_block, half_block))
    if array[y][x + 1] == 0:
        temp_img.paste(BLOCK_CRHAL.rotate(180), (half_block, 0))
        temp_img.paste(BLOCK_CRHAL.rotate(180), (half_block, half_block))
    if array[y - 1][x] == 0:
        temp_img.paste(BLOCK_CRHAL.rotate(270), (0, 0))
        temp_img.paste(BLOCK_CRHAL.rotate(270), (half_block, 0))
    # Corners
    if array[y][x - 1] == 0 and array[y - 1][x] == 0:
        temp_img.paste(BLOCK_CRQUA, (0, 0))
    if array[y][x - 1] == 0 and array[y + 1][x] == 0:
        temp_img.paste(BLOCK_CRQUA.rotate(90), (0, half_block))
    if array[y][x + 1] == 0 and array[y + 1][x] == 0:
        temp_img.paste(BLOCK_CRQUA.rotate(180), (half_block, half_block))
    if array[y][x + 1] == 0 and array[y - 1][x] == 0:
        temp_img.paste(BLOCK_CRQUA.rotate(270), (half_block, 0))
    # Inner Corners
    if array[y - 1][x - 1] == 0 and array[y - 1][x] == 1 and array[y][x - 1] == 1:
        temp_img.paste(BLOCK_CR3QA, (0, 0))
    if array[y + 1][x - 1] == 0 and array[y + 1][x] == 1 and array[y][x - 1] == 1:
        temp_img.paste(BLOCK_CR3QA.rotate(90), (0, half_block))
    if array[y + 1][x + 1] == 0 and array[y + 1][x] == 1 and array[y][x + 1] == 1:
        temp_img.paste(BLOCK_CR3QA.rotate(180), (half_block, half_block))
    if array[y - 1][x + 1] == 0 and array[y - 1][x] == 1 and array[y][x + 1] == 1:
        temp_img.paste(BLOCK_CR3QA.rotate(270), (half_block, 0))
    # Inner Fills
    if array[y - 1][x - 1] == 1 and array[y][x - 1] == 1 and array[y - 1][x] == 1:
        temp_img.paste(BLOCK_CORNR, (0, 0))
    if array[y + 1][x - 1] == 1 and array[y][x - 1] == 1 and array[y + 1][x] == 1:
        temp_img.paste(BLOCK_CORNR, (0, half_block))
    if array[y + 1][x + 1] == 1 and array[y][x + 1] == 1 and array[y + 1][x] == 1:
        temp_img.paste(BLOCK_CORNR, (half_block, half_block))
    if array[y - 1][x + 1] == 1 and array[y][x + 1] == 1 and array[y - 1][x] == 1:
        temp_img.paste(BLOCK_CORNR, (half_block, 0))
    img.paste(temp_img, pos)


def main():
    img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    # Run through the array and fill the resulting image accordingly
    for y, i in enumerate(LAYOUT):
        for x, j in enumerate(i):
            print(
                f"Building block {(y*len(i))+(x+1):>5}/{BLOCKS_HORIZONTAL*BLOCKS_VERTICAL:<5}"
            )
            if j == 0:
                img.paste(BLOCK_WATER, (x * BLOCK_SIZE, y * BLOCK_SIZE))
            else:
                make_block(LAYOUT, x, y, img)

    img.show()
    # img.save('map.png', quality=95)


if __name__ == "__main__":
    main()
