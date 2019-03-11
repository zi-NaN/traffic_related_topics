import cv2
import argparse

def carDetector(classifier='cas1.xml', image='008.bmp'):

    car_cascade = cv2.CascadeClassifier(classifier)
    img = cv2.imread(image, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect cars
    cars = car_cascade.detectMultiScale(gray, 1.1, 1)

    max_x = 0
    max_y = 0
    max_w = 0
    max_h = 0
    max_area = 0

    # Draw border
    for (x, y, w, h) in cars:
        if w * h > max_area:
            max_area = w * h
            max_x = x
            max_y = y
            max_w = w
            max_h = h

    cv2.rectangle(img, (max_x,max_y), (max_x+max_w,max_y+max_h), (0,0,255), 2)
    cv2.imwrite('output.bmp', img)



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='input image for car detection')
    parser.add_argument('--classifier', help='saved harr car classifier')
    args = vars(parser.parse_args())

    if 'input' in args and 'classifier' in args:
        carDetector(parser['classifier'], parser['input'])
    elif 'input' in args:
        carDetector(image=parser['input'])
    elif 'classifier' in args:
        carDetector(parser['classifier'])
    else:
        carDetector()

    