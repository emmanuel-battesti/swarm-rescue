import random

# from cv2 import cv2 as cv2
import cv2
import numpy as np


class ImageToMap:
    def __init__(self, image_source: cv2.Mat, auto_resized: bool = True):
        self._img_src = image_source
        cv2.imshow("image_source", image_source)
        self._img_src = cv2.bitwise_not(self._img_src)
        self._auto_resized = auto_resized

        self.x_max = -1
        self.y_max = -1

        self.height_map = 750
        self.width_map = 0
        self.factor = 0

        self.lines = []
        self.boxes = []

    def launch(self):
        self.img_to_segments()
        self.img_to_boxes()
        self.compute_dim()
        self.write_lines_and_boxes()

    def compute_dim(self):
        self.height_map = 750

        print("original dim map : ({}, {})".format(self._img_src.shape[1], self._img_src.shape[0]))
        print("self.x_max = {}, self.y_max = {}".format(self.x_max, self.y_max))
        print("auto_resized = {}".format(self._auto_resized))

        best_factor = self.height_map / self.y_max
        if not self._auto_resized:
            best_factor = 1.0
        best_width_map = int(round(best_factor * self.x_max))
        print("Best dim map : ({}, {}) with factor {}".format(best_width_map, self.height_map, best_factor))

        self.factor = self.height_map / self._img_src.shape[0]
        if not self._auto_resized:
            self.factor = 1.0
            self.height_map = self._img_src.shape[0]
        self.width_map = int(round(self.factor * self._img_src.shape[1]))
        print("Used dim map : ({}, {}) with factor {}".format(self.width_map, self.height_map, self.factor))

    def img_to_segments(self):
        fld = cv2.ximgproc.createFastLineDetector(do_merge=True)
        size_kernel = 9
        kernel = np.ones((size_kernel, size_kernel), np.uint8)
        img_erode = cv2.erode(self._img_src, kernel, iterations=1)
        cv2.imshow("img_erode", img_erode)

        self.lines = fld.detect(img_erode)
        result_img = fld.drawSegments(self._img_src, self.lines)
        cv2.imshow("result_img", result_img)

        only_lines_image = np.zeros((self._img_src.shape[0], self._img_src.shape[1], 3), dtype=np.uint8)

        for line in self.lines:
            x0 = int(round(line[0][0]))
            y0 = int(round(line[0][1]))
            x1 = int(round(line[0][2]))
            y1 = int(round(line[0][3]))
            cv2.line(only_lines_image, (x0, y0), (x1, y1), (0, 0, 255), 1, cv2.LINE_4)

        # Compute min and max
        for line in self.lines:
            x0 = int(round(line[0][0]))
            x1 = int(round(line[0][2]))
            self.x_max = max(x0, x1, self.x_max)

            y0 = int(round(line[0][1]))
            y1 = int(round(line[0][3]))
            self.y_max = max(y0, y1, self.y_max)

        cv2.imshow("only_lines_image", only_lines_image)

        cv2.waitKey(0)

    def img_to_boxes(self):
        size_kernel = 50
        kernel = np.ones((size_kernel, size_kernel), np.uint8)
        img_box = cv2.morphologyEx(self._img_src, cv2.MORPH_OPEN, kernel)
        cv2.imshow("img_box", img_box)
        thresh_value, thresh_img = cv2.threshold(src=img_box, thresh=127, maxval=255, type=0)
        contours, hierarchy = cv2.findContours(image=thresh_img, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
        cv2.imshow("thresh_img_box", thresh_img)

        contours_poly = []
        self.boxes = []

        for i, curve in enumerate(contours):
            perimeter = cv2.arcLength(curve=curve, closed=True)
            approx_poly = cv2.approxPolyDP(curve=curve, epsilon=0.015 * perimeter, closed=True)
            box = cv2.boundingRect(approx_poly)
            # print("approx_poly.shape[0]", approx_poly.shape[0])
            # print("abs(cv2.contourArea(approx_poly))", abs(cv2.contourArea(approx_poly)))
            # print("cv2.isContourConvex(approx_poly)", cv2.isContourConvex(approx_poly))

            # remove huge boxes
            # if box[2] > 0.7 * self._img_src.shape[1] and box[3] > 0.7 * self._img_src.shape[0]:
            # print("**********")
            # print("width box", box[2])
            # print("height box", box[3])
            # print("width img", self._img_src.shape[1])
            # print("height img", self._img_src.shape[0])
            # print("")
            # continue

            if approx_poly.shape[0] == 4 and abs(cv2.contourArea(approx_poly)) > 300 and cv2.isContourConvex(
                    approx_poly):
                # print("approx_poly", approx_poly)
                contours_poly.append(approx_poly)
                self.boxes.append(box)
                # print("box", box)

        only_boxes_image = np.zeros((thresh_img.shape[0], thresh_img.shape[1], 3), dtype=np.uint8)

        for i in range(len(contours_poly)):
            color = (random.randint(0, 256), random.randint(0, 256), random.randint(0, 256))
            cv2.drawContours(only_boxes_image, contours_poly, i, color)
            # x, y, w, h = self.boxes[i]
            # cv2.rectangle(img=only_boxes_image, pt1=(x, y), pt2=(x + w, y + h), color=color, thickness=-1)

        # Compute min and max
        for box in self.boxes:
            x0 = int(round(box[0]))
            x1 = int(round(box[0] + box[2]))
            self.x_max = max(x0, x1, self.x_max)

            y0 = int(round(box[1]))
            y1 = int(round(box[1] + box[3]))
            self.y_max = max(y0, y1, self.y_max)

        cv2.imshow("only_boxes_image", only_boxes_image)

        cv2.waitKey(0)

    def write_lines_and_boxes(self):
        f = open("generated_code.py", "w")

        f.write("\"\"\"\n")
        f.write("This file was generated by the tool 'image_to_map.py' in the directory tools.\n")
        f.write(
            "This tool permits to create this kind of file by providing it an image of the map we want to create.\n")
        f.write("\"\"\"\n\n")

        f.write("from spg_overlay.normal_wall import NormalWall, NormalBox\n\n\n")

        f.write("# Dimension of the map : ({}, {})\n".format(self.width_map, self.height_map))

        f.write("# Dimension factor : {}\n".format(self.factor))

        f.write("def add_boxes(playground):\n")

        if len(self.boxes) != 0:
            for i, box in enumerate(self.boxes):
                x0 = int(round(self.factor * box[0]))
                y0 = int(round(self.factor * box[1]))
                width = int(round(self.factor * box[2]))
                height = int(round(self.factor * box[3]))

                xw = x0 - self.width_map / 2
                yw = -y0 + self.height_map / 2

                f.write("    # box {}\n".format(i))
                f.write("    box = NormalBox(up_left_point=({}, {}),\n".format(xw, yw))
                f.write("                    width={}, height={})\n".format(width, height))
                f.write("    playground.add(box, box.wall_coordinates)\n\n")
        else:
            f.write("    pass\n\n")

        f.write("\n")
        f.write("def add_walls(playground):\n")

        # orient :
        #   horizontal = 0
        #   vertical = 1
        #   oblique = 2
        if len(self.lines) != 0:
            for i, line in enumerate(self.lines):
                x0 = int(round(self.factor * line[0][0]))
                y0 = int(round(self.factor * line[0][1]))
                x1 = int(round(self.factor * line[0][2]))
                y1 = int(round(self.factor * line[0][3]))

                orient = 2

                if y0 == y1:
                    # horizontal
                    orient = 0

                if x0 == x1:
                    # vertical
                    orient = 1

                # Correct orientation
                if orient == 0 and x0 > x1:  # horizontal
                    x0, x1 = x1, x0  # swap

                if orient == 1 and y0 > y1:  # vertical
                    y0, y1 = y1, y0  # swap

                if orient == 2 and x0 > x1:  # oblique
                    x0, x1 = x1, x0  # swap
                    y0, y1 = y1, y0  # swap

                # Correct size
                if orient == 0:
                    x0 -= 2
                    x1 += 2

                if orient == 1:
                    y0 -= 2
                    y1 += 2

                if orient == 2:
                    x0 -= 2
                    x1 += 2
                    if y1 > y0:  # oblique
                        y0 -= 2
                        y1 += 2
                    else:
                        y1 -= 2
                        y0 += 2

                if orient == 0:
                    f.write("    # horizontal wall {}\n".format(i))
                elif orient == 1:
                    f.write("    # vertical wall {}\n".format(i))
                else:
                    f.write("    # oblique wall {}\n".format(i))

                xw0 = x0 - self.width_map / 2
                yw0 = -y0 + self.height_map / 2

                xw1 = x1 - self.width_map / 2
                yw1 = -y1 + self.height_map / 2

                f.write("    wall = NormalWall(pos_start=({}, {}),\n".format(xw0, yw0))
                f.write("                      pos_end=({}, {}))\n".format(xw1, yw1))
                f.write("    playground.add(wall, wall.wall_coordinates)\n\n")
        else:
            f.write("    pass\n\n")

        f.close()

        print("nombre de boxes =", len(self.boxes))
        print("nombre de lignes =", len(self.lines))


# img_path = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue-alixia/map_data/complete_map_1.png"
img_path = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue-alixia/map_data/intermediate_eval_1.png"
should_auto_resized = False
img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
image_to_map = ImageToMap(image_source=img, auto_resized=should_auto_resized)
image_to_map.launch()
