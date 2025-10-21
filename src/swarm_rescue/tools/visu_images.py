import cv2

def show_image(img_path: str) -> None:
    """
    Loads and displays a grayscale image from the given path.

    Args:
        img_path (str): Path to the image file.
    """
    img1 = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    cv2.imshow("img1", img1)
    cv2.waitKey(0)

def main():
    img_path1 = ("/home/battesti/projetCompetDronesDGA/"
                 "private-swarm-rescue/map_data/"
                 "map_medium_01_color.png")
    show_image(img_path1)

if __name__ == '__main__':
    main()