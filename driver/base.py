# -*- coding: utf-8 -*-
import usb.core


class USBDevice(object):
    def __init__(self, device):
        self.device = device
        self.device.default_timeout = 1000
        self.device.set_configuration()

    @classmethod
    def discover_device(cls):
        for device in cls.devices:
            dev = usb.core.find(idVendor=device[0], idProduct=device[1])
            if dev:  # Found a device
                break
        if dev:
            return cls(dev)
        else:
            return None
