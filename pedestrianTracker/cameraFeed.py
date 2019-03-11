'''
Author:          ZHAO Zinan
Written:         2018-07-04
Last Updated:    03-Oct-2018

as the main function of the whole pedestrian tracking program, track people, cal the least remaining time
'''

import configparser
import datetime
import time
import sys
import cv2
import os
import imutils
from imutils.object_detection import non_max_suppression
import json
import math
import numpy as np


sys.path.append(os.path.join(os.getcwd(), 'pedestrianTracker'))
from peopleTracker import PeopleTracker

'''
a class that track people in camera or sample video and cal the least remaining time to the 
other edge

...

Attributes
------------------
_frame_width : int
_frame_height: int

Methods
------------------
change_running_state()
go_config(config_path=None)
go()
process(frame)
crop_and_resize(frame)
apply_mog(frame)
render_hud(frame)
handle_the_people(frame)
''' 
class CameraFeed:
    # frame dimension (calculated below in go)
    _frame_width = 0
    _frame_height = 0

    # how many frames processed
    _frame = 0
    running = True

    def __init__(self, source=0, crop_x1=0, crop_y1=0, crop_x2=500, crop_y2=500, max_width=640, b_and_w=False,
                 hog_win_stride=6, hog_padding=8, hog_scale=1.05, mog_enabled=False, people_options=None, lines=None,
                 font=cv2.FONT_HERSHEY_SIMPLEX, endpoint=None, pi=False, show_image=True, to_stdout=False,
                 save_first_frame=False, quit_after_first_frame=False):
        self.__dict__.update(locals())

    def change_running_state():
        self.running = not self.running

    def go_config(self, config_path='settings.ini'):

        # load config
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), config_path))

        # remote host settings
        self.endpoint = config.get('host', 'endpoint', fallback=None)

        # platform
        self.pi = config.getboolean('platform', 'pi')
        self.picamera = config.getboolean('platform', 'picamera')
        self.to_stdout = config.getboolean('platform', 'to_stdout')
        self.show_image = config.getboolean('platform', 'show_image')
        self.save_first_frame = config.getboolean('platform', 'save_first_frame')
        self.quit_after_first_frame = config.getboolean('platform', 'quit_after_first_frame')

        # video source settings
        try:
            self.crop_x1 = config.getint('video_source', 'frame_x1')
            self.crop_y1 = config.getint('video_source', 'frame_y1')
            self.crop_x2 = config.getint('video_source', 'frame_x2')
            self.crop_y2 = config.getint('video_source', 'frame_y2')
        except Exception as e:
            print('INFO: no cropping')

        self.max_width = config.getint('video_source', 'max_width')
        self.b_and_w = config.getboolean('video_source', 'b_and_w')

        # hog settings
        self.hog_win_stride = config.getint('hog', 'win_stride')
        self.hog_padding = config.getint('hog', 'padding')
        self.hog_scale = config.getfloat('hog', 'scale')

        # mog settings
        self.mog_enabled = config.getboolean('mog', 'enabled')
        if self.mog_enabled:
            self.mogbg = cv2.createBackgroundSubtractorMOG2()

        # self.lines = lines
        self.source = config.get('video_source', 'source')
        self.people_options = dict(config.items('person'))

        self.go()

    def go(self):

        # setup HUD
        self.last_time = time.time()

        # opencv 3.x bug??
        cv2.ocl.setUseOpenCL(False)

        # people tracking
        self.finder = PeopleTracker(people_options=self.people_options)

        # # STARTS HERE
        # # connect to camera
        # if self.picamera:

        #     from picamera.array import PiRGBArray
        #     from picamera import PiCamera

        #     self.camera = PiCamera()
        #     self.camera.resolution = (640, 480)
        #     self.camera.framerate = 30
        #     self.camera.vflip = True
        #     self.camera.hflip = True

        #     self.rawCapture = PiRGBArray(self.camera, size=(640, 480))

        #     time.sleep(1)  # let camera warm up

        # else:
        #     dirpath = os.path.dirname(os.path.abspath(__file__))
        #     self.camera = cv2.VideoCapture(os.path.join(dirpath, self.source))

        # setup detectors
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # # feed in video
        # if self.picamera:
        #     for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
        #         image = frame.array
        #         self.process(image)
        #         self.rawCapture.truncate(0)

        #         if self.quit_after_first_frame or cv2.waitKey(1) & 0xFF == ord('q'):
        #             break

        #         if not self.running:
        #             break
        # else:
        #     while self.camera.isOpened():
        #         rval, frame = self.camera.read()
        #         if rval:
        #             self.process(frame)
        #         else:
        #             break

        #         if self.quit_after_first_frame or cv2.waitKey(1) & 0xFF == ord('q'):
        #             break

        #         if not self.running:
        #             break

    def process(self, frame):

        frame = self.crop_and_resize(frame)

        print_frame_size = self._frame_height == 0

        self._frame_height = frame.shape[0]
        self._frame_width = frame.shape[1]

        if print_frame_size and not self.to_stdout:
            print('resized video width to {:2d}'.format(self._frame_width))

        frame = self.apply_mog(frame)
        frame = self.handle_the_people(frame)
        frame = self.render_hud(frame)

        # if self.show_image:
        #    cv2.imshow('Camerafeed', frame)

        if self.to_stdout:
            sys.stdout.write(frame.tostring())

        if self.save_first_frame and self._frame == 0:
            cv2.imwrite('first_frame.png', frame)

        return self.remaining

    # help us crop/resize frames as they come in
    def crop_and_resize(self, frame):
        # TODO: change the valid field before testing
        try:
            frame = frame[self.crop_y1:self.crop_y2, self.crop_x1:self.crop_x2]
        except Exception as e:
            pass

        frame = imutils.resize(frame, width=min(self.max_width, frame.shape[1]))

        return frame

    # apply background subtraction if needed
    def apply_mog(self, frame):
        if self.mog_enabled:
            mask = self.mogbg.apply(frame)
            frame = cv2.bitwise_and(frame, frame, mask=mask)

        return frame

    # all the data that overlays the video
    def render_hud(self, frame):
        this_time = time.time()
        diff = this_time - self.last_time
        fps = 1 / diff
        message = 'FPS: {:.2f}'.format(fps)

        self.last_time = time.time()

        return frame
        
    """drop rects which height is < frame_height*percentage (to filter out a more reliable result)

    Parameters
    ----------------
    rects:
        the rects that needs filtering
    frame_height:
        height of the frame that the rects are in 

    Returns
    -----------
    rects whose height is larger than the threshold
    """
    def drop_rects(self, rects, frame_height):
        percentage = float(self.people_options['percentage'])
        rects = np.array([(x, y, w, h) for (x, y, w, h) in rects if w > percentage*frame_height])

        return rects

    def handle_the_people(self, frame):
        if self.b_and_w:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # gray = cv2.GaussianBlur(gray, (15, 15), 0) # whether to use blur depends on the dimensions
            
        (rects, weight) = self.hog.detectMultiScale(gray, winStride=(self.hog_win_stride, self.hog_win_stride),
                                                    padding=(self.hog_padding, self.hog_padding), scale=self.hog_scale)
        
        # merge the overlapping bounding boxes
        rects = np.array([[x, y, x+w, y+h] for (x, y, w, h) in rects])
        rects = non_max_suppression(rects, probs=None, overlapThresh = 0.65)
        rects = [(x1, y1, x2-x1, y2-y1) for (x1, y1, x2, y2) in rects]

        # drop rects that are small (percentage can be changed in settings.ini)
        rects = self.drop_rects(rects, frame.shape[0])

        people = self.finder.people(rects)

        least_remaining = self.finder.least_remaining_time(frame.shape[1]) 

        # draw rectangles around people
        for person in people:
            frame = person.draw(frame)

        # put comments in the video
        cv2.putText(frame, 'Least Remaining Time: {:.2f} s'.format(least_remaining), (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(0, 255, 0), 1)

        self.remaining = least_remaining

        return frame

