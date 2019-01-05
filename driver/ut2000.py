# -*- coding: utf-8 -*-
from __future__ import division
import usb.core
import sys
import time
import numpy as np
from .base import USBDevice
   
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
    X_OFFSET_NULL = 3803
    DATA_CH1 = 0xf9
    DATA_CH2 = 0xfa
    GET_WAVE = 0x06
    Y_RANGE = [2E-3, 5E-3, 10E-3, 20E-3, 50E-3, 100E-3, 200E-3, 500E-3, 1, 2, 5]
    X_RANGE = [0, 25E-10, 5E-9, 10E-9, 20E-9, 50E-9, 100E-9, 200E-9, 500E-9, 1E-6,
               2E-6, 5E-6, 10E-6, 20E-6, 50E-6, 100E-6, 200E-6, 500E-6, 1E-3, 2E-3,
               5E-3, 10E-3, 20E-3, 50E-3, 100E-3, 200E-3, 500E-3, 1, 2, 5, 10, 20, 50]
    COUPLING = ["DC", "AC", "GND"]
    CHANNEL_STATE = 2
    CH_OFFSET = 32
    Y_SENSE_CH1 = 5
    Y_POS_CH1 = 6
    Y_PROBE_CH1 = 19
    COUPLING_CH1 = 12
    X_SCALE_CH1 = 10
    X_CURSOR_CH1 = 11
    BW_LIMIT_CH1 = 15
    INVERTED_CH1 = 9
    
    def __init__(self, device):
        super().__init__(device)
        self.connect()
    
    def connect(self):
        pass
    
    def send_command(self, command, timeout=0):
        raise NotImplementedError()
    
    def attach(self):
        self.send_command(0xf0)
        
    def detach(self):
        self.send_command(0xf1)
    
    def get_screenshot(self):
        self.attach()
        self.send_command(0xe2)
        self._prepage_get_screenshot()
        buf = self.device.read(Endpoint.BULK_IN, self._screenshot_size(),
                               timeout=1000)
        self.detach()
        return buf
    
    def _prepare_get_screenshot(self):
        pass
    
    def _screenshot_size(self):
        return self.SCREEN_RESOLUTION[0] * self.SCREEN_RESOLUTION[1] / 2
    
    def get_data(self):
        self.attach()
        self.send_command(0xe1)
        self._prepare_get_data()
        buf = self.device.read(Endpoint.BULK_IN, 2560, timeout=200)
        self.detach()
        return buf
    
    def _prepare_get_data(self):
        pass
    
    def parse_header(self, header, channel):
        """channel is 0 or 1"""
        return dict(
            V_div= self.Y_RANGE[header[self.Y_SENSE_CH1]]*(10**(header[self.Y_PROBE_CH1])),
            V_div_index = header[self.Y_SENSE_CH1],
            probe = 10**(header[self.Y_PROBE_CH1]),
            probe_index = header[self.Y_PROBE_CH1],
            couple = self.COUPLING[header[self.COUPLING_CH1]],
            couple_index= header[self.COUPLING_CH1],
            s_div = self.X_RANGE[header[self.X_SCALE_CH1]],
            s_div_index = header[self.X_SCALE_CH1],
            active= bool(header[self.CHANNEL_STATE] & (1 << channel)),
            y_offset = 0x7e - header[self.Y_POS_CH1],
            Bw_limit = bool(header[self.BW_LIMIT_CH1]),
            inverted = bool(header[self.INVERTED_CH1]),
            x_offset = header[self.X_CURSOR_CH1],
            x_poz = (header[8] << 8) + header[7],
        )
    
    def get_samples(self):
        data = self.get_data()
        channels = [self.parse_header(data[:0x20], 0),
                    self.parse_header(data[0x20:0x40], 1)]

        # Convert binary reading to voltage
        for i, channel in enumerate(channels):
            raw_samples = self.get_raw_samples(data, i)
            print(repr(raw_samples))
            if raw_samples:
                raw_samples = np.array(raw_samples, np.uint8)
                channel['samples'] = raw_samples
                channel["samples_volt"] = (
                    raw_samples.astype(np.float) - 130) / 256 * channel['V_div'] * 10
                # TODO the other class uses different values
            channel["sample_period"] = channel["s_div"] * 10
            channel["s_offset"] = channel["x_offset"]/255 * channel["s_div"]

        return channels
    
    def get_raw_samples(self, data, channel):
        raise NotImplementedError()

class UT2052CEL(AbstractUT2000):
    SCREEN_RESOLUTION = (400, 240)
    Y_RANGE = [0] + AbstractUT2000.Y_RANGE

    def send_command(self, command, timeout=0):
        self.device.write(Endpoint.BULK_OUT, bytearray([command]), timeout)
    
    def _prepare_screenshot(self):
        metadata = self.device.read(Endpoint.BULK_IN, 64, timeout=100)
        
    def get_raw_samples(self, data, channel):
        data = data[0x40:]  # strip the header
        samples = len(data)//2
        garbage_size = 20
        return (data[:samples] if channel == 0 else data[samples:])[:-garbage_size]


class UT2025B(AbstractUT2000):
    SCREEN_RESOLUTION = (320, 240)

    def connect(self):
        self.send_command( 0x2C, 0)
        self.device.ctrl_transfer(ReqType.CTRL_IN, 0xB2, 0, 0, 8)

    def send_command(self, command, timeout=0):
        self.device.ctrl_transfer(ReqType.CTRL_OUT, 0xB1, command, timeout)
    
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
    devices = [
        (0x5656, 0x0832, UT2025B),
        (0x5656, 0x0834, UT2025B), # UT2102C
        (0x4348, 0x5537, UT2052CEL)
    ]
    for vendor, product, cls in devices:
        dev = usb.core.find(idVendor=vendor, idProduct=product)
        if dev:  # Found a device
            return cls(dev)
