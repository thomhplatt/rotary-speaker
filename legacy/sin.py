import numpy as np

import state

class Audio:
    def __init__(self, frequency = 440):

        self.frequency = frequency
        self.index = 0        
        self.amplitude = 1
        self.sample_rate = 44100
        self.phase = 0.0

    def callback(self, outdata, frames, time, status):

        if status:
            print(status)

        t = (self.index + np.arange(frames)) / self.sample_rate
      
        signal = state.AMPLITUDE * np.sin(2 * np.pi * state.FREQ * t)
      
        outdata[:] = signal.reshape(-1, 1)
              
        self.index += frames

    # def callback(self, outdata, frames, time, status):

    #     if status:
    #         print(status)

    #     frequency = state.FREQUENCY
        
    #     phase_increment = 2 * np.pi * frequency / self.sample_rate
    #     phase = self.phase + phase_increment * np.arange(frames)
        
    #     signal = state.AMPLITUDE * np.sin(phase)
        
    #     outdata[:] = signal.reshape(-1, 1)
    #     self.phase = phase[-1] + phase_increment

    


