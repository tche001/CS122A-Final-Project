import sys
from optparse import OptionParser
import cv2.cv as cv
import os

#HAAR/OpenCV settings
min_size = (20, 20)
image_scale = 1.2
haar_scale = 2
min_neighbors = 3
haar_flags = 0

#ServoBlaster Settings
max_pwm = 249
min_pwm = 1
midScreenWindow = 40  # Midpoint "Error"
panStep = 1 # Pan degree change
tiltStep= 1 # Tilt degree change

startingXpos = 140 # starting x position
startingYpos = 140 # starting tilt position

panGpioPin = 2  # gpio pin 18
tiltGpioPin = 5  # gpio pin 23

#OpenCV
def detect_and_draw(img, cascade):
    gray = cv.CreateImage((img.width,img.height), 8, 1)
    small_img = cv.CreateImage((cv.Round(img.width / image_scale),
                   cv.Round (img.height / image_scale)), 8, 1)
 
    # convert color input image to grayscale
    cv.CvtColor(img, gray, cv.CV_BGR2GRAY)
 
    # scale input image for faster processing
    cv.Resize(gray, small_img, cv.CV_INTER_LINEAR)
 
    cv.EqualizeHist(small_img, small_img)
 
    midFace = None
 
    if(cascade):
        t = cv.GetTickCount()
        # HaarDetectObjects takes 0.02s
        faces = cv.HaarDetectObjects(small_img, cascade, cv.CreateMemStorage(0),
                                     haar_scale, min_neighbors, haar_flags, min_size)
        t = cv.GetTickCount() - t
        if faces:
            for ((x, y, w, h), n) in faces:
                # the input to cv.HaarDetectObjects was resized, so scale the
                # bounding box of each face and convert it to two CvPoints
                pt1 = (int(x * image_scale), int(y * image_scale))
                pt2 = (int((x + w) * image_scale), int((y + h) * image_scale))
                cv.Rectangle(img, pt1, pt2, cv.RGB(255, 0, 0), 3, 8, 0)
                # get the xy corner co-ords, calc the midFace location
                x1 = pt1[0]
                x2 = pt2[0]
                y1 = pt1[1]
                y2 = pt2[1]
                midFaceX = x1+((x2-x1)/2)
                midFaceY = y1+((y2-y1)/2)
                midFace = (midFaceX, midFaceY)
 
    cv.ShowImage("result", img)
    return midFace
    
def move(servo, angle):
    if (min_pwm <= angle <= max_pwm):
        command = 'echo %s=%s > /dev/servoblaster' % (str(servo), str(angle))
        os.system(command)
        #print command
    else:
        print "Servo angle must be an integer between 0 and 249.\n"
 
if __name__ == '__main__':
    # Setup HAAR classifier
    parser = OptionParser(usage = "usage: %prog [options] [camera_index]")
    parser.add_option("-c", "--cascade", action="store", dest="cascade", type="str", help="Haar cascade file, default %default", default = "./haarcascade_frontalface_alt.xml")
    (options, args) = parser.parse_args()
 
    cascade = cv.Load(options.cascade)
 
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
 
    input_name = args[0]
    if input_name.isdigit():
        capture = cv.CreateCameraCapture(int(input_name))
    else:
        print "We need a camera input! Specify camera index e.g. 0"
        sys.exit(0)
 
    cv.NamedWindow("result", 1)
 
    if capture:
        frame_copy = None

        move(panGpioPin, startingXpos)
        move(tiltGpioPin, startingYpos)

        while True:
            frame = cv.QueryFrame(capture)
            if not frame:
                cv.WaitKey(0)
                break
            if not frame_copy:
		frame_copy = cv.CreateImage((frame.width,frame.height),
                                            cv.IPL_DEPTH_8U, frame.nChannels)
            if frame.origin == cv.IPL_ORIGIN_TL:
                cv.Copy(frame, frame_copy)
            else:
                cv.Flip(frame, frame_copy, 0)
            
            midScreenX = (frame.width/2)
            midScreenY = (frame.height/2)
  
            midFace = detect_and_draw(frame_copy, cascade)
            
            if midFace is not None:
                midFaceX = midFace[0]
                midFaceY = midFace[1]
                                
                #Find out if the X component of the face is to the left of the middle of the screen.
                if(midFaceX < (midScreenX - midScreenWindow)):
                    #Update the pan position variable to move the servo to the right.
                    startingXpos += panStep
                    print str(midFaceX) + " > " + str(midScreenX) + " : Pan Right : " + str(startingXpos)
                #Find out if the X component of the face is to the right of the middle of the screen.
                elif(midFaceX > (midScreenX + midScreenWindow)):
                    #Update the pan position variable to move the servo to the left.
                    startingXpos -= panStep
                    print str(midFaceX) + " < " + str(midScreenX) + " : Pan Left : " + str(startingXpos)
                else:
                    print str(midFaceX) + " ~ " + str(midScreenX) + " : " + str(startingXpos)
                
                startingXpos = min(startingXpos, max_pwm)
                startingXpos = max(startingXpos, min_pwm)               
                move(panGpioPin, startingXpos)

                #Find out if the Y component of the face is below the middle of the screen.
                if(midFaceY < (midScreenY - midScreenWindow)):
                    if(startingYpos <= max_pwm):
                        #Update the tilt position variable to lower the tilt servo.
                        startingYpos -= tiltStepSize
                        print str(midFaceY) + " > " + str(midScreenY) + " : Tilt Down : " + str(startingYpos)
                #Find out if the Y component of the face is above the middle of the screen.
                elif(midFaceY > (midScreenY + midScreenWindow)):
                    if(startingYpos >= 1):
                        #Update the tilt position variable to raise the tilt servo.
                        startingYpos += tiltStep
                        print str(midFaceY) + " < " + str(midScreenY) + " : Tilt Up : " + str(startingYpos)
                else:
                    print str(midFaceY) + " ~ " + str(midScreenY) + " : " + str(startingYpos)
                
                startingYpos = min(startingYpos, max_pwm)
                startingYpos = max(startingYpos, min_pwm)  
                move(tiltGpioPin, startingYpos)
                               
            if cv.WaitKey(10) >= 0: # 10ms delay
                break
 
    cv.DestroyWindow("result")
