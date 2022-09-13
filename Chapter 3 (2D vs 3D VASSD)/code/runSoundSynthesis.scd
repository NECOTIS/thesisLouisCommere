//CODE TO RUN THE EXPERIMENT OF THE PAPER: "Sonifoed distance in sensory substitution does not always improve localization: comparison with a 2D and 3D handheld device."
//THE CODE HAS TO BE RUNNED IN PARALLEL WITH THE PYTHON CODE TO DETECT THE TAGS
//CHECK THE READ_ME FILE FOR INSTRUCTIONS

//use the internal server with the scope
(
Server.default= s=Server.internal;
//Server.default.options.outDevice_("Loopback Audio");
s.boot;
)

//Load the 12 buffers

//Free all: collectIntoBuffers
Buffer.freeAll(s);

//Pitched sound
~bufMus = SoundFile.collectIntoBuffers(thisProcess.nowExecutingPath.dirname +/+"sounds/*", s)

//Create a 2D array of synths (15 sound cells); row: elevation, col: azimut,
~synthArray2D = Array2D.new(rows: 3, cols: 5)

(
var col,row;
for ( 0,14, {arg i;
	col = i.div(3);
	row = i.mod(3);
	col.postln;
	row.postln;
	"i".postln;
	i.postln;
	~synthArray2D[row,col]=Synth(\BPR_buf,[bufnum:~bufMus[i],dur:1]);
	~synthArray2D[row,col].run(false);
	});
)

//Check the port of Supercollider (should be by default 57120)
NetAddr.langPort;

//check OSC messages and run sound synthesis
(
e = OSCFunc.newMatching({arg msg, time, addr, recvPort;
	//msg.postln;
	//msg.removeAt(0);
	msg.postln;
	msg.size().postln;
	~action=msg[1];
	~row=msg[2];
	~col=msg[3];
	~dist=msg[4];
/*	~dmin=0.0;
	~dmax=1.0;
	~dur= linlin(~dist,~dmin,~dmax,10,-40);*/
	switch(~action,
		-1,{ //Cell OFF
			~synthArray2D[~row,~col].run(false);
		},
		0,{ //Set dist of already activated cell
			~synthArray2D[~row,~col].set(\dur,~dist);
		},
		1,{ //Activate cell that was not activated
			~synthArray2D[~row,~col].run(true);
			~synthArray2D[~row,~col].set(\dur,~dist);
		}
	)
	},
	'/2d3d',
n);
)

