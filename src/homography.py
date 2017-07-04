import cv2
import numpy as np


def register_by_homography(ref_img_name, target_img_name, ref_points, target_points):
    """ 
    Calculate Homography Matrix using corresponding points.After that a transform image using its matrix.
    :param ref_img_name: 
    :param target_img_name: 
    :param ref_points: 
    :param target_points: 
    :return: 
    """
    # load alpha channel.
    ref_img = cv2.imread(ref_img_name, -1)
    target_img = cv2.imread(target_img_name, -1)
    ref_points = np.array(ref_points)
    target_points = np.array(target_points)
    print(ref_img.shape)
    print(target_img.shape)

    h, status = cv2.findHomography(ref_points, target_points)
    # Warp source image to destination based on homography.
    out_img = cv2.warpPerspective(ref_img, h, (target_img.shape[1], target_img.shape[0]))
    for y in range(out_img.shape[0]):
        for x in range(out_img.shape[1]):
            # Ignore Alpha channel.
            if out_img[y][x][3] == 0:
                continue
            else:
                target_img[y][x][0] = out_img[y][x][0]
                target_img[y][x][1] = out_img[y][x][1]
                target_img[y][x][2] = out_img[y][x][2]

    file_name = "target.png"
    cv2.imwrite(file_name, target_img)
    return target_img, file_name


