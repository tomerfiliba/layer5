from ..channels import ChannelTimeout, LimitedInt16Channel
from .base import Phase1Negotiator, Phase1ProtocolError


class NoCommonPhase2Negotiators(Phase1ProtocolError):
    ERROR_CODE = "UNSUPPORTED"
class Phase2NegotiatorNotSupported(Phase1ProtocolError):
    ERROR_CODE = "UNSUPPORTED"

LimitedChannel = LimitedInt16Channel(4096)

def expect(chan, expected, timeout):
    data, timeout = timing_recv(chan, timeout)
    if data != expected:
        raise Phase1ProtocolError("expected %r, found %r" % (expected, data))
    return timeout


class Phase1ServerNegotiator(Phase1Negotiator):
    def handshake(self, stream):
        chan = LimitedChannel(stream)
        timeout = self.timeout
        try:
            timeout = expect(chan, "HELLO NEGOTIATOR SERVER", timeout)
            timeout = chan.send("HELLO NEGOTIATOR CLIENT", timeout)
            data, timeout = chan.recv(timeout)
            client_supported = set(data.splitlines())
            server_supported = set(phase2_negotiators.keys())
            supported_by_both = server_supported.intersection(client_supported)
            if not supported_by_both:
                raise NoCommonPhase2Negotiators()
            chosen = max(supported_by_both)
            timeout = chan.send(chosen, timeout)
            timeout = expect(chan, "OK", timeout)
        except ChannelTimeout:
            self.report_error("TIMEOUT")
            raise
        except Phase1ProtocolError, ex:
            self.report_error(ex.ERROR_CODE)
            raise
        phase2 = self.phase2_negotiators[chosen]
        phase2.handshake(stream)


class Phase1ClientNegotiator(Phase1Negotiator):        
    def handshake(self, stream):
        chan = LimitedChannel(stream)
        timeout = self.timeout
        try:
            timeout = chan.send(chan, "HELLO NEGOTIATOR SERVER", timeout)
            timeout = expect(chan, "HELLO NEGOTIATOR CLIENT", timeout)
            supported = "\n".join(phase2_negotiators.keys())
            timeout = chan.send(supported, timeout)
            chosen, timeout = chan.recv(timeout)
            if chosen not in phase2_negotiators:
                raise Phase2NegotiatorNotSupported("chosen version is not supported")
            timeout = chan.send("OK", timeout)
        except ChannelTimeout:
            self.report_error("TIMEOUT")
            raise
        except Phase1ProtocolError, ex:
            self.report_error(ex.ERROR_CODE)
            raise
        phase2 = self.phase2_negotiators[chosen]
        phase2.handshake(stream)





