#!/usr/bin/env python
"""Reports where on screen eyes are pointing"""

import os
import time

import cv
import numpy

import cvnumpyconvert
from mouse import setMousePosition

class EyeTracker(object):
    def __init__(self):
        self.storage = cv.CreateMemStorage(0)
        self.last_face_position = None
        self.face_cascade = cv.Load(os.path.expanduser('~/Downloads/haarcascade_frontalface_default.xml'))
        #self.face_cascade = cv.Load('haarcascade_frontalface_alt.xml')
        #self.eye_cascade = cv.Load(os.path.expanduser('~/Downloads/parojos-22x15.xml'))
        self.eye_cascade = cv.Load(os.path.expanduser('~/Downloads/parojosG-45x11.xml'))
        self.detect_times = []
        self.eye_pair_history = []
        self.xamount_histories = [[], []]
        self.yamount_histories = [[], []]
        self.xpos_history = []
        self.ypos_history = []

    def detect(self, image):
        f = self.find_face(image)
        if f:
            eyes = self.find_eyes(image, f)
            if eyes:
                rolling_eyes = self.rolling_eye_pair(eyes, samples=5)
                # find black portions of outside thirds of image
                pupils = self.find_pupils(image, rolling_eyes)
        self.fps(False)

    def rolling_eye_pair(self, eye_pair, samples=3):
        self.eye_pair_history = self.eye_pair_history[-(samples-1):]
        self.eye_pair_history.append(eye_pair)
        ave_eye_pair = [0,0,0,0]
        for i in range(4):
            ave_eye_pair[i] = sum([es[0][i] for es in self.eye_pair_history])/len(self.eye_pair_history)
        rect(image, [ave_eye_pair], (100,110,30))
        return [ave_eye_pair, '?']

    def fps(self, display=True):
        t = time.time()
        self.detect_times.append(t)
        if len(self.detect_times) > 3:
            if display:
                print 'FPS: %.1d' % (len(self.detect_times) / (t - self.detect_times[0]))
        if len(self.detect_times) > 100:
            self.detect_times.pop(0)

    def find_pupils(self, image, eyes):
        w, h = cv.GetSize(image)
        left  = cv.CreateImage((eyes[0][2]/3, eyes[0][3]*2/3,), 8, 3)
        right = cv.CreateImage((eyes[0][2]/3, eyes[0][3]*2/3,), 8, 3)
        left_gray  = cv.CreateImage((eyes[0][2]/3, eyes[0][3]*2/3,), 8, 1)
        right_gray = cv.CreateImage((eyes[0][2]/3, eyes[0][3]*2/3,), 8, 1)
        left_region = cv.GetSubRect(image, (eyes[0][0], eyes[0][1]+eyes[0][3]/6,
            eyes[0][2]/3, eyes[0][3]*2/3))
        right_region = cv.GetSubRect(image, (eyes[0][0]+eyes[0][2]*2/3, eyes[0][1]+eyes[0][3]/6,
            eyes[0][2]/3, eyes[0][3]*2/3))
        cv.Copy(left_region, left)
        cv.Copy(right_region, right)
        cv.CvtColor(left, left_gray, cv.CV_BGR2GRAY)
        cv.CvtColor(right, right_gray, cv.CV_BGR2GRAY)
        l = numpy.squeeze(cvnumpyconvert.cv2array(left_gray))
        r = numpy.squeeze(cvnumpyconvert.cv2array(right_gray))
        if False:
            from matplotlib.pylab import imshow, show
            imshow(l)
            show()
            imshow(r)
            show()
        #cv.ShowImage('left', left_gray)
        #cv.ShowImage('right', right_gray)
        for i, arr, side in [(0, l, 'left'), (1, r, 'right')]:
            squared = arr**2
            ave = numpy.average(squared**2)
            rightness = numpy.array([range(arr.shape[1]) for _ in range(arr.shape[0])])
            downness = numpy.array([[x for _ in range(arr.shape[1])] for x in range(arr.shape[0])])
            xamount = numpy.sum(squared*(rightness**2)) / numpy.sum(rightness**2 * ave)
            yamount = numpy.sum(squared*(downness **2)) / numpy.sum(downness **2 * ave)
            self.xamount_histories[i].append(xamount)
            self.yamount_histories[i].append(yamount)
            #xmin = min(self.xamount_histories[i])
            #xmax = max(self.xamount_histories[i])

            sorted_history = list(self.xamount_histories[i])
            sorted_history.sort()
            try:
                xmin = min(sorted_history[len(sorted_history)/6:len(sorted_history)*5/6])
                xmax = max(sorted_history[len(sorted_history)/6:len(sorted_history)*5/6])
            except ValueError:
                print 'jump starting,', len(sorted_history)
                xmin = sorted_history[0]
                xmax = sorted_history[0]

            sorted_history = list(self.yamount_histories[i])
            sorted_history.sort()
            try:
                ymin = min(sorted_history[len(sorted_history)/6:len(sorted_history)*5/6])
                ymax = max(sorted_history[len(sorted_history)/6:len(sorted_history)*5/6])
            except ValueError:
                print 'jump starting,', len(sorted_history)
                ymin = sorted_history[0]
                ymax = sorted_history[0]

            screen_width = 1440
            screen_height = 900

            xpos = (xamount - xmin) / (xmax - xmin) * screen_width
            ypos = (yamount - ymin) / (ymax - ymin) * screen_height
            self.xpos_history.append(xpos)
            self.ypos_history.append(ypos)
            smooth = 20
            xsmoothed = sum(self.xpos_history[-smooth:]) / len(self.xpos_history[-smooth:])
            ysmoothed = sum(self.ypos_history[-smooth:]) / len(self.ypos_history[-smooth:])
            #setMousePosition(xsmoothed, ysmoothed)
            setMousePosition(xsmoothed, ysmoothed)



        #raw_input('break to allow for ctrl-c')
        #print r
        #raw_input()

    def find_eyes(self, image, f):
        w, h = cv.GetSize(image)
        small = cv.CreateImage((f[0][2], f[0][3]*2/3,), 8, 3)
        src_region = cv.GetSubRect(image, (f[0][0], f[0][1],
            f[0][2], f[0][3]*2/3))
        cv.Copy(src_region, small)
        grayscale = cv.CreateImage((f[0][2], f[0][3]*2/3), 8, 1)
        cv.CvtColor(small, grayscale, cv.CV_BGR2GRAY)
        eye_pairs = cv.HaarDetectObjects(grayscale, self.eye_cascade, self.storage, 1.2, 2, 0, (10, 10))
        for eye_pair in eye_pairs:
            eye_pair = ((eye_pair[0][0]+f[0][0], eye_pair[0][1]+f[0][1],
                eye_pair[0][2], eye_pair[0][3]), eye_pair[1])
            rect(image, eye_pair, (255,0,0))
            return eye_pair

    def find_face(self, image):
        w, h = cv.GetSize(image)
        grayscale = cv.CreateImage((w, h), 8, 1)
        cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
        faces = cv.HaarDetectObjects(grayscale, self.face_cascade, self.storage, 1.2, 2, 0, (300, 250))

        if faces:
            #print 'face detected!'
            for f in faces:
                rect(image, f, (0, 255, 0))
                self.frames_since_face = 0
                self.last_face_position = f
                return f
        elif self.last_face_position:
            #print 'can\'t find face, using old postion'
            self.frames_since_face += 1
            f = self.last_face_position
            rect(image, f, (0, 100, 200))
            return f
        else:
            print 'no face'

def rect(image, result, color=(0,0,255)):
    f = result
    cv.Rectangle(image, (f[0][0], f[0][1]),
            (f[0][0]+f[0][2], f[0][1]+f[0][3]),
            cv.RGB(*color), 3, 8, 0)


if __name__ == '__main__':

    cv.NamedWindow('a_window', cv.CV_WINDOW_AUTOSIZE)

    et = EyeTracker()
    while True:
        capture = cv.CaptureFromCAM(0)
        image = cv.QueryFrame(capture)
        et.detect(image)

        cv.ShowImage('asdf', image)

    raw_input()
