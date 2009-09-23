from ..channels.binary import LimitedInt16Channel
from .base import Phase1Negotiator, Phase1ProtocolError


LimitedChannel = LimitedInt16Channel(4096)

def timing_recv(chan, timeout):
    t0 = time.time()
    data = chan.recv(timeout)
    t1 = time.time()
    return timeout - (t1 - t0), data

def timing_send(chan, data, timeout):
    t0 = time.time()
    chan.send(data, timeout)
    t1 = time.time()
    return timeout - (t1 - t0)

def timing_expect(chan, expected, timeout):
    timeout, data = timing_recv(chan, timeout)
    if data != expected:
        raise Phase1ProtocolError("expected %r, found %r" % (expected, data))
    return timeout


class Phase1ServerNegotiator(Phase1Negotiator):
    def handshake(self, stream):
        chan = LimitedChannel(stream)
        timeout = self.timeout
        try:
            timeout = timing_expect(chan, "HELLO NEGOTIATOR SERVER", timeout)
            timeout = timing_send(chan, "HELLO NEGOTIATOR CLIENT", timeout)
            timeout, data = timing_recv(chan, timeout)
            client_supported = set(data.splitlines())
            server_supported = set(phase2_negotiators.keys())
            chosen = max(server_supported.intersection(client_supported))
            timeout = timing_send(chan, chosen, timeout)
            timeout = timing_expect(chan, "OK", timeout)
        except Phase1ProtocolError:
            stream.close()
            raise
        phase2 = self.phase2_negotiators[chosen]
        phase2.handshake(stream)


class Phase1ClientNegotiator(Phase1Negotiator):        
    def handshake(self, stream):
        chan = LimitedChannel(stream)
        timeout = self.timeout
        try:
            timeout = timing_send(chan, "HELLO NEGOTIATOR SERVER", timeout)
            timeout = timing_expect(chan, "HELLO NEGOTIATOR CLIENT", timeout)
            supported = "\n".join(phase2_negotiators.keys())
            timeout = timing_send(chan, supported, timeout)
            timeout, chosen = timing_recv(chan, timeout)
            if chosen not in phase2_negotiators:
                raise Phase1ProtocolError("chosen version is not supported")
            timeout = timing_send(chan, "OK", timeout)
        except Phase1ProtocolError:
            stream.close()
            raise
        phase2 = self.phase2_negotiators[chosen]
        phase2.handshake(stream)





