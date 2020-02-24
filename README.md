# LED-Visualiser
A music visualiser built for the Raspberry Pi using a WS2812B LED strip.
Produces a similar effect to the one seen [here](https://www.youtube.com/watch?v=lU1GVVU9gLU) except it is implemented entirely in software.
This approach allows more customisation while bypassing the need for the electronics used in the video.

# Setup
The program is written for a WS2812B LED strip. Audio is inputted through a generic USB sound card. This is essential as the LEDs require the
PWM pin, which disables the on-board audio of the Raspberry Pi.

A text-based curses UI is provided through TUI.py. This allows live adjustment of the triggering threshhold, brightness, mode and speed.

Automatic startup on Raspbian can be achieved by setting up TUI.py to run as a systemd service as follows (provided TUI.py is in /home/pi/):

    sudo mv tui.service /lib/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable tui.service

### Modes:

    Low frequency: FFT will only respond to low frequency bands.
    Absolute volume: FFT will take all frequency bands into account when triggering the LEDs.
    
# Requirements
    numpy==any
    pyalsaaudio==0.8.4
    rpi-ws281x==1.0.0
