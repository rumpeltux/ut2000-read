Python driver for UNI-T UT2000 series digital oscilloscopes
===========================================================

Fork from [dnet/ut2025b](https://github.com/dnet/ut2025b). [Original website](http://hsbp.org/ut2025b)

Support
-------

Tested with

- UT2052CEL

Should also work with:
- UT2025B
- UT2102C

Probably compatible with other UT2000 series devices as well.

Setup
-----

- Install PyUSB 1.0 (https://github.com/walac/pyusb)
- Install PIL

Usage
-----

* Connect the scope via USB
* python getshot.py > foo.png

You should do this as root / Administrator as it manipulates USB directly.
In case of an "Image transfer error, try again" message, just keep trying,
after a few attempts it starts to work and continues to do so, as long as the
scope is connected to the PC.

Check `python getshot.py -h` for optional parameters. You can specify a colormap which transforms
the 4-bit image to RGB values. The default is a simple color map with light background,
but the format is straightforward enought for everyone to create new and better ones (see driver/colormaps.py).

License
-------

The whole project is licensed under MIT license.

Dependencies
------------

 - Python 2.x (tested with 2.7)
 - PyUSB 1.0 (http://sourceforge.net/projects/pyusb/)
