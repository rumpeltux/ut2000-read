# -*- coding: utf-8 -*-
from __future__ import division
import usb.core
import sys
import time
from .base import USBDevice


class UT2000(USBDevice):
    """
    UT2xxx series digital storage oscilloscopes
    """

    # List of supported devices
    # vendor id, product id, description
    devices = [
        (0x5656, 0x0832, 'UT2025B'),
        (0x5656, 0x0834, 'UT2102C')
    ]

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
    Y_SENSE_CH2 = Y_SENSE_CH1 + CH_OFFSET
    Y_POS_CH1 = 6
    Y_POS_CH2 = Y_POS_CH1 + CH_OFFSET
    Y_PROBE_CH1 = 19
    Y_PROBE_CH2 = Y_PROBE_CH1 + CH_OFFSET
    COUPLING_CH1 = 12
    COUPLING_CH2 = COUPLING_CH1 + CH_OFFSET
    X_SCALE_CH1 = 10
    X_SCALE_CH2 = 10 + CH_OFFSET
    X_CURSOR_CH1 = 11
    X_CURSOR_CH2 = 11 + CH_OFFSET
    BW_LIMIT_CH1 = 15
    BW_LIMIT_CH2 = 15 + CH_OFFSET
    INVERTED_CH1 = 9
    INVERTED_CH2 = 9 + CH_OFFSET

    class Endpoint(object):
        BULK_IN = 0x82

    class ReqType(object):
        VENDOR_REQUEST = 0x40
        RECIPIENT_ENDPOINT = 0x02
        DEVICE_TO_HOST = 0x80
        HOST_TO_DEVICE = 0x00

        CTRL_OUT = RECIPIENT_ENDPOINT | VENDOR_REQUEST | HOST_TO_DEVICE
        CTRL_IN = RECIPIENT_ENDPOINT | VENDOR_REQUEST | DEVICE_TO_HOST

    def __init__(self, device):
        super(UT2000, self).__init__(device)
        self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB1, 0x2C, 0)
        self.device.ctrl_transfer(self.ReqType.CTRL_IN, 0xB2, 0, 0, 8)

    def get_screenshot(self):
        buf = None
        for i in [0xF0] + [0x2C] * 10 + [0xCC] * 10 + [0xE2]:
            self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB1, i, 0)
        time.sleep(0.05)
        self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB0, 0, 38)
        try:
            for bufsize in [8192] * 4 + [6144]:
                buf = self.device.read(self.Endpoint.BULK_IN, bufsize)
        except usb.core.USBError:
            print >>sys.stderr, e
            print >>sys.stderr, 'Image transfer error, try again'
            sys.exit(1)
        finally:
            # leave 'far mode'
            self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB1, 0xF1, 0)
        return bug

    def get_data(self):
        for i in [0xF0] + [0x2C] * 10 + [0xDC] * 10 + [0xCC] * 10 + [0xE1]:
            self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB1, i, 0)
        time.sleep(0.05)
        self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB0, 0x01, 2)
        try:
            data = self.device.read(self.Endpoint.BULK_IN, 1024)
        except usb.core.USBError, e:
            print >>sys.stderr, e
            print >>sys.stderr, 'Data transfer error, try again'
            sys.exit(1)
        finally:
            # leave 'far mode'
            self.device.ctrl_transfer(self.ReqType.CTRL_OUT, 0xB1, 0xF1, 0)
        return data

    def get_samples(self, output_file):
        data = self.get_data()
        channels = [{}, {}]
        #channels[0]["header"] = data[0:32]
        #channels[1]["header"] = data[32:64]
        channels[0]["V_div"] = self.Y_RANGE[data[self.Y_SENSE_CH1]]*(10**(data[self.Y_PROBE_CH1]))
        channels[0]["V_div_index"] = data[self.Y_SENSE_CH1]
        channels[1]["V_div"] = self.Y_RANGE[data[self.Y_SENSE_CH2]]*(10**(data[self.Y_PROBE_CH2]))
        channels[1]["V_div_index"] = data[self.Y_SENSE_CH2]
        channels[0]["probe"] = 10**(data[self.Y_PROBE_CH1])
        channels[0]["probe_index"] = data[self.Y_PROBE_CH1]
        channels[1]["probe"] = 10**(data[self.Y_PROBE_CH2])
        channels[1]["probe_index"] = data[self.Y_PROBE_CH2]
        channels[0]["couple"] = self.COUPLING[data[self.COUPLING_CH1]]
        channels[1]["couple"] = self.COUPLING[data[self.COUPLING_CH2]]
        channels[0]["couple_index"] = data[self.COUPLING_CH1]
        channels[1]["couple_index"] = data[self.COUPLING_CH2]
        # save samples data to buffers
        if len(data) == 1024:
            channels[0]["samples"] = data[516:766].tolist()
            channels[1]["samples"] = data[770:1020].tolist()
        elif len(data) == 2560:
            channels[0]["samples"] = data[516:1266].tolist()
            channels[1]["samples"] = data[1520:2270].tolist()
        else:
            print >>sys.stderr, "Err: Unexcepted length of data sample, no data decoded then."
        channels[0]["s_div"] = self.X_RANGE[data[self.X_SCALE_CH1]]
        channels[0]["s_div_index"] = data[self.X_SCALE_CH1]
        channels[1]["s_div"] = self.X_RANGE[data[self.X_SCALE_CH2]]
        channels[1]["s_div_index"] = data[self.X_SCALE_CH2]
        channels[0]["active"] = bool(data[self.CHANNEL_STATE] & 0x01)
        channels[1]["active"] = bool(data[self.CHANNEL_STATE] & 0x02)
        channels[0]["y_offset"] = 0x7e - data[self.Y_POS_CH1]
        channels[1]["y_offset"] = 0x7e - data[self.Y_POS_CH2]
        channels[0]["Bw_limit"] = bool(data[self.BW_LIMIT_CH1])
        channels[1]["Bw_limit"] = bool(data[self.BW_LIMIT_CH2])
        channels[0]["inverted"] = bool(data[self.INVERTED_CH1])
        channels[1]["inverted"] = bool(data[self.INVERTED_CH2])
        channels[0]["x_offset"] = data[self.X_CURSOR_CH1]
        channels[1]["x_offset"] = data[self.X_CURSOR_CH2]
        channels[0]["x_poz"] = (data[8] << 8) + data[7]
        channels[1]["x_poz"] = (data[40] << 8) + data[39]

        # Convert binary reading to voltage
        for channel in channels:
            channel["samples_volt"] = [((y-channel["y_offset"])/255 - 0.5)*channel["V_div"]*10 for y in channel["samples"]]
            channel["sample_period"] = channel["s_div"] * 10
            channel["s_offset"] = channel["x_offset"]/255 * channel["s_div"]

        return channels
