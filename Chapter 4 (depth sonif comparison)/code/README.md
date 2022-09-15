Code to reproduce the experiments in the paper: "Evaluation of depth sonifications for visual-to-auditory sensory substitution"

To run the system, you have to run the python and the supercollider files in parallel. 

For the position estimation (runTagDetection.py):
- Version of python: 3.6.8
- Version of the libraries: apriltag: 0.0.16, numpy: 1.17.2, pythonosc: 1.7.0, pyqtgraph: 0.10.0, pyqt: 5.9.2, cv2: 4.1.1
- In the paper, we use the RGB sensor of a Kinect (with the freenect lib) but any webcam can be used. 
- You can download the tags from https://april.eecs.umich.edu/software/apriltag
- Sizes of the tags you use can be set at the beginning of the python code

For the sound synthesis (runSoundSynthesis.scd)
- the code is written with Supercollider. If you are not familiar with Supercollider, you should first read this : https://doc.sccode.org/Tutorials/Getting-Started/02-First-Steps.html#:~:text=To%20execute%20it%2C%20simply%20click,Try%20this%20now 
- Supercollider version we use: 3.11.2

Interface of the system: 
