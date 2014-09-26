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

sample_rate = 48000
channels = 2
sample_bits = 16
seconds = 10 * 60

sample_bytes = sample_bits / 8
scale = (2 ** (sample_bits - 1)) - 1
sample_count = sample_rate * seconds

f = open('/dev/stdout', 'wb')

header_len = 18
data_len = sample_count * channels * sample_bytes

# It'd be nice to use the wave module in write mode, but that wants to seek
# the file, which doesn't work too well with stdout.
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

def lerp2d(x0, y0, x1, y1, i, n):
    f = i / n
    x = x0 + f * (x1 - x0)
    y = y0 + f * (y1 - y0)
    return x, y

def arc(x0, y0, sa, ea, na, w, h, i, n):
    f = i / n
    a = (sa + (f * (ea - sa))) / na
    a *= 2 * math.pi
    x = x0 + w * math.cos(a)
    y = y0 + h * math.sin(a)
    return x, y

def draw_L(i):
    if chi < 36:
        return lerp2d(-1, 1, -1, -1, i, 35)
    else:
        return lerp2d(-1, -1, 1, -1, i - 36, 11)

def draw_O(i):
    return arc(0, 0, 0, 1, 1, 1, 1, i, 47)

def draw_V(i):
    if i < 24:
        return lerp2d(-1, 1, 0, -1, i, 23)
    else:
        return lerp2d(0, -1, 1, 1, (i - 24), 23)

def draw_E(i):
    if i < 10:
        return lerp2d(1, 1, -1, 1, i, 9)
    elif i < 28:
        return lerp2d(-1, 1, -1, -1, i - 10, 17)
    elif i < 38:
        return lerp2d(-1, -1, 1, -1, i - 28, 9)
    else:
        return lerp2d(-1, 0, 1, 0, i - 38, 9)

def draw_A(i):
    if i < 20:
        return lerp2d(0, 1, 1, -1, i, 19)
    elif i < 40:
        return lerp2d(-1, -1, 0, 1, i - 20, 19)
    else:
        return lerp2d(-0.5, 0, 0.5, 0, (i - 40), 7)

def draw_N(i):
    if i < 16:
        return lerp2d(-1, -1, -1, 1, i, 15)
    elif i < 32:
        return lerp2d(-1, 1, 1, -1, (i - 16), 15)
    else:
        return lerp2d(1, -1, 1, 1, (i - 32), 15)

def draw_D(i):
    if i < 16:
        return lerp2d(-1, -1, -1, 1, i, 15)
    else:
        return arc(-1, 0, 15, 0, 31, 2, 1, i, 31)

s = 'LOVELAND'
chmap = {
    'A': draw_A,
    'D': draw_D,
    'E': draw_E,
    'L': draw_L,
    'N': draw_N,
    'O': draw_O,
    'V': draw_V,
}

xo = scale
yo = 0
xoch = 0

for i in xrange(sample_count):
    chn = (i / 48) % 8
    chi = float(i % 48)

    if chi == 0:
        xoch += 0.12 * 2 * scale
    if chn == 0 and chi == 0:
        xoch = 0
    if chn == 0 and chi == 0:
        xo -= 100
    if chn == 7 and chi == 47:
        if xo + xoch < -scale:
            xo = scale

    x, y = chmap[s[chn]](chi)

    x *= 0.1 * scale
    y *= 0.1 * scale
    x += xo + xoch
    y += yo

    # FIXME: Need much better clipping than this!
    if x < -scale:
        x = -scale
    if x > scale:
        x = scale

    data = struct.pack('<hh', y, x)
    f.write(data)

f.close()
