# The MIT License (MIT)
#
# Copyright (c) 2017 Scott Shawcroft for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import struct
from . import core


class EndpointDescriptor(core.Descriptor):
    """Single endpoint configuration"""
    fields = [('bEndpointAddress', "B", None),
              ('bmAttributes', "B", None),
              ('wMaxPacketSize', "H", 0x40),
              ('bInterval', "B", 0)]

    bLength = 0x07
    bDescriptorType = 0x5

    TYPE_CONTROL = 0b00
    TYPE_ISOCHRONOUS = 0b01
    TYPE_BULK = 0b10
    TYPE_INTERRUPT = 0b11

    DIRECTION_IN =  0x80
    DIRECTION_OUT = 0x00

    @property
    def bEndpointAddress(self):
        return self.data[0]

    @bEndpointAddress.setter
    def bEndpointAddress(self, value):
        self.data[0] = value


class InterfaceDescriptor(core.Descriptor):
    """Single interface that includes ``subdescriptors`` such as endpoints.

    ``subdescriptors`` can also include other class and vendor specific
    descriptors. They are serialized in order after the `InterfaceDescriptor`.
    """
    fields = [('bInterfaceNumber', "B", 0),
              ('bAlternateSetting', "B", 0),
              ('bNumEndpoints', "B", 0),
              ('bInterfaceClass', "B", None),
              ('bInterfaceSubClass', "B", 0),
              ('bInterfaceProtocol', "B", 0),
              ('iInterface', "B", 0)]

    bLength = 0x09
    bDescriptorType = 0x4

    def __init__(self, *args, **kwargs):
        self.subdescriptors = []
        if "subdescriptors" in kwargs:
            self.subdescriptors = kwargs["subdescriptors"]
        super().__init__(*args, **kwargs)

    def __bytes__(self):
        endpoint_count = 0
        subdescriptor_bytes = []
        for desc in self.subdescriptors:
            subdescriptor_bytes.append(bytes(desc))
            if desc.bDescriptorType == EndpointDescriptor.bDescriptorType:
                endpoint_count += 1
        subdescriptor_bytes = b"".join(subdescriptor_bytes)
        self.data[2] = endpoint_count
        return super().__bytes__() + subdescriptor_bytes

    @property
    def bInterfaceNumber(self):
        return self.data[0]

    @bInterfaceNumber.setter
    def bInterfaceNumber(self, value):
        self.data[0] = value


class InterfaceAssociationDescriptor(core.Descriptor):
    """Groups interfaces into a single function"""
    fields = [('bFirstInterface', "B", None),
              ('bInterfaceCount', "B", None),
              ('bFunctionClass', "B", None),
              ('bFunctionSubClass', "B", None),
              ('bFunctionProtocol', "B", None),
              ('iFunction', "B", 0)]

    bLength = 0x08
    bDescriptorType = 0xB


class ConfigurationDescriptor(core.Descriptor):
    """High level configuration that prepends the interfaces."""
    fields = [('wTotalLength', "H", None),
              ('bNumInterfaces', "B", None),
              ('bConfigurationValue', "B", 0x1),
              ('iConfiguration', "B", 0),
              # bus powered (bit 6), no remote wakeup (bit 5),
              # bit 7 is always 1 and 0-4 are always 0
              ('bmAttributes', "B", 0x80),
              # 100 mA by default
              ('bMaxPower', "B", 50)]

    bLength = 0x09
    bDescriptorType = 0x2


class DeviceDescriptor(core.Descriptor):
    """Holds basic device level info.
    """
    fields = [('bcdUSB', "H", 0x200),
              ('bDeviceClass', "B", 0xef),
              ('bDeviceSubClass', "B", 0x02),
              ('bDeviceProtocol', "B", 0x01),
              ('bMaxPacketSize0', "B", 0x40),
              ('idVendor', "H", None),
              ('idProduct', "H", None),
              ('bcdDevice', "H", 0x100),
              ('iManufacturer', "B", None),
              ('iProduct', "B", None),
              ('iSerialNumber', "B", None),
              ('bNumConfigurations', "B", 1)]

    bLength = 0x12
    bDescriptorType = 0x1


class StringDescriptor:
    """Holds a string referenced by another descriptor by index.

       Its recommended to hold these in a list and use ``index`` in subsequent
       descriptors to link to them.
    """
    def __init__(self, value):
        if type(value) == str:
            self._bString = value.encode("utf-16-le")
            self._bLength = len(self._bString) + 2
        elif len(value) > 1:
            self._bLength = value[0]
            if value[1] != 3:
                raise ValueError("Sequence not a StringDescriptor")
            self._bString = value[2:2+self.bLength]

    def __bytes__(self):
        return struct.pack("BB{}s".format(len(self._bString)), self.bLength,
                           self.bDescriptorType, self._bString)

    @property
    def bString(self):
        return self._bString.decode("utf-16-le")

    @bString.setter
    def bString(self, value):
        self._bString = value.encode("utf-16-le")
        self._bLength = len(self.encoded) + 2

    @property
    def bDescriptorType(self):
        return 3

    @property
    def bLength(self):
        return self._bLength
