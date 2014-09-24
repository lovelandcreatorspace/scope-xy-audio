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
import pygame
from pygame.locals import *
import sys
import time

def write_u(f, n, bytes):
    for i in range(bytes):
        f.write(chr(n & 0xff))
        n = n >> 8

def write_u32(f, n):
    write_u(f, n, 4)

def write_u16(f, n):
    write_u(f, n, 2)

def write_u8(f, n):
    write_u(f, n, 1)

winsize = (640, 480)
sample_rate = 48000
channels = 2
sample_bits = 16
seconds = 10 * 60

base_freq = 50
mult_scale = 1.0
max_mult = 10 * mult_scale
l_mult = mult_scale
r_mult = mult_scale

phase_max = 16.0
phase = phase_max / 2

sample_bytes = sample_bits / 8
scale = (2 ** (sample_bits - 1)) - 1
sample_count = sample_rate * seconds

f = open('/dev/stdout', 'wb')

header_len = 18
data_len = sample_count * channels * sample_bytes

f.write('RIFF')
write_u32(f, data_len + header_len + 12) # RIFF section length (whole file minus 'RIFF')
f.write('WAVE')
f.write('fmt ')
# WAVEFORMATEX header (header_len + 18)
write_u32(f, header_len) # fmt section length
write_u16(f, 1) # PCM
write_u16(f, channels) # channel count
write_u32(f, sample_rate) # frequency
write_u32(f, sample_rate * channels * sample_bytes) # byte-rate
write_u16(f, channels * sample_bytes) # block align
write_u16(f, sample_bits) # bits/sample/channel
write_u16(f, header_len - (16 + 2))
f.write('data')
write_u32(f, data_len)

pygame.init()
surface = pygame.display.set_mode(winsize, pygame.HWSURFACE | pygame.DOUBLEBUF)

def dump_freqs():
    print >>sys.stderr, 'Left: %dHz (x%0.2f)' % (c_freqs[0], c_freqs[0] / base_freq),
    print >>sys.stderr, 'Right %dHz (x%0.2f)' % (c_freqs[1], c_freqs[1] / base_freq),
    print >>sys.stderr, "Phase: 2pi * %f" % (phase / phase_max)

def gen_freqs():
    global c_freqs
    l_scaled_mult = l_mult / mult_scale
    r_scaled_mult = r_mult / mult_scale
    l_freq = base_freq * l_scaled_mult
    r_freq = base_freq * r_scaled_mult
    c_freqs = (l_freq, r_freq)
    dump_freqs()

gen_freqs()
sample = 0

running = True
while running:
    if not pygame.event.peek():
        ms = pygame.time.get_ticks()
        max_samples = ((ms + 10.0) * sample_rate) / 1000
        #print >>sys.stderr, sample, max_samples
        if sample > max_samples:
            #print >>sys.stderr, "Sleep!"
            time.sleep(0.05) # Comment this out or reduce sleep time if audio is intermittent
            continue
        for chan in range(channels):
            if chan:
                ofs = (phase * math.pi * 2) / phase_max
            else:
                ofs = 0
            data = math.sin(((sample * 2.0 * math.pi * c_freqs[chan]) / sample_rate) + ofs)
            data *= scale
            data = int(data)
            write_u(f, data, sample_bytes)
        sample += 1
        continue

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_KP9, pygame.K_e):
                if r_mult < max_mult:
                    r_mult += 1
                gen_freqs()
            if event.key in (pygame.K_KP3, pygame.K_c):
                if r_mult > mult_scale:
                    r_mult -= 1
                gen_freqs()
            if event.key in (pygame.K_KP7, pygame.K_q):
                if l_mult < max_mult:
                    l_mult += 1
                gen_freqs()
            if event.key in (pygame.K_KP1, pygame.K_z):
                if l_mult > mult_scale:
                    l_mult -= 1
                gen_freqs()
            if event.key in (pygame.K_KP4, pygame.K_a):
                if phase > 0:
                    phase -= 1
                dump_freqs()
            if event.key in (pygame.K_KP6, pygame.K_d):
                if phase < phase_max:
                    phase += 1
                dump_freqs()
            if event.key in (pygame.K_x, ):
                running = False
                break

f.close()
