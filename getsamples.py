#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
from driver.ut2000 import UT2000

dev = UT2000.discover_device()
if dev is None:
    print >>sys.stderr, 'USB device cannot be found, check connection'
    sys.exit(1)

channels = dev.get_samples(sys.stdout)
print json.dumps(channels, sort_keys=True, indent=4)
