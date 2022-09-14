#CODE TO RUN THE EXPERIMENT OF THE PAPER: "Evaluation of depth sonifications for visual-to-auditory sensory substitution" 
#THE CODE HAS TO BE RUNNED IN PARALLEL WITH THE SUPERCOLLIDER CODE THAT SYNTHESIZES THE SOUND 
#CHECK THE READ_ME FILE FOR INSTRUCTIONS

# Copyright (c) 
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  - Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Authors: Louis Commère, Jean Rouat (advisor)
# Date: July 26, 2022
# Organization: Groupe de recherche en Neurosciences Computationnelles et Traitement Intelligent des Signaux (NECOTIS),
# Université de Sherbrooke, Canada



import apriltag
import numpy as np
import freenect #we use the RGB sensor of a kinect, but the experiment can be runned with a simple webcam
import pandas as pd
from pythonosc import udp_client
import argparse
import sys
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *
import time
import datetime
import random
import cv2


#DIRECTORY FOR THE RESULTS TO SET 
DIR = ""

#RESULT FILE NAME 
FILENAME_RES = "result_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".csv"


MIN_DETECT = 0.45 # Minimum distance at wich the tag on the box an be detected (given the camera fov and the tag size)
ZRANGE = 1.0 # Sonified depth range for the experiment 
DCAM = MIN_DETECT+ZRANGE # Distance between de camera and the edge of the table
MAX_ANGLE_DETECT = np.deg2rad(10) # (horizontal fov / 2), use for when the azimuth is sonified to avoid generating an angle (for the positioning task) outside of the camera fov

#Video window to display camera images
class QtCapture(QtGui.QWidget):
    def __init__(self, *args):
        super(QtGui.QWidget, self).__init__()

        #Frame per second for the TAG detection / position estimation (can be increased if computational power allows it)
        self.fps = 24

        #Uncomment for webcam
        #self.cap = cv2.VideoCapture(*args)

        #OSC communication with Supercollider
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--ip", default="localhost")
        self.parser.add_argument("--port", type=int, default=57120)
        self.args = self.parser.parse_args()
        print(self.args)
        self.client = udp_client.SimpleUDPClient(self.args.ip, self.args.port)

        #Pyqt video handling
        self.video_frame = QtGui.QLabel()
        lay = QtGui.QVBoxLayout()
        #lay.setContentsMargins(0)
        lay.addWidget(self.video_frame)
        self.setLayout(lay)
        #self.cam_params = (589.322232303107740,589.849429472609130,321.140896612950880,235.563195335248370)

        #fx,fy,cx,cy of the camera 
        self.cam_params = (524,524,316.7,238.5) 

        #Distance between the tag and the subject
        self.dist = 0
        self.olddist=0

        #First time to send osc ? 
        self.firstosc = True

        #Use pan for traning?
        self.panTraining = False
        self.trainingON = False
                                
        #Sonif method and state (training / exp)
        self.sonifmethod = 0 #0 
        self.state = -1 # -1 -> traning, 0 watinig for exp , 1 running exp

        #Angle and dist
        self.angle = 90
        self.dist = 0


    def setFPS(self, fps):
        self.fps = fps

    #Function that is computed every frame
    def nextFrameSlot(self):

        #Get the grame from the camera
        #Uncomment for using webccam
        #ret, frame = self.cap.read()
        frame = np.array(freenect.sync_get_video()[0]) #comment if you are not using freenect
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #Detect the tag and estimate the pos
        detector = apriltag.Detector()
        result = detector.detect(gray)
        print("Number of detected tag:",len(result))

        if(len(result)>0): #If we detect at least one tag
            result = detector.detect(gray)
            x = result[0].center[0]
            y = result[0].center[1]
            
            #Position estimation
            pose = detector.detection_pose(result[0],self.cam_params,0.171)
            self.xpos = - pose[0][0][3] 
            self.zpos = np.clip(DCAM - pose[0][2][3],0,ZRANGE)

            #Compute the angle of the box
            if self.xpos >0:
                self.angle = 180 - np.degrees(np.arctan(self.zpos/self.xpos))
            elif self.xpos == 0 : 
                self.angle = 90
            elif self.xpos<0:
                self.angle = - np.degrees(np.arctan(self.zpos/self.xpos))
            self.dist = np.sqrt(self.xpos*self.xpos + self.zpos*self.zpos)

            #Send msg to supercollider
            if(self.trainingON and self.sonifmethod !=0):
                if self.panTraining:
                    self.sendDistToSc(self.zpos,self.angle)
                    #self.sendDistToSc(self.dist,self.angle)
                else:
                    #self.sendDistToSc(self.dist,0)
                    self.sendDistToSc(self.zpos,90)
            self.olddist = self.dist
        
        #if the tag is not detected
        else:
            x=0
            y=0

        #display the tracking of the tag
        cv2.circle(gray,(int(x),int(y)),10,(255,0,0),-1)
        img = QtGui.QImage(gray, frame.shape[1], frame.shape[0], QtGui.QImage.Format_Grayscale8)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

    def get_dist(self):
        #return self.dist
        return self.zpos

    def sendDistToSc(self,d,p): #d pour distance, p pour panning : boolean
        print("dist send", d,"angle,",p)
        #print(self.client)
        #tempremap = remap(self.dist,0.5,1.5,1.5,0.5)
        msg = [self.sonifmethod,d,p,self.firstosc]
        #c = udp_client.SimpleUDPClient(self.args.ip, self.args.port)
        #c.send_message("\Pos",msg)

        self.client.send_message("/Pos",msg)
        if (self.firstosc == True): self.firstosc = False

    def sendStopToSc(self):
        msg = [0,self.dist,0,False]
        self.client.send_message("/Pos",msg)
        self.firstosc = True

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000./self.fps)

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QtGui.QWidget, self).deleteLater()


#User interface with PyQT to choose the exp mode (training or positionning task) and the sonification 
class ControlWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        freenect.init()

        #Result table
        self.result = pd.DataFrame({"s":[],"tr":[],"te":[],"e":[],"pos":[],"posP":[],"rp":[],"pan":[],"angle":[],"angleP":[],"dist":[],"distP":[]}) #s= sonif method, tr: time to answe, 'e': error of replacement, 'rp': number of replay asked
        self.nbreplay = 0
        self.numExp = 0

        #Random pos for exp
        self.randomPosExp = 0
        self.randomAngleExp = 0
        self.randomDistsExp = 0
        
        #answering time 
        self.timeAtStart = 0
        self.timeAtStartTraining = 0
        self.trainingTime = 0

        #Start video and april tag recognition
        self.capture = None
        self.startCapture()

        layout = QGridLayout()
        self.setLayout(layout)
        self.state = "Training"
        self.sonif = 0

        expWidget=QWidget()
        expLayout =  QGridLayout()
        # radioButtonPan = QRadioButton("Pan")
        # #radiobuttonPan.toggled.connect(self.onClickedState)
        # expLayout.addWidget(radioButtonPan, 0, 1)
        radiobuttonExp = QRadioButton("Entrainement")
        radiobuttonExp.setChecked(True)
        radiobuttonExp.state = -1
        radiobuttonExp.toggled.connect(self.onClickedState)
        expLayout.addWidget(radiobuttonExp, 0, 0)
        radiobuttonExp = QRadioButton("Experience")
        radiobuttonExp.state = 0
        radiobuttonExp.toggled.connect(self.onClickedState)
        expLayout.addWidget(radiobuttonExp, 0, 2)
        self.start_button = QtGui.QPushButton('Start exp')
        self.start_button.clicked.connect(self.onClickedStart)
        self.end_button = QtGui.QPushButton('End exp')
        self.end_button.clicked.connect(self.onClickedEnd)
        self.start_Training_button = QtGui.QPushButton('Start train')
        self.start_Training_button.clicked.connect(self.onClickedStartTraining)
        self.end_Training_button = QtGui.QPushButton('End train')
        self.end_Training_button.clicked.connect(self.onClickedEndTraining)
        # self.end_button = QtGui.QPushButton('Stop')
        #vbox = QtGui.QVBoxLayout(self)
        #vbox.addWidget(self.b1)
        expLayout.addWidget(self.start_Training_button,1,0)
        expLayout.addWidget(self.end_Training_button,1,1)
        expLayout.addWidget(self.start_button,1,2)
        expLayout.addWidget(self.end_button,1,3)
        expWidget.setLayout(expLayout)
        self.panToggleButton= QPushButton("Angle") 
        self.panToggleButton.setCheckable(True)
        self.panToggleButton.clicked.connect(self.onClickedPan)
        expLayout.addWidget(self.panToggleButton,2,0)


        sonifLayout = QGridLayout()
        sonifWidget = QWidget()

        #vbox.addWidget(self.quit_button)
        #vbox.addWidget(self.capture.video_frame)

        radiobuttonSonif = QRadioButton("pause")
        radiobuttonSonif.setChecked(True)
        #radiobuttonSonif.setChecked(True)
        radiobuttonSonif.sonifMethod = 0
        radiobuttonSonif.toggled.connect(self.onClickedSonif)
        sonifLayout.addWidget(radiobuttonSonif, 2, 0)
        radiobuttonSonif = QRadioButton("amp")
        radiobuttonSonif.sonifMethod = 1
        radiobuttonSonif.toggled.connect(self.onClickedSonif)
        sonifLayout.addWidget(radiobuttonSonif, 2, 1)
        radiobuttonSonif = QRadioButton("reverb")
        radiobuttonSonif.sonifMethod = 2
        radiobuttonSonif.toggled.connect(self.onClickedSonif)
        sonifLayout.addWidget(radiobuttonSonif, 2, 2)
        radiobuttonSonif = QRadioButton("br")
        radiobuttonSonif.sonifMethod = 3
        radiobuttonSonif.toggled.connect(self.onClickedSonif)
        sonifLayout.addWidget(radiobuttonSonif, 2, 3)
        radiobuttonSonif = QRadioButton("freq")
        radiobuttonSonif.sonifMethod = 4
        radiobuttonSonif.toggled.connect(self.onClickedSonif)
        sonifLayout.addWidget(radiobuttonSonif, 2, 4)
        radiobuttonSonif = QRadioButton("snr")
        radiobuttonSonif.sonifMethod = 5
        radiobuttonSonif.toggled.connect(self.onClickedSonif)
        sonifLayout.addWidget(radiobuttonSonif, 2, 5)
        replay_button = QtGui.QPushButton('Replay')
        replay_button.clicked.connect(self.onClickedReplay)
        sonifLayout.addWidget(replay_button,3,1)
        save_button = QtGui.QPushButton('Save')
        save_button.clicked.connect(self.onClickedSave)
        sonifLayout.addWidget(save_button,3,3)
        sonifWidget.setLayout(sonifLayout)
        
        layout.addWidget(expWidget,0,0)
        layout.addWidget(sonifWidget,1,0)

        self.setLayout(layout)

        self.setWindowTitle('Control Panel')
        self.setGeometry(100,100,200,200)
        self.show()
    
    def onClickedPan(self): 
        # if button is checked 
        if self.panToggleButton.isChecked(): 
            self.capture.panTraining = True
        # if it is unchecked 
        else: 
            self.capture.panTraining = False
        print("Pan is",self.capture.panTraining)
            
    def onClickedStartTraining(self):
        if(self.capture.state==-1):
            self.capture.trainingON = True
            print("Training starts with method %s" % self.capture.sonifmethod)
            self.timeAtStartTraining = time.time()
            self.capture.state=-2 #training in progress

    def onClickedEndTraining(self):
        if( self.capture.state==-2):#In training
            self.capture.trainingON = False
            self.capture.sendStopToSc()
            print("Training ends with method %s" % self.capture.sonifmethod)
            self.trainingTime = time.time() - self.timeAtStartTraining
            self.capture.state=-1
            self.numExp = 0
    
    def onClickedSave(self):
         if(self.capture.state!=1):
            self.result.to_csv(DIR+FILENAME_RES,header=True)
            print("Result saved in %s" % (DIR+FILENAME_RES))

    def onClickedReplay(self):
        if(self.capture.state==1 and self.capture.sonifmethod !=0):
            if(self.capture.panTraining):
                self.capture.sendDistToSc(self.randomDistsExp,self.randomAngleExp)
                time.sleep(2.0)
                self.capture.sendStopToSc()
                print("Replay dist",self.randomDistsExp,"And Angle",self.randomAngleExp)
            else:
                self.nbreplay = self.nbreplay + 1
                print("Number of replay %s" % self.nbreplay)
                self.capture.sendDistToSc(self.randomPosExp,90)
                time.sleep(2.0)
                self.capture.sendStopToSc()

    def onClickedState(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            if(self.capture.state!=-2): #Be sure we are not in a training session
                self.capture.state = radioButton.state
                print("State is %s" % (self.capture.state))


    def onClickedSonif(self):
        self.capture.sendStopToSc()
        time.sleep(0.1)   
        radioButton = self.sender()
        if radioButton.isChecked():
            self.capture.sonifmethod = radioButton.sonifMethod
            print("Sonif is %s" % (self.capture.sonifmethod))

    def onClickedStart(self):
        #self.generateRandomAngleAndDist()
        if(self.capture.state==0 and self.capture.sonifmethod !=0): #sonif method 0 -> pause
            if(self.capture.panTraining):
                self.generateRandomAngleAndDist()
                self.capture.sendDistToSc(self.randomDistsExp,self.randomAngleExp)
                print("Exp start with random dist",self.randomDistsExp,"And Angle",self.randomAngleExp)

            else:
                self.randomPosExp = random.choice(np.arange(0.0,ZRANGE,0.01))
                self.capture.sendDistToSc(self.randomPosExp,90)
                print("Exp start with random pos %s" % self.randomPosExp)

            self.capture.state = 1
            time.sleep(2.0)
            self.timeAtStart = time.time()
            self.capture.sendStopToSc()   

    def generateRandomAngleAndDist(self): # to generate the angle and the distance in the detectable area
        self.randomAngleExp = int(random.choice(np.arange(0,180,1)))
        angleRad = np.deg2rad(self.randomAngleExp)
        if  self.randomAngleExp < 90 : 
            tempxmax = -DCAM*np.tan(MAX_ANGLE_DETECT)/(np.tan(angleRad)*np.tan(MAX_ANGLE_DETECT)+1)
            tempzmax = -np.tan(angleRad)*tempxmax
        elif self.randomAngleExp == 90:
            tempxmax = 999
            tempzmax = 999
        elif self.randomAngleExp > 90:
            tempxmax = DCAM*np.tan(MAX_ANGLE_DETECT)/(-np.tan(angleRad)*np.tan(MAX_ANGLE_DETECT)+1)
            tempzmax = -np.tan(angleRad)*tempxmax
        print("XMAX,",tempxmax,"ZMAX,",tempzmax)
        tempddistmax = min(np.sqrt(tempxmax*tempxmax+tempzmax*tempzmax),ZRANGE)
        self.randomDistsExp = random.choice(np.arange(0.,tempddistmax,0.01))
        self.randomPosExp = self.randomDistsExp*np.abs(np.sin(angleRad))
        #print("Dist",self.randomDistsExp,"Angle",self.randomAngleExp)


    def onClickedEnd(self):
        if(self.capture.state==1):
            answeringTimeTemp =  time.time() - self.timeAtStart
            distPartTemp =self.capture.get_dist()
            errTemp = abs(distPartTemp - self.randomPosExp)
            print("Exp end after %s" % (answeringTimeTemp))
            tempdf = pd.DataFrame({"s":[self.capture.sonifmethod],"tr":[answeringTimeTemp],"te":[self.trainingTime],"e":[errTemp],"pos":[self.randomPosExp],"posP":[distPartTemp],"rp":[self.nbreplay],"pan":[self.capture.panTraining],"angle":[self.randomAngleExp],"angleP":[self.capture.angle],"dist":[self.randomDistsExp],"distP":[self.capture.dist]})
            self.result = self.result.append(tempdf)
            self.capture.state = 0
            self.nbreplay = 0
            print(self.result,"\n")
            self.numExp = self.numExp+1
            print("Exp numero",self.numExp)

    def startCapture(self):
        if not self.capture:
            self.capture = QtCapture(0)
            #self.end_button.clicked.connect(self.capture.stop)
            # self.capture.setFPS(1)
            #self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)
        self.capture.start()
        self.capture.show()

    def endCapture(self):
        self.capture.deleteLater()
        self.capture = None
    
    def onExit(self):
        #self.result.to_csv(DIR+FILENAME_RES,header=True)
        self.endCapture()
        print("Close experiment app")


def remap(OldValue,OldMin,OldMax,NewMin,NewMax):
    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)  
    NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
    return NewValue

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = ControlWindow()
    #app.aboutToQuit.connect(window.onExit)
    sys.exit(app.exec_())
