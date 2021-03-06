#!/usr/bin/env python2

# Copyright (c) 2014 Stephen Warren <swarren@wwwdotorg.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import math
import struct
import sys
import wave

import pygame
from pygame.locals import *

from OpenGL import platform
gl = platform.OpenGL
import OpenGL.arrays

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# FIXME: we should have cmdline parameters to configure this.
if False: # oscillofun
    x_ch = 0
    y_ch = 1
    x_inv = -1
    y_inv = -1
else: # youscope, beams of light, scroller
    x_ch = 1
    y_ch = 0
    x_inv = 1
    y_inv = 1

iters_per_frame = 1

sample_rate = 48000
num_channels = 2
bits_per_sample = 16
max_sample_value = (2 ** 15) - 1
w = None

def open_wav(f):
    global w
    global sample_rate
    global bits_per_sample
    global max_sample_value
    global num_channels

    w = wave.open(f)
    sample_rate = w.getframerate()
    num_channels = w.getnchannels()
    bits_per_sample = w.getsampwidth() * 8
    if bits_per_sample != 16:
        raise Exception('Only 16-bit audio is supported')

def read_data_chunk_from_wav():
    data = w.readframes(sample_rate / (60 * iters_per_frame))
    return data

def create_window():
    glutInit(sys.argv)
    width, height = 1024, 1024
    pygame.init()
    pygame.display.set_mode((width, height), OPENGL | DOUBLEBUF)
    glClear(GL_COLOR_BUFFER_BIT)
    glEnable(GL_BLEND)

def react_to_wav_parameters():
    gluOrtho2D(-max_sample_value * x_inv, max_sample_value * x_inv, -max_sample_value * y_inv, max_sample_value * y_inv)

def fade_image():
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # FIXME: Alpha value needs tweaking, and we likely need to split up each
    # video frame into chunks which get faded separately.
    # Something like 0.2 is good for lissajou.py's output, to prevent flickering
    # Something like 0.8 is good for oscillofun, to prevent too much ghosting
    glColor4f(0.0, 0.0, 0.0, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(-max_sample_value,  max_sample_value, 0.0)
    glVertex3f( max_sample_value,  max_sample_value, 0.0)
    glVertex3f( max_sample_value, -max_sample_value, 0.0)
    glVertex3f(-max_sample_value, -max_sample_value, 0.0)
    glEnd()

prev_x = 0
prev_y = 0
def draw_samples(data):
    global prev_x, prev_y

    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glLineWidth(2)
    glBegin(GL_LINES)
    # FIXME: This doesn't handle anything other than 16-bit signed
    for sample in xrange(len(data) / (2 * num_channels)):
        # FIXME: We should probably pre-calculate some of this
        channels = struct.unpack('<' + ('h' * num_channels), data[sample * 2 * num_channels:(sample + 1) * 2 * num_channels])
        x = channels[x_ch]
        y = channels[y_ch]
        # FIXME: The alpha calculations here were pulled out of thin air...
        # Still, they look reasonable on most of oscillofun and youscope.
        # I suspect we really need a non-linear response curve though
        line_len = math.sqrt(((x - prev_x) ** 2) + ((y - prev_y) ** 2))
        fraction_of_long_line = line_len / (4 * max_sample_value)
        color_factor = (1 - fraction_of_long_line) ** 100
        glColor4f(0.0, 1.0 * color_factor, 0.0, 1.0)
        glVertex3f(prev_x, prev_y, 0.0)
        glVertex3f(x, y, 0.0)
        prev_x = x
        prev_y = y
    glEnd()

def end_image():
    pygame.display.flip()

def main():
    create_window()
    open_wav(sys.stdin)
    react_to_wav_parameters()
    quit = False
    while True:
        for e in pygame.event.get():
            if e.type == QUIT:
                quit = True
            if e.type == KEYDOWN:
                if e.key in (pygame.K_q, pygame.K_x):
                    quit = True
            if quit:
                break
        if quit:
            break
        for i in xrange(iters_per_frame):
            fade_image()
            d = read_data_chunk_from_wav()
            if not d:
                # FIXME: It'd be nice to accept multiple files back-to-back and
                # keep going. A cmdline option to select the mode would be useful.
                # To do that, call open_wav() and react_to_wav_parameters() here.
                sys.exit(0)
            draw_samples(d)
        end_image()

if __name__ == '__main__':
    main()
