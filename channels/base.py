from ..streams import StreamTimeout


class ChannelError(Exception):
    pass
class ChannelTimeout(ChannelError):
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
        try:
            return self._recv(timeout)
        except StreamTimeout, ex:
            raise ChannelTimeout(ex)
    def send(self, data, timeout):
        try:
            return self._send(timeout)
        except StreamTimeout, ex:
            raise ChannelTimeout(ex)

    def _recv(self, timeout):
        raise NotImplementedError()
    def _send(self, data, timeout):
        raise NotImplementedError()

