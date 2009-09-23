class NegotiatorError(Exception):
    pass
class Phase1ProtocolError(NegotiatorError):
    pass
class Phase2ProtocolError(NegotiatorError):
    pass


class Phase1Negotiator(object):
    DEFAULT_HANDSHAKE_TIMEOUT = 5

    def __init__(self, phase2_negotiators, timeout = DEFAULT_HANDSHAKE_TIMEOUT):
        # assert no newline in keys?
        self.phase2_negotiators = phase2_negotiators
        self.timeout = timeout
    
    @classmethod
    def from_phase2_negotiators(cls, phase2_negotiators, timeout = DEFAULT_HANDSHAKE_TIMEOUT):
        return cls(dict((str(n.VERSION), n) for n in phase2_negotiators), timeout)
    
    def handshake(self, stream):
        raise NotImplementedError()


class Phase2Negotiator(object):
    DEFAULT_HANDSHAKE_TIMEOUT = 5
    VERSION = None
    
    def __init__(self, timeout = DEFAULT_HANDSHAKE_TIMEOUT):
        assert self.VERSION is not None
        self.timeout = timeout
    
    def handshake(self, stream):
        raise NotImplementedError()



