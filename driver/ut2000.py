# -*- coding: utf-8 -*-
from __future__ import division
import usb.core
import sys
import time
from PIL import Image
import numpy as np
from .base import USBDevice
from . import colormaps
   
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
    
class AbstractUT2000(USBDevice):
    """
    UT2xxx series digital storage oscilloscopes
    """

    # ------------------------
    # Data parsing definitions
    Y_RANGE = [2E-3, 5E-3, 10E-3, 20E-3, 50E-3, 100E-3, 200E-3, 500E-3, 1, 2, 5]
    X_RANGE = [0, 25E-10, 5E-9, 10E-9, 20E-9, 50E-9, 100E-9, 200E-9, 500E-9, 1E-6,
               2E-6, 5E-6, 10E-6, 20E-6, 50E-6, 100E-6, 200E-6, 500E-6, 1E-3, 2E-3,
               5E-3, 10E-3, 20E-3, 50E-3, 100E-3, 200E-3, 500E-3, 1, 2, 5, 10, 20, 50]
    COUPLING = ["DC", "AC", "GND"]

    CHANNEL_STATE = 2
    CH_OFFSET = 32
    Y_SENSE = 5
    Y_POS = 6
    Y_PROBE = 19
    COUPLING = 12
    X_SCALE = 10
    X_CURSOR = 11
    BW_LIMIT = 15
    INVERTED = 9

    # The 0 reference value in the uint8 sample data.
    SAMPLE_BASE = 128
    
    def __init__(self, device):
        super().__init__(device)
        self.connect()
    
    def connect(self):
        pass
    
    def send_command(self, code: int, timeout_millis: int = 0):
        """Device specific implementation to send a command code."""
        raise NotImplementedError()
    
    def attach(self):
        """Enter remote control mode (may disable the on-device UI)"""
        self.send_command(0xf0)
        
    def detach(self):
        """Leave remote control mode."""
        self.send_command(0xf1)

    def get_screenshot(self, **kwargs):
        """Acquire and decode a screenshot. See also #decode_screenshot."""
        buf = self.get_raw_screenshot()
        return self.decode_screenshot(buf, **kwargs)
        
    def get_raw_screenshot(self):
        self.send_command(0xe2)
        self._prepare_get_screenshot()
        # The device sometimes sends an additional 64-byte header.
        # We read the screenshot with a very long timeout to give the device enough time to process.
        buf = self.device.read(Endpoint.BULK_IN, self._screenshot_size(), timeout=1000)
        try:
          # If there’s trailing data, read that as well, short timeout this time.
          buf2 = self.device.read(Endpoint.BULK_IN, 64, timeout=50)
        except usb.core.USBError:  # [Errno 110] Operation timed out
          return buf
        return buf[64:] + buf2

    def decode_screenshot(self, buf, colormap=colormaps.simple):
        """decodes the screenshot as sent by the device."""
        width, height = self.SCREEN_RESOLUTION
        img = Image.new('RGB', (width, height))
        x, y = 0, 0
        for pos in range(0, self._screenshot_size(), 2):
          # bytes '\xAB\xCD' results in pixels C, D, A, B
          value = buf[pos:pos+2]
          for binval in reversed(value):
            for half in (binval >> 4, binval & 0x0f):
              color = colormap[half]
              img.putpixel((x, y), color)
              x += 1
              if x == width:
                  x = 0
                  y += 1
        return img

    def _prepare_get_screenshot(self):
        """Additional commands etc to send before acquiring a screenshot."""
        pass
    
    def _screenshot_size(self):
        return self.SCREEN_RESOLUTION[0] * self.SCREEN_RESOLUTION[1] // 2
    
    def get_data_raw(self):
        """Reads the recorded samples and metadata. Returns the raw buffer."""
        self.send_command(0xe1)
        self._prepare_get_data()
        buf = self.device.read(Endpoint.BULK_IN, 2560, timeout=200)
        return buf
    
    def _prepare_get_data(self):
        """Additional commands etc to send before reading samples."""
        pass
    
    def parse_header(self, header, channel):
        """channel is 0 or 1"""
        return dict(
            V_div=self.Y_RANGE[header[self.Y_SENSE]]*(10**(header[self.Y_PROBE])),
            V_div_index=header[self.Y_SENSE],
            probe=10**(header[self.Y_PROBE]),
            probe_index=header[self.Y_PROBE],
            couple=self.COUPLING[header[self.COUPLING]],
            couple_index=header[self.COUPLING],
            s_div=self.X_RANGE[header[self.X_SCALE]],
            s_div_index=header[self.X_SCALE],
            active=bool(header[self.CHANNEL_STATE] & (1 << channel)),
            y_offset=0x7e - header[self.Y_POS],
            Bw_limit=bool(header[self.BW_LIMIT]),
            inverted=bool(header[self.INVERTED]),
            x_offset=header[self.X_CURSOR],
            x_poz=(header[8] << 8) + header[7],
        )
    
    def get_samples(self):
        """Reads the recorded samples and parses metadata. Return a dict per channel."""
        data = self.get_data()
        channels = [self.parse_header(data[:0x20], 0),
                    self.parse_header(data[0x20:0x40], 1)]

        # Convert binary reading to voltage
        for i, channel in enumerate(channels):
            raw_samples = self.get_raw_samples(data, i)
            if raw_samples:
                raw_samples = np.array(raw_samples, np.uint8)
                channel['samples'] = raw_samples
                channel["samples_volt"] = (
                    raw_samples.astype(np.float) - self.SAMPLE_BASE) / 256 * channel['V_div'] * 10
            channel["sample_period"] = channel["s_div"] * 10
            channel["s_offset"] = channel["x_offset"]/255 * channel["s_div"]

        return channels
    
    def get_raw_samples(self, data, channel):
        """Device specific logic to extract the sample array from the data buffer."""
        raise NotImplementedError()

class UT2052CEL(AbstractUT2000):
    SCREEN_RESOLUTION = (400, 240)
    Y_RANGE = [0] + AbstractUT2000.Y_RANGE

    def get_data_raw(self):
        buf = super().get_data_raw()
        # Sometimes the device doesn't send the header. Just try again.
        if len(buf) != 704:
          print('Warning: Did receive incomplete data (length=%d)' % len(buf), file=sys.stderr)
          return self.get_data_raw()
        return buf

    def send_command(self, code: int, timeout_millis: int = 0):
        self.device.write(Endpoint.BULK_OUT, bytearray([code]), timeout_millis)
        
    def get_raw_screenshot(self):
        return super().get_raw_screenshot()[0x80:]  # strip the header

    def get_raw_samples(self, data, channel):
        data = data[0x40:]  # strip the header
        samples = len(data)//2
        garbage_size = 20
        # Contains 2x320 bytes of data. The last 20 bytes of each channel are
        # always filled with '\xff\x00' though.
        return (data[:samples] if channel == 0 else data[samples:])[:-garbage_size]


class UT2025B(AbstractUT2000):
    SCREEN_RESOLUTION = (320, 240)
    SAMPLE_BASE = 130

    def connect(self):
        self.send_command( 0x2C, 0)
        self.device.ctrl_transfer(ReqType.CTRL_IN, 0xB2, 0, 0, 8)

    def send_command(self, code: int, timeout_millis: int = 0):
        self.device.ctrl_transfer(ReqType.CTRL_OUT, 0xB1, code, timeout_millis)

    def attach(self):
        super().attach()
        for i in [0x2C] * 10 + [0xCC] * 10:
            self.send_command(i)

    def _prepare_get_screenshot(self):
        time.sleep(0.05)
        self.device.ctrl_transfer(ReqType.CTRL_OUT, 0xB0, 0, 38)

    def _prepare_get_data(self):
        time.sleep(0.05)
        self.device.ctrl_transfer(ReqType.CTRL_OUT, 0xB0, 0x01, 2)
        
    def get_raw_samples(self, data, channel):
        if len(data) == 1024:
            return data[516:766] if channel == 0 else data[770:1020]
        elif len(data) == 2560:
            return data[516:1266] if channel == 0 else data[1520:2270]
        else:
            print('data =', repr(data), file=sys.stderr)
            raise RuntimeError("Unexcepted length of data sample (%d), no data decoded then." % len(data))

def open():
    """scans for supported devices and returns an instance if found."""
    devices = [
        (0x5656, 0x0832, UT2025B),
        (0x5656, 0x0834, UT2025B), # UT2102C
        (0x4348, 0x5537, UT2052CEL)
    ]
    for vendor, product, cls in devices:
        dev = usb.core.find(idVendor=vendor, idProduct=product)
        if dev:  # Found a device
            return cls(dev)
