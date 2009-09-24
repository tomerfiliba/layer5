class NegotiatorError(Exception):
    pass
class Phase1ProtocolError(NegotiatorError):
    ERROR_CODE = "ERROR"
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

    @classmethod
    def report_error(cls, chan, errcode):
        try:
            chan.send(errcode, 0)
        except Exception:
            pass
        chan.stream.close()
    
    def handshake(self, stream):
        raise NotImplementedError()


class Phase2Negotiator(object):
    DEFAULT_HANDSHAKE_TIMEOUT = 5
    VERSION = None
    
    def __init__(self, timeout = DEFAULT_HANDSHAKE_TIMEOUT):
        assert type(self.VERSION) is str, "VERSION must be set to a string"
        self.timeout = timeout
    
    def __repr__(self):
        return "<%s.%s(%r) object at 0x%x>" % (self.__class__.__module__, 
            self.__class__.__name__, id(self))
    
    def handshake(self, stream):
        raise NotImplementedError()



