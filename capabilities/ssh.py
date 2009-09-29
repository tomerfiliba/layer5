"""
establishes ssh port-forwarding on both sides, closes the existing connection,
and starts a new connection over the port-forwarding
"""


class SshClientCapability(object):
    def handshake(self, medium):
        server_port = medium.call.bind_server_locally()
        os.system("ssh -fN -L%d:%s:%d" % (free_port, host, server_port))
        old_sock = medium.channel.stream.sock
        new_sock = SocketStream.connect("localhost", free_port)
        medium.channel.stream.sock = new_sock
        old_sock.close()

class SshServerCapability(object):
    def handshake(self, medium):
        medium.serve()
    
    def bind_server_locally(self):
        return local_port




