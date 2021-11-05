import random

import cv2
import numpy as np


class ImageToMap:
    def __init__(self, image_source: cv2.Mat):
        self.src = image_source
        self.src = cv2.bitwise_not(self.src)

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
        self.factor = self.height_map / self.y_max
        self.width_map = int(round(self.factor * self.x_max))
        print("Best width map :", self.width_map)

    def img_to_segments(self):
        fld = cv2.ximgproc.createFastLineDetector(do_merge=False)
        kernel = np.ones((3, 3), np.uint8)
        img_erode = cv2.erode(self.src, kernel, iterations=2)

        self.lines = fld.detect(img_erode)
        result_img = fld.drawSegments(self.src, self.lines)
        cv2.imshow("result_img", result_img)

        only_lines_image = np.zeros((self.src.shape[0], self.src.shape[1], 3), dtype=np.uint8)

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
        ret, thresh = cv2.threshold(src=self.src, thresh=127, maxval=255, type=0)
        contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)

        contours_poly = []
        self.boxes = []

        for i, curve in enumerate(contours):
            approx_poly = cv2.approxPolyDP(curve=curve, epsilon=0.1, closed=True)
            box = cv2.boundingRect(approx_poly)
            # print("approx_poly.shape[0]", approx_poly.shape[0])
            # print("abs(cv2.contourArea(approx_poly))", abs(cv2.contourArea(approx_poly)))
            # print("cv2.isContourConvex(approx_poly)", cv2.isContourConvex(approx_poly))
            if approx_poly.shape[0] == 4 and abs(cv2.contourArea(approx_poly)) > 300 and cv2.isContourConvex(
                    approx_poly):
                # print("approx_poly", approx_poly)
                contours_poly.append(approx_poly)
                self.boxes.append(box)
                # print("box", box)

        only_boxes_image = np.zeros((thresh.shape[0], thresh.shape[1], 3), dtype=np.uint8)

        for i in range(len(contours_poly)):
            color = (random.randint(0, 256), random.randint(0, 256), random.randint(0, 256))
            cv2.drawContours(only_boxes_image, contours_poly, i, color)
            cv2.rectangle(img=only_boxes_image, rec=self.boxes[i], color=color, thickness=-1)

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
        f.write("from spg_overlay.normal_wall import NormalWall, NormalBox\n\n\n")

        f.write("# Dimension of the map : ({},{})\n".format(self.height_map, self.width_map))

        f.write("# Dimension factor : {}\n".format(self.factor))

        f.write("def add_boxes(playground):\n")

        for i, box in enumerate(self.boxes):
            x0 = int(round(self.factor * box[0]))
            y0 = int(round(self.factor * box[1]))
            width = int(round(self.factor * box[2]))
            height = int(round(self.factor * box[3]))

            f.write("    # box {}\n".format(i))
            f.write("    playground.add_element(NormalBox(up_left_point=({}, {}),\n".format(x0, y0))
            f.write("                                     width={}, height={}))\n".format(width, height))

        f.write("\n\n")
        f.write("def add_walls(playground):\n")

        for i, line in enumerate(self.lines):
            x0 = int(round(self.factor * line[0][0]))
            y0 = int(round(self.factor * line[0][1]))
            x1 = int(round(self.factor * line[0][2]))
            y1 = int(round(self.factor * line[0][3]))

            f.write("    # wall {}\n".format(i))
            f.write("    playground.add_element(NormalWall(start_point=({}, {}),\n".format(x0, y0))
            f.write("                                      end_point=({}, {})))\n".format(x1, y1))

        f.close()

        print("nombre de boxes =", len(self.boxes))
        print("nombre de lignes =", len(self.lines))


img = cv2.imread("/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/CIREX_MAP1_simpleWalls.png", 0)
image_to_map = ImageToMap(img)
image_to_map.launch()
