import time
import alsaaudio
import numpy as np
from math import floor
import LEDRender


class FFT():
    def __init__(self, PROD):
        self.CHUNK = 1024 * 2
        self.FS = 44100
        # time in seconds between steps for color change
        self.step_increment = 0.02
        self.PROD = PROD
        if not self.PROD:
            print("Each chunk is " + str(float(self.CHUNK) / self.FS * 1000) + "ms long with a frequency spacing of %sHz" % (
                str(round(float(self.FS) / self.CHUNK, 2))))

        self.threshhold = 300000
        self.brightness = 1
        self.sensitive_bands = 5

    def freqToIndex(self,freq):
        chunk = self.CHUNK
        if freq == 0:
            return 0
        else:
            f = float(self.FS) / chunk  # this is the spacing of each index in frequency space
            index = floor(freq / f)
            if index > chunk / 2:
                index = chunk / 2
            # print(f)
            return int(index)

    def index_to_freq(self,index):
        chunk=self.CHUNK
        T = float(chunk) / self.FS
        return index / T

    # returns the average of the frequency bands in lta
    def average_lta(self,lta):
        sum = 0
        for el in lta:
            sum += el
        return sum / len(lta)

    def calculate_octaves(self,chunk):
        # calculate 1/3 octave frequency ranges. Based on wikipedia
        arr = []
        for i in range(-18, 14):
            fcentre = 1000 * (2.0 ** (float(i) / 3))
            fd = 2.0 ** (1.0 / 6)
            fupper = fcentre * fd
            flower = fcentre / fd
            arr.append([self.freqToIndex(flower), self.freqToIndex(fupper)])
        return arr

    def set_options(self, options):
        # options: {"mode": 0/1, "threshhold": float, "brightness":float}
        mode = options.get("mode")
        threshhold = options.get("threshhold")
        brightness = options.get("brightness")
        if mode == 0:
            # low freq mode
            self.sensitive_bands = 5
        if mode == 1:
            # 'absolute volume' mode (minus a few troublesome frequency bands)
            self.sensitive_bands = 23
        self.brightness = brightness
        self.threshhold = threshhold

    def get_threshhold(self):
        return self.threshhold


    def generate_rainbow(self):
        t = time.time()
        # one step every second t=t
        # one step every 0.1 seconds t*=10
        # one step every step increment t/=step_increment
        t /= self.step_increment
        t = int(t)
        step = t % 1536
        # print(step)
        if step <= 255:
            return [255, step, 0]
        elif step <= 511:
            step -= 256
            return [255 - step, 255, 0]
        elif step <= 767:
            step -= 512
            return [0, 255, step]
        elif step <= 1023:
            step -= 768
            return [0, 255 - step, 255]
        elif step <= 1279:
            step -= 1024
            return [step, 0, 255]
        elif step <= 1535:
            step -= 1280
            return [255, 0, 255 - step]

    def end(self):
        print(". Ending")
        self.leds.run = False
        self.leds.off()

    def main(self):
        # LED initialisation
        self.leds = LEDRender.MyLED(self.PROD)
        self.leds.off()
        inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device="default")
        out = alsaaudio.PCM(device="plughw:1,0")

        out.setchannels(1)
        out.setrate(self.FS)
        out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        out.setperiodsize(self.CHUNK)

        # Set attributes: Mono, 44100 Hz, 16-bit little endian samples
        inp.setchannels(1)
        inp.setrate(self.FS)
        inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

        # each frame is 2 bytes. For 4096 bytes of data need 2048 frames
        inp.setperiodsize(self.CHUNK)

        lta_length = 10
        long_term_averages = [[] for i in range(32)]  # average over 30 frames
        short_term_average = [0] * 32  # average over 1 frame
        average_energy = 0
        frames = 0
        ADDITIVE_THRESHHOLD = 300000  # good for one third vol on oneplus 6

        # begin main loop
        try:
            while True:
                l, data_bytes = inp.read()
                out.write(data_bytes)
                if l:
                    data = np.frombuffer(data_bytes, dtype=np.int16)
                    fft_data = np.fft.rfft(data)  # this will be half of chunk size
                    indexes = self.calculate_octaves(len(fft_data) * 2)
                    if frames < lta_length:
                        frames += 1
                        total_energy = 0
                        for el in fft_data:
                            total_energy += abs(el)
                        average_energy += total_energy
                        for i in range(32):  # range(2) is 0 and 1
                            low_index = indexes[i][0]
                            high_index = indexes[i][1]
                            bandwidth = high_index - low_index + 1
                            sum = 0
                            for n in range(low_index, high_index):
                                sum += abs(fft_data[n])
                            average = sum / bandwidth
                            long_term_averages[i].append(average)
                    else:
                        short_term_average_list = []
                        beat_bands = []
                        long_term_low_f = 0
                        short_term_low_f = 0
                        # capture bands 3-8 for low frequency response
                        for i in range(self.sensitive_bands):
                            long_term_low_f += self.average_lta(long_term_averages[i + 3])
                        for i in range(32):  # range(2) is 0 and 1
                            low_index = indexes[i][0]
                            high_index = indexes[i][1]
                            bandwidth = high_index - low_index + 1
                            sum = 0
                            for n in range(low_index, high_index):
                                sum += abs(fft_data[n])
                            average = sum / bandwidth
                            short_term_average = average
                            short_term_average_list.append(short_term_average)
                            if short_term_average > self.average_lta(long_term_averages[i]) * 3:
                                beat_bands.append(i)
                            long_term_averages[i].pop(0)
                            long_term_averages[i].append(average)
                        for i in range(self.sensitive_bands):
                            short_term_low_f += short_term_average_list[i + 3]
                        if short_term_low_f > long_term_low_f + self.threshhold:
                            result = self.generate_rainbow()
                            #set brightness
                            result = [int(el*self.brightness) for el in result]
                            self.leds.chaser(*result)


        except KeyboardInterrupt:
            self.end()


if __name__ == "__main__":
    f = FFT(False)
    f.main()
