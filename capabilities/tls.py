import ssl


class TlsClientCapability(object):
    def handshake(self, medium):
        stream = medium.channel.stream
        if not isinstance(stream, SocketChannel):
            raise TypeError
        stream.sock = ssl.wrap_socket(stream.sock)

class TlsServerCapability(object):
    def handshake(self, medium):
        stream = medium.channel.stream
        if not isinstance(stream, SocketChannel):
            raise TypeError
        stream.sock = ssl.wrap_socket(stream.sock, server = True)


