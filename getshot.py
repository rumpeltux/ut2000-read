#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# getshot.py - gets a single screenshot from an UT2000 series scope

import sys
import driver.ut2000

parser = argparse.ArgumentParser(description='Convert raw data from scope to png')
parser.add_argument('--colormap', dest='colormap', default='simple',
                    help='Which colormap to use')
parser.add_argument('--magnify', dest='magnify',
                    default=2, type=int, metavar='N',
                    help='Magnification factor (nearest neighbour resampling)')

args = parser.parse_args()
dev = driver.ut2000.open()
if dev is None:
    print('USB device cannot be found, check connection', file=sys.stderr)
    sys.exit(1)
dev.attach()
img = dev.get_screenshot()
img = img.resize((WIDTH * args.magnify, HEIGHT * args.magnify), resample=Image.NEAREST)
img.save(sys.stdout.buffer)
dev.detach()
