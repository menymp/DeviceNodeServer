#!/usr/bin/env python
import cv2
import numpy as np


class LocalVideoService():
    def __init__(self, cameraId, width = 800, height = 600):
        # select first video device in system
        self.cam = cv2.VideoCapture(cameraId)
        # set camera resolution
        self.w = width
        self.h = height
        # set crop factor
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)

    def set_resolution(self, new_w, new_h):
        if isinstance(new_h, int) and isinstance(new_w, int):
            # check if args are int and correct
            if (new_w <= 800) and (new_h <= 600) and \
               (new_w > 0) and (new_h > 0):
                self.h = new_h
                self.w = new_w
            else:
                # bad params
                raise Exception('Bad resolution')
        else:
            # bad params
            raise Exception('Not int value')

    def get_frame(self, fdenable):
        success, image = self.cam.read()
        if success:
            # scale image
            image = cv2.resize(image, (self.w, self.h))
            image = np.zeros((self.h, self.w, 3), np.uint8)
            cv2.putText(image, 'No camera', (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)
        # encoding picture to jpeg
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()