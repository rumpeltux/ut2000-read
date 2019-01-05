#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# getshot.py - gets a single screenshot from an UT2000 series scope
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

import usb.core
import sys

"""
List of supported USB devices
    vendor id, product id, description
"""
devices = [
    (0x5656, 0x0832, 'UT2025B'),
    (0x5656, 0x0834, 'UT2102C'),
    (0x4348, 0x5537, 'UT2052CEL')
]


class Endpoint(object):
    BULK_IN = 0x82
    BULK_OUT = 2


class ReqType(object):
    VENDOR_REQUEST = 0x40
    RECIPIENT_ENDPOINT = 0x02
    DEVICE_TO_HOST = 0x80
    HOST_TO_DEVICE = 0x00

    CTRL_OUT = RECIPIENT_ENDPOINT | VENDOR_REQUEST | HOST_TO_DEVICE
    CTRL_IN = RECIPIENT_ENDPOINT | VENDOR_REQUEST | DEVICE_TO_HOST


for device in devices:
    dev = usb.core.find(idVendor=device[0], idProduct=device[1])
    if dev:  # Found a device
        break

if dev is None:
    print >>sys.stderr, 'USB device cannot be found, check connection'
    sys.exit(1)
    
def send_control_command(value):
    if 0:
        dev.ctrl_transfer(ReqType.CTRL_OUT, 177, i, 0)
    else:
        dev.write(Endpoint.BULK_OUT, bytearray([value]))

dev.set_configuration()

if 0:
    dev.ctrl_transfer(ReqType.CTRL_OUT, 177, 0x2C, 0)
    dev.ctrl_transfer(ReqType.CTRL_IN, 178, 0, 0, 8)
else:
    send_control_command(0xe2)
#for i in [0xF0] + [0x2C] * 10 + [0xCC] * 10 + [0xE2]:
#    send_control_command(i)
    #dev.ctrl_transfer(ReqType.CTRL_OUT, 177, i, 0)

try:
    if 0:
        dev.ctrl_transfer(ReqType.CTRL_OUT, 176, 0, 38)
    for bufsize in [4096] * 11 + [3008]:
        buf = dev.read(Endpoint.BULK_IN, bufsize, 100)
        buf.tofile(sys.stdout)
    send_control_command(0xf1)
except usb.core.USBError:
    print >>sys.stderr, 'Image transfer error, try again'
    sys.exit(1)
