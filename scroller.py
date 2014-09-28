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
seconds = 6 * 60 * 60 # can go up to a little over 6 hours

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

def draw_A(i):
    if i < 20:
        return lerp2d(0.5, 1, 1, 0, i, 19)
    elif i < 40:
        return lerp2d(0, 0, 0.5, 1, i - 20, 19)
    else:
        return lerp2d(0.25, 0.5, 0.75, 0.5, (i - 40), 7)

def draw_D(i):
    if i < 16:
        return lerp2d(0, 0, 0, 1, i, 15)
    else:
        return arc(0, 0.5, 15, 0, 31, 0.75, 0.5, i, 31)

def draw_E(i):
    if i < 10:
        return lerp2d(0.75, 1, 0, 1, i, 9)
    elif i < 28:
        return lerp2d(0, 1, 0, 0, i - 10, 17)
    elif i < 38:
        return lerp2d(0, 0, 0.75, 0, i - 28, 9)
    else:
        return lerp2d(0, 0.5, 0.75, 0.5, i - 38, 9)

def draw_N(i):
    if i < 16:
        return lerp2d(0, 0, 0, 1, i, 15)
    elif i < 32:
        return lerp2d(0, 1, 0.75, 0, (i - 16), 15)
    else:
        return lerp2d(0.75, 0, 0.75, 1, (i - 32), 15)

def draw_L(i):
    if i < 36:
        return lerp2d(0, 1, 0, 0, i, 35)
    else:
        return lerp2d(0, 0, 0.75, 0, i - 36, 11)

def draw_O(i):
    return arc(0.5, 0.5, 0, 1, 1, 0.5, 0.5, i, 47)

def draw_V(i):
    if i < 24:
        return lerp2d(0.5, 0, 1, 1, i, 23)
    else:
        return lerp2d(0, 1, 0.5, 0, i - 24, 23)

def draw_C(i):
    return arc(0.5, 0.5, 45, 325, 360, 0.5, 0.5, i, 47)

def draw_S(i):
    if i < 24:
        return arc(0.75 / 2, 0.75, 0, 270, 360, 0.75 / 2, 0.25, i, 23)
    else:
        return arc(0.75 / 2, 0.25, 90, -180, 360, 0.75 / 2, 0.25, i - 24, 23)

def draw_a(i):
    if i < 36:
        return arc(0.25, 0.25, 0, 1, 1, 0.25, 0.25, i, 35)
    else:
        return lerp2d(0.5, 0.45, 0.5, 0, i - 36, 11)

def draw_c(i):
    return arc(0.25, 0.25, 45, 325, 360, 0.25, 0.25, i, 47)

def draw_e(i):
    if i < 36:
        return arc(0.25, 0.25, 0, 315, 360, 0.25, 0.25, i, 35)
    else:
        return lerp2d(0, 0.25, 0.5, 0.25, i - 36, 11)

def draw_o(i):
    return arc(0.25, 0.25, 0, 1, 1, 0.25, 0.25, i, 47)

def draw_p(i):
    if i < 24:
        return arc(0.25, 0.25, 0, 1, 1, 0.25, 0.25, i, 23)
    else:
        return lerp2d(0, 0.5, 0, -0.5, i - 24, 23)

def draw_r(i):
    if i < 12:
        return arc(0.25, 0.25, 45, 180, 360, 0.25, 0.25, i, 11)
    else:
        return lerp2d(0, 0, 0, 0.5, i - 12, 35)

def draw_t(i):
    if i < 12:
        return lerp2d(0, 0.65, 0.5, 0.65, i, 11)
    else:
        return lerp2d(0.25, 0, 0.25, 1, i - 12, 35)

def draw_SPACE(i):
    return 0.5, 0.5

char_width = 1.2
font_scale = 0.2
s = 'LOVELAND CreatorSpace   '

IX_FUNC = 0
IX_ITERS = 1
IX_WIDTH = 2
chmap = {
    'A': (draw_A, 48, char_width),
    'C': (draw_C, 48, char_width),
    'D': (draw_D, 48, char_width * 0.75),
    'E': (draw_E, 48, char_width * 0.75),
    'L': (draw_L, 48, char_width * 0.75),
    'N': (draw_N, 48, char_width * 0.75),
    'O': (draw_O, 48, char_width),
    'S': (draw_S, 48, char_width * 0.75),
    'V': (draw_V, 48, char_width),
    'a': (draw_a, 48, char_width * 0.5),
    'c': (draw_c, 48, char_width * 0.5),
    'e': (draw_e, 48, char_width * 0.5),
    'o': (draw_o, 48, char_width * 0.5),
    'p': (draw_p, 48, char_width * 0.5),
    'r': (draw_r, 48, char_width * 0.5),
    't': (draw_t, 48, char_width * 0.5 * 0.9),
    ' ': (draw_SPACE, 48, char_width),
}


first_sindex = 0
first_xo = scale
cur_yo = -font_scale * 0.5 * scale
init_line = True
init_ch = True
for i in xrange(sample_count):
    if init_line:
        cur_sindex = first_sindex
        cur_xo = first_xo
        init_line = False
    if init_ch:
        cur_iter = 0
        cur_ch = chmap[s[cur_sindex]]
        init_ch = False

    x_ch, y_ch = cur_ch[IX_FUNC](cur_iter * 1.0)

    x = cur_xo + x_ch * font_scale * scale
    y = cur_yo + y_ch * font_scale * scale

    # FIXME: Need much better clipping than this!
    if x < -scale:
        x = -scale
    if x > scale:
        x = scale

    data = struct.pack('<hh', y, x)
    f.write(data)

    cur_iter += 1
    if cur_iter == cur_ch[IX_ITERS]:
        init_ch = True
        cur_xo += cur_ch[IX_WIDTH] * font_scale * scale
        cur_sindex += 1
        if cur_sindex == len(s):
            cur_sindex = 0
        if cur_xo <= -scale:
            first_sindex = cur_sindex
            first_xo = cur_xo
        if cur_xo >= scale:
            first_xo -= 100
            init_line = True

f.close()
