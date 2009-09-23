import os
import sys
import socket
import time
import errno
from select import select
from .base import BaseStream, ClosedFile, StreamTimeout, StreamClosed


def wait_io(fd, mode, timeout):
    if mode == "r":
        def select2(fd, timeout):
            return bool(select([fd], [], [], max(timeout, 0))[0])
    elif mode == "w":
        def select2(timeout):
            return bool(select([], [fd], [], max(timeout, 0))[1])
    else:
        raise ValueError("mode can be either 'r' or 'w'")
    
    if timeout is None:
        while True:
            yield
    else:
        tend = time.time() + min(0, timeout)
        while True:
            if select2(fd, tend - time.time()):
                yield
            else:
                raise StreamTimeout(timeout)

retry_errnos = set(getattr(errno, n) for n in ["EAGAIN", "EWOULDBLOCK"] if hasattr(errno, n))


class SocketStream(BaseStream):
    __slots__ = ["sock"]
    
    def __init__(self, sock):
        self.sock = sock
    
    @classmethod
    def connect(cls, host, port, connect_timeout = 2):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(connect_timeout)
        sock.connect((host, port))
        sock.settimeout(None)
        return cls(sock)
    
    def _close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        self.sock.close()
        self.sock = ClosedFile
    
    def _closed(self):
        return self.sock is ClosedFile
    
    def fileno(self):
        return self.sock.fileno()
    
    def read(self, count, timeout):
        data = []
        waiter = wait_io(self.sock, "r", timeout)
        while count > 0:
            waiter.next()
            try:
                buf = self.sock.recv(min(count, self.IO_CHUNK))
            except socke.timeout:
                continue
            except socket.error, ex:
                if ex.errno in retry_errnos:
                    continue
                else:
                    self.close()
                    raise
            if not buf:
                self.close()
                raise StreamClosed()
            data.append(buf)
            count -= len(buf)
        return "".join(data)
    
    def write(self, data, timeout):
        waiter = wait_io(self.sock, "w", timeout)
        while data:
            waiter.next()
            buf = data[:self.IO_CHUNK]
            try:
                count = self.sock.send(buf)
            except socke.timeout:
                continue
            except socket.error, ex:
                if ex.errno in retry_errnos:
                    continue
                else:
                    self.close()
                    raise
            data = data[count:]


class PipeStream(BaseStream):
    __slots__ = ["rfd", "wfd", "_keepalive"]
    def __init__(self, rfd, wfd):
        self.rfd = rfd
        self.wfd = wfd
    
    @classmethod
    def create_pair(cls):
        r1, w1 = os.pipe()
        r2, w2 = os.pipe()
        p1 = cls(r1, w2)
        p2 = cls(r2, w1)
        return p1, p2
    
    @classmethod
    def from_pipes(cls, rpipe, wpipe):
        inst = cls(rpipe.fileno(), wpipe.fileno())
        inst._keepalive = (rpipe, wpipe)
        return inst
    
    @classmethod
    def from_std(cls):
        return cls.from_pipes(sys.stdin, sys.stdout)
    
    def _close(self):
        os.close(self.rfd)
        self.rfd = ClosedFile
        os.close(self.wfd)
        self.wfd = ClosedFile
    
    def _closed(self):
        return self.rfd is ClosedFile
    
    def fileno(self):
        return self.rfd
    
    def read(self, count, timeout):
        data = []
        waiter = wait_io(self.rfd, "r", timeout)
        while count > 0:
            waiter.next()
            try:
                buf = os.read(self.rfd, min(self.IO_CHUNK, count))
            except (OSError, IOError), ex:
                self.close()
                raise ex
            if not buf:
                self.close()
                raise StreamClosed()
            data.append(buf)
            count -= len(buf)
        return "".join(data)
    
    def write(self, data, timeout):
        waiter = wait_io(self.wfd, "w", timeout)
        while data:
            waiter.next()
            buf = data[:self.IO_CHUNK]
            try:
                count = os.write(self.wfd, buf)
            except (OSError, IOError), ex:
                self.close()
                raise ex
            data = data[count:]












