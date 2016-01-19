#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# pd2pdf.py - converts a UT2000 series scope screenshot to PNG
#
# Copyright (c) 2011 András Veres-Szentkirályi and contributors
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from __future__ import with_statement, division
import argparse
from PIL import Image
import sys
import os


parser = argparse.ArgumentParser(description='Convert raw data from scope to png')
parser.add_argument('input', help='Path to binary input file. Pass - for stdin',
                    type=argparse.FileType('r'))
parser.add_argument('output', help='Path to png output file',
                    type=argparse.FileType('w'))
parser.add_argument('--colormap', dest='colormap', default='colormaps/simple.txt',
                    help='Path to colormap file')
parser.add_argument('--magnify', dest='magnify',
                    default=1, type=int, metavar='N',
                    help='Magnification factor (nearest neighbour resampling)')

args = parser.parse_args()

with file(args.colormap, 'r') as colormap_file:
    COLORMAP = [tuple(int(i) for i in row.split(',')) for row in colormap_file]


WIDTH, HEIGHT = 320, 240

img = Image.new('RGB', (WIDTH, HEIGHT))

#if not args.input:
#    args.input = sys.stdin

try:
    x, y = 0, 0
    for _ in xrange(WIDTH * HEIGHT // 4):
        value = args.input.read(2)
        for binval in reversed([ord(ch) for ch in value]):
            for half in (binval >> 4, binval & 0x0f):
                color = COLORMAP[half]
                img.putpixel((x, y), color)
                x += 1
                if x == WIDTH:
                    x = 0
                    y += 1
finally:
    img = img.resize((WIDTH * args.magnify, HEIGHT * args.magnify), resample=Image.NEAREST)
    if args.output is sys.stdout:
        print img
    else:
        img.save(args.output)
