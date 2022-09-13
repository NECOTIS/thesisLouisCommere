Code to reproduce the experiments presented in the article "Sonified distance in sensory substitution does not always improve localization: comparison with a 2D and 3D handheld device." (https://ieeexplore.ieee.org/document/9855663)

To run the system, you have to run the python and the supercollider files in parallel. 

For the tag detection (runTagDetection.py):
- We use a playstation eye camera (with the pseyepy lib)  for the video input but any webcam can be used. 
- Sizes of the tags you use can be set at the beginning of the python code


For the sound synthesis (runSoundSynthesis.scd)
- the code is written with Supercollider. If you are not familiar with Supercollider, you should first read this : https://doc.sccode.org/Tutorials/Getting-Started/02-First-Steps.html#:~:text=To%20execute%20it%2C%20simply%20click,Try%20this%20now 



Interface of the system: 


 <img src="https://user-images.githubusercontent.com/6518453/189969154-08d6aae5-fa0a-4e4e-b2f6-51de0a7e8670.png" width="300">

 2D / 3D button: Mode 2D -> Distance between the camera and the tag is not encoded, Mode 3D -> the distance is encoded (with repetition rate)
 
 Localization / Navigaton button: Localization -> localization experiment (tags are smaller) / Navigation -> navigation experiments (tags are bigger)



