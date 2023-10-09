import cv2
import numpy as np

from tools.progress_bar import print_progress_bar


def wall_width_correction(image_source: cv2.Mat) -> cv2.Mat:
    img = image_source.copy()
    rows, cols = img.shape
    # imgTarget = np.zeros((rows, cols), np.uint8)
    # print("image_source.shape", image_source.shape)
    # print("imgTarget.shape", imgTarget.shape)

    new_width = 9

    # line by line
    j_end = 0
    for i in range(rows):
        j_start = 0
        prev_value = 1
        # print("")
        for j in range(cols):
            print_progress_bar(index=i * cols + j, total=cols * rows - 1,
                               label="wall_width_correction : line by line processing")
            value = img[i, j]
            if value == 0 and prev_value == 255:
                j_start = j

            black_size = 0
            if value == 255 and prev_value == 0 and j_start != 0:
                j_end = j
                black_size = j_end - j_start

            prev_value = value

            if 0 < black_size < new_width:
                n_to_add = new_width - black_size
                n_to_add_front = int(n_to_add / 2)
                n_to_add_back = n_to_add - n_to_add_front
                j0 = max(0, j_start - n_to_add_front)
                j1 = min(cols, j_end + n_to_add_back)
                img[i, j0:j1] = 0
                prev_value = 0
                j_start = j0

            if new_width < black_size < 2 * new_width:
                n_to_rm = black_size - new_width
                n_to_rm_front = int(n_to_rm / 2)
                n_to_rm_back = n_to_rm - n_to_rm_front
                # print(black_size, n_to_rm, n_to_rm_front, n_to_rm_back)
                j0 = max(0, j_start + n_to_rm_front)
                j1 = min(cols, j_end - n_to_rm_back)
                img[i, j_start:j0] = 255
                img[i, j1:j_end] = 255

    # col by col
    print("")
    i_end = 0
    for j in range(cols):
        i_start = 0
        prev_value = 255
        # print("")
        for i in range(rows):
            print_progress_bar(index=i + j * rows, total=cols * rows - 1,
                               label="wall_width_correction : col by col processing")
            value = img[i, j]
            if value == 0 and prev_value == 255:
                i_start = i

            black_size = 0
            if value == 255 and prev_value == 0 and i_start != 0:
                i_end = i
                black_size = i_end - i_start

            prev_value = value

            if 0 < black_size < new_width:
                n_to_add = new_width - black_size
                n_to_add_front = int(n_to_add / 2)
                n_to_add_back = n_to_add - n_to_add_front
                i0 = max(0, i_start - n_to_add_front)
                i1 = min(rows, i_end + n_to_add_back)
                img[i0:i1, j] = 0
                prev_value = 0
                i_start = i0

            if new_width < black_size < 1.5 * new_width:
                n_to_rm = black_size - new_width
                n_to_rm_front = int(n_to_rm / 2)
                n_to_rm_back = n_to_rm - n_to_rm_front
                # print(black_size, n_to_rm, n_to_rm_front, n_to_rm_back)
                i0 = max(0, i_start + n_to_rm_front)
                i1 = min(rows, i_end - n_to_rm_back)
                img[i_start:i0, j] = 255
                img[i1:i_end, j] = 255

    print("")

    return img


def remove_white_patch(image_source: cv2.Mat) -> cv2.Mat:
    img = image_source.copy()
    rows, cols = img.shape

    patch_size_max = 10

    # line by line
    j_end = 0
    for i in range(rows):
        j_start = 0
        prev_value = 0
        # print("")
        white_size = 0
        for j in range(cols):
            print_progress_bar(index=i * cols + j, total=cols * rows - 1,
                               label="remove_white_patch : line by line processing")
            value = img[i, j]
            if value == 255 and prev_value == 0:
                j_start = j

            white_size = 0
            if value == 0 and prev_value == 255:
                j_end = j
                white_size = j_end - j_start

            prev_value = value

            if 0 < white_size < patch_size_max:
                img[i, j_start:j_end] = 0

        if prev_value == 255:
            white_size = cols - j_start

        if 0 < white_size < patch_size_max:
            img[i, j_start:cols] = 0

    # col by col
    print("")
    i_end = 0
    white_size = 0
    for j in range(cols):
        i_start = 0
        prev_value = 0
        # print("")
        for i in range(rows):
            print_progress_bar(index=i + j * rows, total=cols * rows - 1,
                               label="remove_white_patch : col by col processing")
            value = img[i, j]
            if value == 255 and prev_value == 0:
                i_start = i

            white_size = 0
            if value == 0 and prev_value == 255:
                i_end = i
                white_size = i_end - i_start

            prev_value = value

            if 0 < white_size < patch_size_max:
                img[i_start:i_end, j] = 0

        if prev_value == 255:
            white_size = rows - i_start

        if 0 < white_size < patch_size_max:
            img[i_start:rows, j] = 0

    print("")

    return img


def remove_black_patch(image_source: cv2.Mat) -> cv2.Mat:
    img = image_source.copy()
    rows, cols = img.shape

    patch_size_max = 4

    # line by line
    j_end = 0
    for i in range(rows):
        j_start = 0
        prev_value = 255
        # print("")
        black_size = 0
        for j in range(cols):
            print_progress_bar(index=i * cols + j, total=cols * rows - 1,
                               label="remove_black_patch : line by line processing")
            value = img[i, j]
            if value == 0 and prev_value == 255:
                j_start = j

            black_size = 0
            if value == 255 and prev_value == 0:
                j_end = j
                black_size = j_end - j_start

            prev_value = value

            if 0 < black_size < patch_size_max:
                img[i, j_start:j_end] = 255

        if prev_value == 0:
            black_size = cols - j_start

        if 0 < black_size < patch_size_max:
            img[i, j_start:cols] = 255

    # col by col
    print("")
    i_end = 0
    black_size = 0
    for j in range(cols):
        i_start = 0
        prev_value = 0
        # print("")
        for i in range(rows):
            print_progress_bar(index=i + j * rows, total=cols * rows - 1,
                               label="remove_black_patch : col by col processing")
            value = img[i, j]
            if value == 0 and prev_value == 255:
                i_start = i

            black_size = 0
            if value == 255 and prev_value == 0:
                i_end = i
                black_size = i_end - i_start

            prev_value = value

            if 0 < black_size < patch_size_max:
                img[i_start:i_end, j] = 255

        if prev_value == 0:
            black_size = rows - i_start

        if 0 < black_size < patch_size_max:
            img[i_start:rows, j] = 255

    print("")

    return img


def remove_noise(image_source: cv2.Mat) -> cv2.Mat:
    # Remove white pixels noise
    size_kernel = 10
    kernel = np.ones((size_kernel, size_kernel), np.uint8)
    img_opening = cv2.morphologyEx(image_source, cv2.MORPH_OPEN, kernel)
    # cv2.imshow("img_opening", img_opening)

    # Remove black pixels noise
    size_kernel_1 = 21
    size_kernel_2 = 5
    kernel = np.ones((size_kernel_2, size_kernel_1), np.uint8)
    img_closing_horiz = cv2.morphologyEx(img_opening, cv2.MORPH_CLOSE, kernel, iterations=1)
    # cv2.imshow("img_closing_horiz", img_closing_horiz)

    kernel = np.ones((size_kernel_1, size_kernel_2), np.uint8)
    img_closing_verti = cv2.morphologyEx(img_opening, cv2.MORPH_CLOSE, kernel, iterations=1)
    # cv2.imshow("img_closing_verti", img_closing_verti)

    img_closing = cv2.min(img_closing_horiz, img_closing_verti)

    return img_closing


def image_cleaning(image_source: cv2.Mat) -> cv2.Mat:
    img_clean = wall_width_correction(image_source)
    return img_clean


img_path = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/map_medium_01_color.png"
# img_path = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/map_complete_map_2.png"
print("image path : {}".format(img_path))
img_source = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
cv2.imshow("img_source", img_source)

img_clean1 = remove_noise(img_source)
cv2.imshow("img_clean1", img_clean1)

img_clean2 = image_cleaning(img_clean1)
cv2.imshow("img_clean2", img_clean2)

img_clean3 = remove_noise(img_clean2)
cv2.imshow("img_clean3", img_clean3)

img_clean4 = remove_white_patch(img_clean3)
cv2.imshow("img_clean4", img_clean4)

cv2.imwrite('/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/map_clean.png', img_clean4)

cv2.waitKey(0)
