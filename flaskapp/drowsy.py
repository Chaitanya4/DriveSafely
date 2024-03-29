from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
from threading import Thread
from urllib.request import urlopen
import numpy as np
import playsound
import argparse
import imutils
import time
import dlib
import cv2
from flask import Flask,jsonify,render_template,request,redirect,Response
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')
def drowsydetect():
        def sound_alarm():
                # play an alarm sound
                playsound.playsound("alarm.wav")
        def eye_aspect_ratio(eye):
                # compute the euclidean distances between the two sets of
                # vertical eye landmarks (x, y)-coordinates
                A = dist.euclidean(eye[1], eye[5])
                B = dist.euclidean(eye[2], eye[4])
         
                # compute the euclidean distance between the horizontal
                # eye landmark (x, y)-coordinates
                C = dist.euclidean(eye[0], eye[3])
         
                # compute the eye aspect ratio
                ear = (A + B) / (2.0 * C)
         
                # return the eye aspect ratio
                return ear

        # define two constants, one for the eye aspect ratio to indicate
        # blink and then a second constant for the number of consecutive
        # frames the eye must be below the threshold for to set off the
        # alarm
        EYE_AR_THRESH = 0.25
        EYE_AR_CONSEC_FRAMES = 22
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        # initialize the frame counter as well as a boolean used to
        # indicate if the alarm is going off
        COUNTER = 0
        ALARM_ON = False

        # initialize dlib's face detector (HOG-based) and then create
        # the facial landmark predictor

        print("[INFO] loading facial landmark predictor...")
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        # grab the indexes of the facial landmarks for the left and
        # right eye, respectively
        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        # start the video stream thread
        print("[INFO] starting video stream thread...")
        vs = VideoStream(src=0).start()
        time.sleep(1.0)
         
        # loop over frames from the video stream
        while True:
            
                
                # grab the frame from the threaded video file stream, resize
                # it, and convert it to grayscale
                # channels)
                frame= vs.read()
                frame = imutils.resize(frame, width=900)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
         
                # detect faces in the grayscale frame
                rects = detector(gray, 0)

                

                faces = face_cascade.detectMultiScale(gray, 1.3, 5) 
          
                for (x,y,w,h) in faces:
                        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,0),2)
                # To draw a rectangle in a face   
                        roi_gray = gray[y:y+h, x:x+w] 
                        roi_color = frame[y:y+h, x:x+w] 
        # loop over the face detections
                for rect in rects:
                        # determine the facial landmarks for the face region, then
                        # convert the facial landmark (x, y)-coordinates to a NumPy
                        # array
                        shape = predictor(gray, rect)
                        shape = face_utils.shape_to_np(shape)
         
                        # extract the left and right eye coordinates, then use the
                        # coordinates to compute the eye aspect ratio for both eyes
                        leftEye = shape[lStart:lEnd]
                        rightEye = shape[rStart:rEnd]
                        leftEAR = eye_aspect_ratio(leftEye)
                        rightEAR = eye_aspect_ratio(rightEye)
         
                        # average the eye aspect ratio together for both eyes
                        ear = (leftEAR + rightEAR) / 2.0
                        # compute the convex hull for the left and right eye, then
                        # visualize each of the eyes
                        leftEyeHull = cv2.convexHull(leftEye)
                        rightEyeHull = cv2.convexHull(rightEye)
                        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
                        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
                        # check to see if the eye aspect ratio is below the blink
                        # threshold, and if so, increment the blink frame counter
                        if ear < EYE_AR_THRESH:
                                COUNTER += 1
         
                                # if the eyes were closed for a sufficient number of
                                # then sound the alarm
                                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                                        # if the alarm is not on, turn it on
                                        if not ALARM_ON:
                                                ALARM_ON = True
         
                                                # check to see if an alarm file was supplied,
                                                # and if so, start a thread to have the alarm
                                                # sound played in the background
                                                
                                                t = Thread(target=sound_alarm)
                                                t.deamon = True
                                                t.start()
         
                                        # draw an alarm on the frame
                                        cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
         
                        # otherwise, the eye aspect ratio is not below the blink
                        # threshold, so reset the counter and alarm
                        else:
                                COUNTER = 0
                                ALARM_ON = False
                        # draw the computed eye aspect ratio on the frame to help
                        # with debugging and setting the correct eye aspect ratio
                        # thresholds and frame counters
                        cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
         
                # show the frame
                #cv2.imshow("Frame", frame)
                frame = cv2.imencode('.jpg', frame)[1].tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                key = cv2.waitKey(1) & 0xFF
         
                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                    break
@app.route('/video_stream')
def video_stream():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(drowsydetect(),mimetype='multipart/x-mixed-replace; boundary=frame')
