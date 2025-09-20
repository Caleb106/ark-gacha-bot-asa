import source.utility.screen
import cv2 
import numpy as np

'''takes a picture of the region of the bottom console window outputs the mean value of the whole bar '''
def output_mean_colour():
    if source.utility.screen.screen_resolution == 1440:
        roi = source.utility.screen.get_screen_roi(0,1419,2560,2)
    else:
        roi = source.utility.screen.get_screen_roi(0,1059,1920,2)
    gray_roi = cv2.cvtColor(roi(), cv2.COLOR_BGR2GRAY)
    average = np.mean(gray_roi)
    print(f"the average console colour was : {average} go to console.json and set +and - 5 from this in the respected section IE upperbound = average+5 ")


if __name__ == "__main__":
    output_mean_colour()
    input(f"")