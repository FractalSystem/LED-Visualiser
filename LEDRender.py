from neopixel import *
from threading import Thread
import time
import copy

# LED strip configuration:
LED_COUNT      = 300      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0




class MyLED:
    def __init__(self, PROD):
        self.PROD = PROD
        r_d = self.set_speed()
        if not self.PROD:
            print("Render delay is: " + str(r_d) + "s")
        self.render_delay = r_d
        self.run = True
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        #confirm start
        self.strip.setPixelColor(1, Color(255,0,0))
        self.strip.show()
        self.current_chasers = [] #each chaser is {location: int, length: int, rgb:[r,g,b]}
        self.old_array = [Color(0, 0, 0)] * LED_COUNT
        Thread(target = self.loop).start()


    def set_speed(self, target_speed = 2.0):
        # in ms-1
        leds_per_m = 60.0
        leds_per_sec = target_speed * leds_per_m
        jump_distance = 2.0
        return jump_distance / leds_per_sec #render delay

        
    def loop(self):
        #main redering loop
        if not self.PROD:
            print("Running render loop...")
        if LED_COUNT >150:
            jump =2
        else:
            jump =1

        while self.run:
            start_time = time.time()
            master_arr = [Color(0,0,0)]*LED_COUNT
            # each chaser is {location: int, length: int, rgb:[r,g,b]}

            # fill in blank LEDs as long as they're between two on leds
            previous_chaser = None
            for i, chaser in enumerate(self.current_chasers):
                if previous_chaser:  # ignore the first one
                    location = chaser.get("location")
                    previous_chaser_location = previous_chaser.get("location")
                    previous_chaser_length = previous_chaser.get("length")
                    gap = location - (previous_chaser_location + previous_chaser_length)
                    if gap > 0 and gap <= 4:
                        previous_chaser["length"] += gap
                previous_chaser = chaser


            # Write current_chasers to a master render array
            for chaser in self.current_chasers:
                location = chaser.get("location")
                rgb = chaser.get("rgb")
                for i in range(chaser.get("length")): # fill in all leds along the chaser length
                    if location+i<LED_COUNT:
                        master_arr[location+i] = Color(rgb[1], rgb[0], rgb[2])
                chaser["location"] +=jump
            self.apply_array(master_arr)
            #delete all completed chasers
            self.current_chasers = [a for a in self.current_chasers if a.get("location")<=LED_COUNT]
            elapsed = time.time()-start_time #in seconds
            self.old_array = copy.copy(master_arr)
            if elapsed<self.render_delay:
                time.sleep(self.render_delay-elapsed)
            else:
                if not self.PROD:
                    print("LED's can't keep up. Try increasing render delay.")

    def fill_in(self, chasers):
        # fill in blank LEDs as long as they're between two on leds
        previous_chaser = None
        for i, chaser in enumerate(chasers):
            location = chaser.get("location")
            previous_chaser_location = chaser.get("location")
            previous_chaser_length = chaser.get("length")
            if previous_chaser: #ignore the first one
                gap = location-(previous_chaser_location+previous_chaser_length)
                if gap >0 and gap<=4:
                    previous_chaser["length"] = previous_chaser_length+gap


            previous_chaser = chaser

        
    def apply_array(self, array):
        for i,el in enumerate(array):
            if self.old_array[i] != el:
                self.strip.setPixelColor(i, el)
        self.strip.show()
    
    def chaser(self, r, g, b):
        chaser = {"location":0, "length":2, "rgb":[r,g,b]}
        if chaser not in self.current_chasers:
            self.current_chasers.append(chaser)
        
    def off(self):
        off = Color(0,0,0)
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, off)
        self.strip.show()


        
        
