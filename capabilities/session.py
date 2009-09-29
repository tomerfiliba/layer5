"""
the session capability sends a unique cookie to the other party.
if the connection is dropped, this layer will attempt to reconnect
the medium, and uses the cookie to resume the verify the session.

parameters:
 * max_reconnect_attempts
 * reconnect_attempt_timeout
 * reconnect_attempt_backoff_interval

"""
import random
import time
import hashlib


class SessionChannel(object):
    MAX_RECONNECT_ATTEMPTS = 3
    RECONNECT_ATTEMPT_TIMEOUT = 4
    RECONNECT_ATTEMPT_MIN_INTERVAL = 1
    RECONNECT_ATTEMPT_MAX_INTERVAL = 10
    
    def __init__(self, channel):
        self.channel = channel
    
    @classmethod
    def generate_cookie(cls):
        data = repr(time.time()) + " " + repr(random.random())
        return hashlib.sha1(data * 10).digest()
    
    def reconnect(self):
        self.channel.stream.reconnect()
        renegotiate()
    
    #
    # channel API
    #
    def send(self, data, timeout):
        try:
            return self.channel.send(data, timeout)
        except ChannelError:
            pass
    
    def recv(self, timeout):
        try:
            return self.channel.recv(timeout)
        except ChannelError:
            pass


if __name__ == "__main__":
    print SessionChannel.generate_cookie().encode("hex")

