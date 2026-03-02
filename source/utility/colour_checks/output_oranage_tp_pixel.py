import source.utility.screen
import cv2 

'''these values are for a screen of 2560x1440'''
orange = {
    "x":705,
    "y":290
}

def get_orange_pixel():
    x,y = orange["x"],orange["y"]
    if source.utility.screen.screen_resolution == 1080:
        x *= 0.75
        y *= 0.75
    roi = source.utility.screen.get_screen_roi(int(x),int(y),1,1)
    hsv = cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
    print(f"{hsv[0, 0]} -> these colours should be put into xxxxxx location in xxxx file") 
    return hsv[0, 0]


if __name__ == "__main__":
    get_orange_pixel()
    input(f"")