import cv2

img_path1 = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue-alixia/map_data/complete_map_2.png"
img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
cv2.imshow("img1", img1)

img_path2 = "/home/battesti/projetCompetDronesDGA/private-swarm-rescue-alixia/map_data/complete_map_2_clean.png"
img2 = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE)
cv2.imshow("img2", img2)

cv2.waitKey(0)
