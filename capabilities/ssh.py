"""
establishes ssh port-forwarding on both sides, closes the existing connection,
and starts a new connection over the port-forwarding
"""
import socket
import subprocess


class SshClientCapability(object):
    def __init__(self, username = None, identity_file = None):
        self.username = username
        self.identity_file = identity_file
    
    def handshake(self, medium):
        s = socket.socket()
        s.bind(("localhost", 0))
        _, local_port = s.getsockname()
        
        server_port = medium.call.bind_server_locally()
        subprocess.Popen("ssh -fN -L%d:localhost:%d" % (local_port, server_port, host))
        os.system()
        old_sock = medium.channel.stream.sock
        new_sock = SocketStream.connect("localhost", free_port)
        medium.channel.stream.sock = new_sock
        old_sock.close()

class SshServerCapability(object):
    def handshake(self, medium):
        medium.serve()
    
    def bind_server_locally(self):
        s = SocketStream.bind("localhost", 0)
        return s.local_port




