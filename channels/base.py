class ChannelError(Exception):
    pass
class ChannelSendError(ChannelError):
    pass
class ChannelRecvError(ChannelError):
    pass


class BaseChannel(object):
    __slots__ = ["stream"]
    
    def __init__(self, stream):
        self.stream = stream
    def fileno(self):
        return self.stream.fileno()
    def recv(self, timeout):
        raise NotImplementedError()
    def send(self, data, timeout):
        raise NotImplementedError()


