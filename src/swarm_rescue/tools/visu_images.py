import cv2

img_path1 = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue/map_data/map_medium_01_color.png"
img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
cv2.imshow("img1", img1)

cv2.waitKey(0)
