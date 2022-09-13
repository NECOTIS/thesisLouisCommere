#CODE TO RUN THE EXPERIMENT OF THE PAPER: "Sonifoed distance in sensory substitution does not always improve localization: comparison with a 2D and 3D handheld device." 
#THE CODE HAS TO BE RUNNED IN PARALLEL WITH THE SUPERCOLLIDER CODE THAT SYNTHESIZES THE SOUND 
#CHECK THE READ_ME FILE FOR INSTRUCTIONS

import apriltag
import numpy as np
from pythonosc import udp_client
import argparse
import sys
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *
import cv2
import itertools
from pseyepy import Camera #we use a playstation camera but any webccam can be used, comment if not needed

#Size of the used tags (in meters)
SIZE_TAG_LOC= 0.043
SIZE_TAG_NAVIG = 0.13

class QtCapture(QtGui.QWidget):
    def __init__(self, *args):
        super(QtGui.QWidget, self).__init__()
        
        #Frame per second for the TAG detection / position estimation (can be increased if computational power allows it)
        self.fps = 24
        
        # Uncomment to use your Webcam 
        #self.cap = cv2.VideoCapture(0)

        # Eye playstation camera
        self.psCam = Camera(fps=self.fps ,resolution=Camera.RES_LARGE)

        #OSC communication with Supercollider 
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--ip", default="localhost")
        self.parser.add_argument("--port", type=int, default=57120)
        self.args = self.parser.parse_args()
        self.client = udp_client.SimpleUDPClient(self.args.ip, self.args.port)
        
        #PYQT objects to display the UI interface
        lay = QtGui.QGridLayout() 
        layMode = QtGui.QGridLayout()
         widgetMode = QWidget()
        layExp = QtGui.QGridLayout()
        widgetExp = QWidget()
        self.video_frame = QtGui.QLabel()
        lay.addWidget(self.video_frame,0,0)
        radiobuttonMode = QRadioButton("2D")
        radiobuttonMode.setChecked(True)
        radiobuttonMode.state = False
        radiobuttonMode.toggled.connect(self.onClickedMode)
        layMode.addWidget(radiobuttonMode,1,0)
        radiobuttonMode = QRadioButton("3D")
        radiobuttonMode.state = True
        radiobuttonMode.toggled.connect(self.onClickedMode)
        layMode.addWidget(radiobuttonMode,1,1)
        widgetMode.setLayout(layMode)
        lay.addWidget(widgetMode)
        radiobuttonExp = QRadioButton("Localization")
        radiobuttonExp.setChecked(True)
        radiobuttonExp.state = 0
        radiobuttonExp.toggled.connect(self.onClickedExp)
        layExp.addWidget(radiobuttonExp,2,0)
        radiobuttonExp = QRadioButton("Navigation")
        radiobuttonExp.state = 1
        radiobuttonExp.toggled.connect(self.onClickedExp)
        layExp.addWidget(radiobuttonExp,2,1)
        widgetExp.setLayout(layExp)
        lay.addWidget(widgetExp)
        self.setLayout(lay)

        #Camera parameters (fx,fy,cx,cy)
        self.cam_params = (524,524,316.7,238.5) 

        #Dist of the april tag
        self.dist = 0
                                
        #Activation grid
        self.numCellX=5
        self.numCellY=3
        wCell=640/self.numCellX
        hCell=480/self.numCellY
        self.actGrid=[]
        self.actGrid=[[Cell(int(i*wCell),int(j*hCell),int(wCell),int(hCell)) for i in range(self.numCellX)] for j in range(self.numCellY)]
        #print(self.actGrid)

        #Mode: 2D : False, 3D : True
        self.mode3D = False

        #Localization is the default experimental mode
        self.tagSize = SIZE_TAG_LOC #MOYEN loc
        
        #Start the pyQYT window
        self.start()

    def setFPS(self, fps):
        self.fps = fps

    #Function that is runned every frame (tag detection + send active cells to supercollider)
    def nextFrameSlot(self):
        #Uncomment for using webccam
        #ret, frame = self.cap.read()
        #print(frame.size)

        #Uncomment for using Kinect
        #frame = np.array(freenect.sync_get_video()[0])

        #Uncomment for using PS cam
        frame,timestamp = self.psCam.read()
        
        #print( frame.shape[0],frame.shape[1])

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detector = apriltag.Detector()
        result = detector.detect(gray)
        dist={} #list of dist of the detected april tag

        #Turn off previous active cells
        for i, j in list(itertools.product(range(self.numCellY),range(self.numCellX))):
            self.actGrid[i][j].isActive=False

        if(len(result)>0): #If we detect at least one tag
            numTag = len(result)  #number of detected tags
            #print("Number of detected tag:",numTag)
            result = detector.detect(gray)
            
            for i in range(numTag):  #for every detected tags
                
                #image coordinate of the tag 
                cX=int(result[i].center[0])
                cY=int(result[i].center[1])

                #Draw tag center (with circle)
                cv2.circle(frame,(cX,cY),10,(255,0,0),-1)

                #World coordinate of the tag
                pose = detector.detection_pose(result[i],self.cam_params,self.tagSize) 
                xworld = pose[0][0][3]
                yworld = pose[0][1][3]
                zworld = pose[0][2][3]
                print(zworld)

                #Check in which cell are the tags 
                for i, j in list(itertools.product(range(self.numCellY),range(self.numCellX))):
                    if self.actGrid[i][j].isInCell(cX,cY): 
                        self.actGrid[i][j].isActive=True
                        dist[(str(i),str(j))]=np.sqrt(xworld*xworld+yworld*yworld+zworld*zworld)
                        #print(dist)
                        #print(i,j)
                        #self.actGrid[i][j].displayCell(frame)
                        #self.sendCellToSC(i,j,False,0)


        #Draw cells, send osc to supercollider and set wasActive
        for i, j in list(itertools.product(range(self.numCellY),range(self.numCellX))):
            
            if self.actGrid[i][j].isActive and self.actGrid[i][j].wasActive and self.mode3D:
                 self.sendCellToSC(0,i,j,self.mode3D,dist[(str(i),str(j))]) #set synth parameters 

            if self.actGrid[i][j].isActive and not(self.actGrid[i][j].wasActive):
                self.sendCellToSC(1,i,j,self.mode3D,dist[(str(i),str(j))]) #Turn on synth
                self.actGrid[i][j].wasActive=True

            if not(self.actGrid[i][j].isActive) and self.actGrid[i][j].wasActive:
                self.sendCellToSC(-1,i,j,self.mode3D,0) #Turn off synth
                self.actGrid[i][j].wasActive=False
            # else:
            #     self.actGrid[i][j].wasActive=False
            #self.actGrid[i][j].displayCell(frame)
        
        for i, j in list(itertools.product(range(self.numCellY),range(self.numCellX))):
            if(not(self.actGrid[i][j].isActive)):
                 self.actGrid[i][j].displayCell(frame)
        
        for i, j in list(itertools.product(range(self.numCellY),range(self.numCellX))):
            if(self.actGrid[i][j].isActive):
                 self.actGrid[i][j].displayCell(frame)
                    
        #Display images
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)#.Format_Grayscale8)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

    #Function to send osc to supercollider
    #on: 1 (activate synth) / -1: deactivate synt / 0 change already activated
    def sendCellToSC(self,on,row,col,senddist,dist):
        #print(2-row,col)
        if senddist: 
            msg=[on,2-row,col,dist]
        else : 
            msg=[on,2-row,col,1]
            
        self.client.send_message("/2d3d",msg)

    #function to change the mode (2D / 3D)
    def onClickedMode(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.mode3D = radioButton.state
            print("3D mode is %s" % (self.mode3D))

    #function to change the experiment (localization vs navigation)
    def onClickedExp(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            if(radioButton.state==0): #Localization
                self.tagSize = SIZE_TAG_LOC
                print("Exp: localization")
            if(radioButton.state==1): #Navigation
                #self.tagSize = 0.171
                self.tagSize = SIZE_TAG_NAVIG

                print("Exp: Navigation")

    #start the pyQT window
    def start(self):
        self.setWindowFlags(QtCore.Qt.Tool)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000./self.fps)
        self.show()

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QtGui.QWidget, self).deleteLater()

    def onExit(self):
        self.deleteLater()
        print("Close experiment app")

    def remap(OldValue,OldMin,OldMax,NewMin,NewMax):
        OldRange = (OldMax - OldMin)  
        NewRange = (NewMax - NewMin)  
        NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
        return NewValue

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = QtCapture(0)
    #app.aboutToQuit.connect(window.onExit)
    sys.exit(app.exec_())
