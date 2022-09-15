// #CODE TO RUN THE EXPERIMENT OF THE PAPER: "Evaluation of depth sonifications for visual-to-auditory sensory substitution"
// #THE CODE HAS TO BE RUNNED IN PARALLEL WITH THE PYTHON CODE THAT ESTIMATE THE BOX POSITION
// #CHECK THE README FILE FOR INSTRUCTIONS

/*# Copyright (c)
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
# Université de Sherbrooke, Canada*/


//use the internal server with the scope
(
Server.default= s=Server.internal;
s.boot;
)


//Check the port of Supercollider (should be by default 57120)
NetAddr.langPort;

//Define the 5 synths (Amp, Reverb, BRR, Freq, SNR)

(
SynthDef(\AmpSonif, {|freqFond=400,deltaFreq=400,ampDB=0,pan=0|
	var nbHarm = 3;
	var freqs = Array.fill(nbHarm, { arg i; i*deltaFreq + freqFond });
	var sig = Klang.ar(`[ freqs, 1/nbHarm, nil], 1, 0) * ampDB.dbamp;//* EnvGen.kr(Env.perc(0.01,2),doneAction:2);
	Out.ar(0,Pan2.ar(sig,pan));
}).load(s);

SynthDef(\ReverbSonif, { |out, mix = 0.25, room = 0.9, damp = 0.9,pan=0|
    var sig = FreeVerb.ar(
            Decay.ar(Impulse.ar(1), 0.25, LFCub.ar(800, 0)), // mono src
            mix, // mix 0-1
            room, // room 0-1
            damp, // damp 0-1 duh
        4);
	Out.ar(out,Pan2.ar(sig,pan));
}).load(s);

SynthDef(\RepetitionRateSonif, {|rateFreq=3,pan=0|
	var sig = Decay.ar(Impulse.ar(rateFreq), 0.18,SinOsc.ar(1200,0,1)*2);
	Out.ar(0,Pan2.ar(sig,pan));
}).load(s);

SynthDef(\FreqSonif, {|midinote=69,pan=0|
	var freq=midinote.midicps;
	var sig = SinOsc.ar(freq)* AmpComp.kr(freq, 150);
	Out.ar(0,Pan2.ar(sig,pan));
}).load(s);

SynthDef(\SNRSonif, {|snd=1,pan=0|
	var amp=1;
	var sig = SinOsc.ar(440,0,amp*snd,PinkNoise.ar(1-snd)*amp);
	Out.ar(0,Pan2.ar(sig,pan));
}).load(s);

)


//check OSC messages and run sound synthesis
(
e = OSCFunc.newMatching({arg msg, time, addr, recvPort;
	//msg.postln;
	//msg.removeAt(0);
	msg.postln;
	//msg.size().postln;
	~sonif = msg[1];
	~dist = msg[2];
	~pan = linlin(msg[3],0,180,-1,1);
	~pan.postln;
	~firstosc = msg[4];
	~dmin=0.0;
	~dmax=1.0;
	~firstosc.if({
		//~synth.free;
		switch (~sonif,
			1,{//~synth.free;
				~amp = linlin(~dist,~dmin,~dmax,10,-40); //Amp
				~synth = Synth(\AmpSonif,[ampDB:~amp,pan:~pan]);},

			2,{//~synth.free;
				~mix = linlin(~dist,~dmin,~dmax,0.01,0.99); //Reverb
				~synth = Synth(\ReverbSonif,[mix:~mix,pan:~pan]);},

			3,{//~synth.free;
				~br = linlin(~dist,~dmin,~dmax,15.0,0.1); //Beep repettio rate
				~synth = Synth(\RepetitionRateSonif,[rateFreq:~br,pan:~pan]);},

			4,{//~synth.free;
				~midinote=linlin(~dist,~dmin,~dmax,107,48); //Freq
				~synth = Synth(\FreqSonif,[midinote:~midinote,pan:~pan]);},

			5,{//~synth.free;
				~snr =linlin(~dist,~dmin,~dmax,0.99,0.01); //SNR
				~synth = Synth(\SNRSonif,[snd:~snr,pan:~pan]);}
			)

	},{
		switch (~sonif,

			1,{~amp = linlin(~dist,~dmin,~dmax,10,-40);
				~amp.postln;
				~synth.set(\ampDB,~amp,\pan,~pan);},

			2,{~mix = linlin(~dist,~dmin,~dmax,0.05,0.95);
				~synth.set(\mix,~mix,\pan,~pan);},

			3,{~br = linlin(~dist,~dmin,~dmax,10.0,1.0);
				~synth.set(\rateFreq,~br,\pan,~pan);},

			4,{~midinote=linlin(~dist,~dmin,~dmax,107,48);
				~synth.set(\midinote,~midinote,\pan,~pan);},

			5,{~snr =linlin(~dist,~dmin,~dmax,0.95,0.05);
				~synth.set(\snd,~snr,\pan,~pan);},

			0,{~synth.free;}
		)
	});


	},
	'/Pos',
n);
)

