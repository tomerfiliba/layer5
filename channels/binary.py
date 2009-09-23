import time
from struct import Struct
from .base import BaseChannel, ChannelSendError, ChannelRecvError


class PrefixedLengthChannel(BaseChannel):
    HEADER = None
    FRAME_LIMIT = None
    
    def send(self, data, timeout):
        if self.FRAME_LIMIT and len(data) > self.FRAME_LIMIT:
            raise ChannelSendError("frame too long")
        header = self.HEADER.pack(len(data))
        self.stream.write(header + data, timeout)

    def recv(self, timeout):
        if timeout is not None:
            t0 = time.time()
        header = self.stream.read(self.HEADER.size, timeout)
        if timeout is not None:
            timeout = min(0, t0 + timeout - time.time())
        if self.FRAME_LIMIT and length > self.FRAME_LIMIT:
            raise ChannelRecvError("frame too long")
        length, = self.HEADER.unpack(header)
        self.stream.read(length, timeout)

class Int16Channel(PrefixedLengthChannel):
    HEADER = Struct("!H")

class Int32Channel(PrefixedLengthChannel):
    HEADER = Struct("!L")

def LimitedInt16Channel(limit):
    return type("Int16Channel<%d>" % (limit,), (Int16Channel,), {"FRAME_LIMIT" : limit})








