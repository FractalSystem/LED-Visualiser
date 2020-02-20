#! python2
# -*- coding: utf-8 -*-
import curses
import time
import locale
import platform
import threading

#enable display of unicode characters
locale.setlocale(locale.LC_ALL, '')

# PROD allows testing of this program outside of the Raspberry Pi
if platform.system() == "Windows":
    PROD = False
else:
    PROD = True
if PROD:
    import FFT


class TUI():
    def __init__(self):
        if PROD:
            self.FFT_obj = FFT.FFT(True)
            self.threshhold = self.FFT_obj.get_threshhold()
            t = threading.Thread(target = self.FFT_obj.main)
            t.daemon = True
            t.start()
        else:
            self.FFT_obj = None
            self.threshhold = 300000
        self.menu = ["Mode", "Threshold", "Brightness"]
        self.options = [["Low Frequency", "Absolute Volume"], [str(self.threshhold)],
                        ["0%" ,"20%","40%", "60%", "80%", "100%"]]
        self.menu_index = 0
        self.options_index = [0, 0, 5]


    def main_loop(self):
        try:
            while True:
                if self.FFT_obj:
                    self.FFT_obj.set_options({"mode": self.options_index[0], "threshhold":int(self.threshhold), "brightness":self.options_index[2]*0.2})
                stdscr.addstr(0, 0, str("LED Configuation"))
                h,w = stdscr.getmaxyx()

                curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

                #set up menu text
                text = self.menu[self.menu_index]
                x = w//2 - len(text)//2
                y=h//2-1
                stdscr.addstr(y, x, text, curses.color_pair(1))

                #set up options text
                text = self.options[self.menu_index][self.options_index[self.menu_index]]
                x = w//2-len(text)//2
                y=h//2
                stdscr.addstr(y, x, text)
                stdscr.refresh()


                key = stdscr.getch()
                if key == curses.KEY_RIGHT:
                    if self.menu_index != len(self.menu)-1:
                        self.menu_index +=1
                    else:
                        pass
                        # self.menu_index =0
                elif key == curses.KEY_LEFT:
                    if self.menu_index != 0:
                        self.menu_index -=1
                    else:
                        pass
                        # self.menu_index =len(self.menu)-1

                if self.menu_index != 1:
                    if key == curses.KEY_UP:
                        if self.options_index[self.menu_index] != len(self.options[self.menu_index])-1:
                            self.options_index[self.menu_index] +=1
                        #disable wrapping
                        # else:
                        #     self.options_index[self.menu_index] =0
                    elif key == curses.KEY_DOWN:
                        if self.options_index[self.menu_index] != 0:
                            self.options_index[self.menu_index] -=1
                            #no wrapping here either
                else:
                    if key == curses.KEY_UP:
                        self.threshhold*=2.0
                        self.options[1] = [str(self.threshhold)]
                    elif key == curses.KEY_DOWN:
                        self.threshhold /= 2.0
                        self.options[1] = [str(self.threshhold)]

                stdscr.clear()
        except KeyboardInterrupt:
            stdscr.addstr(0,0,"Ending...")
            if self.FFT_obj:
                self.FFT_obj.end()
                print("Ended FFT")
            self.FFT_obj.leds.off()


if __name__ == "__main__":
    stdscr = curses.initscr()
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    t=TUI()
    t.main_loop()
    # stdscr.addstr(0, 0, "hi")
    # stdscr.addstr(5, 0, "hey")
    stdscr.clear()
    stdscr.refresh()
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    print("LED configurator exited successfully.")


