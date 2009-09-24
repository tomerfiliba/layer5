import time


class StreamError(Exception):
    pass
class StreamTimeout(StreamError):
    def __init__(self, timeout):
        StreamError.__init__(self, "IO timed out after %r seconds" % (timeout,))
        self.timeout = timeout
class StreamClosed(StreamError):
    pass


class BaseStream(object):
    __slots__ = []
    IO_CHUNK = 8100
    
    def __del__(self):
        self.close()
    def close(self):
        if self.closed:
            return
        self._close()
    def _close(self):
        raise NotImplementedError()
    @property
    def closed(self):
        return self._closed()
    def _closed(self):
        raise NotImplementedError()
    def fileno(self):
        raise NotImplementedError()
    
    def recv(self, count, timeout):
        if timeout is not None:
            t0 = time.time()
        data = self._recv(count, timeout)
        if timeout is not None:
            timeout -= time.time() - t0
        return data, timeout
    def write(self, data, timeout):
        if timeout is not None:
            t0 = time.time()
        self._write(data, timeout)
        if timeout is not None:
            timeout -= time.time() - t0
        return timeout
    
    def _read(self, count, timeout):
        raise NotImplementedError()
    def _write(self, data, timeout):
        raise NotImplementedError()
    
class _ClosedFile(object):
    def __getattr__(self, name):
        raise StreamClosed()
    def fileno(self):
        raise StreamClosed()
    def close(self):
        pass
    def closed(self):
        return True
    def __int__(self):
        raise StreamClosed()
ClosedFile = _ClosedFile()

