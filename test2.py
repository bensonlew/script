#!/usr/bin/env python
""" Inject command to own command line """

import sys, fcntl, termios
import pandas as pd


import numpy as np




def main():
    """ x """
    tty = sys.stdin
    old_attr = termios.tcgetattr(tty)
    new_attr = termios.tcgetattr(tty)
    # No echo please
    new_attr[3] &= ~termios.ECHO
    termios.tcsetattr(tty, termios.TCSANOW, new_attr)

    cmd = ' '.join(sys.argv[1:])
    for char in cmd:
        fcntl.ioctl(tty, termios.TIOCSTI, char)

    termios.tcsetattr(tty, termios.TCSANOW, old_attr)

if __name__ == '__main__':
    main()
