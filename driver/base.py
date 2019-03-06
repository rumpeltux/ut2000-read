# -*- coding: utf-8 -*-
import usb.core


class USBDevice(object):
    def __init__(self, device):
        self.device = device
        self.device.default_timeout = 1000
        self.device.set_configuration()

    def __del__(self):
        usb.util.dispose_resources(self.device)
