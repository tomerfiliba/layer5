import time
from struct import Struct
from .base import BaseChannel, ChannelSendError, ChannelRecvError


class PrefixedLengthChannel(BaseChannel):
    HEADER = None
    FRAME_LIMIT = None
    
    def _send(self, data, timeout):
        if self.FRAME_LIMIT and len(data) > self.FRAME_LIMIT:
            raise ChannelSendError("frame too long")
        header = self.HEADER.pack(len(data))
        return self.stream.write(header + data, timeout)

    def _recv(self, timeout):
        timeout, header = self.stream.read(self.HEADER.size, timeout)
        if self.FRAME_LIMIT and length > self.FRAME_LIMIT:
            raise ChannelRecvError("frame too long")
        length, = self.HEADER.unpack(header)
        return self.stream.read(length, timeout)

class Int16Channel(PrefixedLengthChannel):
    HEADER = Struct("!H")

class Int32Channel(PrefixedLengthChannel):
    HEADER = Struct("!L")

def LimitedInt16Channel(limit):
    return type("Int16Channel<%d>" % (limit,), (Int16Channel,), {"FRAME_LIMIT" : limit})








