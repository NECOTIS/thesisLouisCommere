Code to reproduce the experiments in the paper: "Evaluation of depth sonifications for visual-to-auditory sensory substitution"

To run the system, you have to run the python and the supercollider codes in parallel. 

For the position estimation of the pbox(runBoxDetection.py):
- Version of python: 3.6.8
- Version of the libraries: apriltag: 0.0.16, numpy: 1.17.2, pythonosc: 1.7.0, pyqtgraph: 0.10.0, pyqt: 5.9.2, cv2: 4.1.1
- In the paper, we use the RGB sensor of a Kinect (with the freenect lib) but any webcam can be used. 
- You can download the tags from https://april.eecs.umich.edu/software/apriltag
- **You have to set at the beginning of the code**: TAG_SIZE (the size of the tag you are using to estimate the position), DIR (directory in which results are saved), MIN_DETECT (Minimum distance at wich the tag can be detected given the camera fov and the tag size -> to be determined experimentally or choose a large enough value), ZRANGE (Sonified depth range for the experiment), MAX_ANGLE_DETECT (horizontal fov / 2), use for the azimut sonification to avoid generating an angle (for the positioning task) outside of the camera fov)
- The camera should be set at ZRAGE+MIND_DETECT meter from the user

For the sound synthesis (runSoundSynthesis.scd)
- the code is written with Supercollider. If you are not familiar with Supercollider, you should first read this : https://doc.sccode.org/Tutorials/Getting-Started/02-First-Steps.html#:~:text=To%20execute%20it%2C%20simply%20click,Try%20this%20now 
- Supercollider version we use: 3.11.2

Interface of the system: 

 <img src="https://user-images.githubusercontent.com/6518453/190511778-78cbab68-8dd3-45ff-84b6-87e09dde6081.png" width="300">


