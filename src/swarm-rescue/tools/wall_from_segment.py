import cv2
import numpy as np

img = cv2.imread("/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/CIREX_MAP1_simpleWalls.png", 0)

img = cv2.bitwise_not(img)
fld = cv2.ximgproc.createFastLineDetector(do_merge=False)
kernel = np.ones((3, 3), np.uint8)
img_erode = cv2.erode(img, kernel, iterations=2)

lines = fld.detect(img_erode)
result_img = fld.drawSegments(img, lines)

# test_image = np.zeros(img.shape, dtype=np.uint8)
test_image = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)

for line in lines:
    x0 = int(round(line[0][0]))
    y0 = int(round(line[0][1]))
    x1 = int(round(line[0][2]))
    y1 = int(round(line[0][3]))
    cv2.line(test_image, (x0, y0), (x1, y1), (0, 0, 255), 1, cv2.LINE_4)

# Compute min and max
x_max = -1
y_max = -1
for line in lines:
    x0 = int(round(line[0][0]))
    x1 = int(round(line[0][2]))
    x_max = max(x0, x1, x_max)

    y0 = int(round(line[0][1]))
    y1 = int(round(line[0][3]))
    y_max = max(y0, y1, y_max)

height_map = 750
factor = height_map / y_max
width_map = int(round(factor * x_max))
print("Best width map :", width_map)

f = open("map_from_img.py", "w")
f.write("from spg_overlay.normal_wall import NormalWall\n\n\n")
f.write("# Dimension of the map : ({},{})\n".format(height_map, width_map))
f.write("# Dimension factor : {}\n".format(factor))
f.write("def add_walls(playground):\n")

for i, line in enumerate(lines):
    x0 = int(round(factor * line[0][0]))
    y0 = int(round(factor * line[0][1]))
    x1 = int(round(factor * line[0][2]))
    y1 = int(round(factor * line[0][3]))

    f.write("    # wall {}\n".format(i))
    f.write("    playground.add_element(NormalWall(start_point=({}, {}),\n".format(x0, y0))
    f.write("                                      end_point=({}, {})))\n".format(x1, y1))
f.close()

print("nombre de lignes=", len(lines))

# cv2.imshow("Normal", img)
cv2.imshow("test_image", test_image)
# cv2.imshow("Result", result_img)

cv2.waitKey(0)
