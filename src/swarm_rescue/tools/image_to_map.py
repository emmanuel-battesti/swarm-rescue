import random

import cv2
import numpy as np


class ImageToMap:
    def __init__(self, image_source: cv2.Mat, auto_resized: bool = True):
        self._img_src = image_source
        cv2.imshow("image_source", self._img_src)
        cv2.waitKey(0)

        img_hsv = cv2.cvtColor(self._img_src, cv2.COLOR_BGR2HSV)
        # lower bound and upper bound for all color except black
        lower_bound = (0, 0, 100)
        upper_bound = (180, 255, 255)
        # find the colors within the boundaries
        mask_walls = cv2.inRange(img_hsv, lower_bound, upper_bound)
        self._img_src_walls = cv2.bitwise_not(mask_walls)
        # cv2.imshow("mask_walls", self._img_src_bw)
        # cv2.waitKey(0)

        self._auto_resized = auto_resized

        self.height_map = 750
        self.width_map = 0
        self.factor = 1.0

        self.lines = []
        self.boxes = []

    def launch(self):
        self.compute_dim()
        self.img_to_segments()
        self.img_to_boxes()
        self.write_lines_and_boxes()
        self.detect_people()
        self.detect_rescue_center()

    def detect_people(self):
        # convert to hsv colorspace
        img_hsv = cv2.cvtColor(self._img_src, cv2.COLOR_BGR2HSV)

        # lower bound and upper bound for Green color
        lower_bound = (22, 93, 0)
        upper_bound = (45, 255, 255)
        # find the colors within the boundaries
        mask_people = cv2.inRange(img_hsv, lower_bound, upper_bound)

        # define kernel size
        kernel = np.ones((7, 7), np.uint8)

        # Remove unnecessary noise from mask
        mask_people = cv2.morphologyEx(mask_people, cv2.MORPH_CLOSE, kernel)
        mask_people = cv2.morphologyEx(mask_people, cv2.MORPH_OPEN, kernel)

        # Setup SimpleBlobDetector parameters.
        params = cv2.SimpleBlobDetector_Params()
        # Change thresholds
        params.filterByArea = True
        params.maxArea = 2000
        # Convexity = Area of the Blob / Area of its convex hull (max = 1 for convex shape)
        params.filterByConvexity = True
        params.minConvexity = 0.75
        # Circularity = 4 pi * Area / (perimeter)²  (max = 1 for circle)
        params.filterByCircularity = True
        params.minCircularity = 0.75

        # Set up the detector with default parameters.
        detector = cv2.SimpleBlobDetector_create(params)

        scaled_mask_people = 255 - (mask_people.astype(np.float32) * 255 / np.max(mask_people)).astype(np.uint8)
        # Detect blobs.
        keypoints = detector.detect(scaled_mask_people)

        print("Code to add in map_xxx.py:")
        txt_people_position = "\tself._wounded_persons_pos = ["
        for i, keyPoint in enumerate(keypoints):
            x = self.factor * keyPoint.pt[0] - self.width_map / 2
            y = self.height_map / 2 - self.factor * keyPoint.pt[1]
            txt_people_position += "({0:.0f},{1:.0f})".format(x, y)
            if i < len(keypoints) - 1:
                txt_people_position += ", "
        txt_people_position += "]"
        print(txt_people_position)

        # # Draw detected blobs as red circles.
        # # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
        # mask_people_rbg = cv2.cvtColor(mask_people, cv2.COLOR_GRAY2RGB)
        # im_with_keypoints = cv2.drawKeypoints(mask_people_rbg, keypoints, np.array([]), (0, 0, 255),
        #                                       cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        # Show keypoints
        # cv2.imshow("Keypoints", im_with_keypoints)
        # cv2.waitKey(0)

    def detect_rescue_center(self):
        # convert to hsv colorspace
        img_hsv = cv2.cvtColor(self._img_src, cv2.COLOR_BGR2HSV)

        # lower boundary RED color range values; Hue (0 - 10)
        lower1 = np.array([0, 100, 20])
        upper1 = np.array([10, 255, 255])

        # upper boundary RED color range values; Hue (160 - 180)
        lower2 = np.array([160, 100, 20])
        upper2 = np.array([179, 255, 255])

        lower_mask = cv2.inRange(img_hsv, lower1, upper1)
        upper_mask = cv2.inRange(img_hsv, lower2, upper2)

        mask_rescue_center = lower_mask + upper_mask

        # define kernel size
        kernel = np.ones((7, 7), np.uint8)

        # Remove unnecessary noise from mask
        mask_rescue_center = cv2.morphologyEx(mask_rescue_center, cv2.MORPH_CLOSE, kernel)
        mask_rescue_center = cv2.morphologyEx(mask_rescue_center, cv2.MORPH_OPEN, kernel)

        # find the contours
        contours, _ = cv2.findContours(mask_rescue_center, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # take the first contour
        cnt = contours[0]

        # compute the bounding rectangle of the contour
        x_rec, y_rec, w_rec, h_rec = cv2.boundingRect(cnt)
        # x_rec -= 2
        # y_rec -= 2
        # w_rec += 1
        # h_rec += 1
        # print(x_rec, y_rec, w_rec, h_rec)

        # draw contour
        mask_rescue_center_rbg = cv2.cvtColor(mask_rescue_center, cv2.COLOR_GRAY2RGB)
        mask_rescue_center_rbg = cv2.drawContours(mask_rescue_center_rbg, [cnt], 0, (0, 255, 255), 2)

        # draw the bounding rectangle
        mask_rescue_center_rbg = cv2.rectangle(mask_rescue_center_rbg, (x_rec, y_rec), (x_rec + w_rec, y_rec + h_rec),
                                               (0, 255, 0), 2)

        # display the image with bounding rectangle drawn on it
        cv2.imshow("Bounding Rectangle", mask_rescue_center_rbg)
        cv2.waitKey(0)

        # self._rescue_center = RescueCenter(size=(90, 170))
        # self._rescue_center_pos = ((-505, -285), 0)

        print("Code to add in map_xxx.py:")
        x_rec *= self.factor
        y_rec *= self.factor
        h_rec *= self.factor
        w_rec *= self.factor
        x = x_rec + w_rec * 0.5 - self.width_map * 0.5
        y = self.height_map * 0.5 - (y_rec + h_rec * 0.5)
        txt_rescue1 = "\tself._rescue_center = RescueCenter(size=({0:.0f},{1:.0f}))".format(w_rec, h_rec)
        txt_rescue2 = "\tself._rescue_center_pos = (({0:.0f},{1:.0f}), 0)".format(x, y)
        print(txt_rescue1)
        print(txt_rescue2)

    def compute_dim(self):
        self.height_map = 750

        print("original dim map : ({}, {})".format(self._img_src_walls.shape[1], self._img_src_walls.shape[0]))
        print("auto_resized = {}".format(self._auto_resized))

        self.factor = self.height_map / self._img_src_walls.shape[0]
        if not self._auto_resized:
            self.factor = 1.0
            self.height_map = self._img_src_walls.shape[0]
        self.width_map = int(round(self.factor * self._img_src_walls.shape[1]))
        print("Used dim map : ({}, {}) with factor {}".format(self.width_map, self.height_map, self.factor))

        print("Code to add in map_xxx.py:")
        print("\tself._size_area = ({0:.0f},{1:.0f})".format(self.width_map, self.height_map))

    def img_to_segments(self):
        fld = cv2.ximgproc.createFastLineDetector(do_merge=True)
        size_kernel = 9
        kernel = np.ones((size_kernel, size_kernel), np.uint8)
        img_erode = cv2.erode(self._img_src_walls, kernel, iterations=1)
        cv2.imshow("img_erode", img_erode)

        self.lines = fld.detect(img_erode)
        result_img = fld.drawSegments(self._img_src_walls, self.lines)
        cv2.imshow("result_img", result_img)

        only_lines_image = np.zeros((self._img_src_walls.shape[0], self._img_src_walls.shape[1], 3), dtype=np.uint8)

        for line in self.lines:
            x0 = int(round(line[0][0]))
            y0 = int(round(line[0][1]))
            x1 = int(round(line[0][2]))
            y1 = int(round(line[0][3]))
            cv2.line(only_lines_image, (x0, y0), (x1, y1), (0, 0, 255), 1, cv2.LINE_4)

        # Compute min and max
        # for line in self.lines:
        #     x0 = int(round(line[0][0]))
        #     x1 = int(round(line[0][2]))
        #     self.x_max = max(x0, x1, self.x_max)
        #
        #     y0 = int(round(line[0][1]))
        #     y1 = int(round(line[0][3]))
        #     self.y_max = max(y0, y1, self.y_max)

        cv2.imshow("only_lines_image", only_lines_image)

        cv2.waitKey(0)

    def img_to_boxes(self):
        size_kernel = 50
        kernel = np.ones((size_kernel, size_kernel), np.uint8)
        img_box = cv2.morphologyEx(self._img_src_walls, cv2.MORPH_OPEN, kernel)
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
        # for box in self.boxes:
        #     x0 = int(round(box[0]))
        #     x1 = int(round(box[0] + box[2]))
        #     self.x_max = max(x0, x1, self.x_max)
        #
        #     y0 = int(round(box[1]))
        #     y1 = int(round(box[1] + box[3]))
        #     self.y_max = max(y0, y1, self.y_max)

        cv2.imshow("only_boxes_image", only_boxes_image)

        cv2.waitKey(0)

    def write_lines_and_boxes(self):
        f = open("generated_code.py", "w")

        f.write("\"\"\"\n")
        f.write("This file was generated by the tool 'image_to_map.py' in the directory tools.\n")
        f.write(
            "This tool permits to create this kind of file by providing it an image of the map we want to create.\n")
        f.write("\"\"\"\n\n")

        f.write("from spg_overlay.entities.normal_wall import NormalWall, NormalBox\n\n\n")

        f.write("# Dimension of the map : ({}, {})\n".format(self.width_map, self.height_map))

        f.write("# Dimension factor : {}\n".format(self.factor))

        f.write("def add_boxes(playground):\n")

        if len(self.boxes) != 0:
            for i, box in enumerate(self.boxes):
                x0 = self.factor * box[0]
                y0 = self.factor * box[1]
                width = self.factor * box[2]
                height = self.factor * box[3]

                xw = int(round(x0 - self.width_map / 2))
                yw = int(round(-y0 + self.height_map / 2))
                width_w = int(round(width))
                height_w = int(round(height))

                f.write("    # box {}\n".format(i))
                f.write("    box = NormalBox(up_left_point=({}, {}),\n".format(xw, yw))
                f.write("                    width={}, height={})\n".format(width_w, height_w))
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
                x0 = self.factor * line[0][0]
                y0 = self.factor * line[0][1]
                x1 = self.factor * line[0][2]
                y1 = self.factor * line[0][3]

                orient = 2

                if abs(y0 - y1) < 2.0:
                    # horizontal
                    orient = 0
                    y0 = (y0 + y1) / 2
                    y1 = y0

                if abs(x0 - x1) < 2.0:
                    # vertical
                    orient = 1
                    x0 = (x0 + x1) / 2
                    x1 = x0

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

                xw0 = int(round(x0 - self.width_map / 2))
                yw0 = int(round(-y0 + self.height_map / 2))

                xw1 = int(round(x1 - self.width_map / 2))
                yw1 = int(round(-y1 + self.height_map / 2))

                f.write("    wall = NormalWall(pos_start=({}, {}),\n".format(xw0, yw0))
                f.write("                      pos_end=({}, {}))\n".format(xw1, yw1))
                f.write("    playground.add(wall, wall.wall_coordinates)\n\n")
        else:
            f.write("    pass\n\n")

        f.close()

        print("nombre de boxes =", len(self.boxes))
        print("nombre de lignes =", len(self.lines))


# img_path = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/map_complete_map_2.png"
img_path = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/map_medium_02_color.png"
should_auto_resized = False
# img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
img = cv2.imread(img_path)
image_to_map = ImageToMap(image_source=img, auto_resized=should_auto_resized)
image_to_map.launch()
