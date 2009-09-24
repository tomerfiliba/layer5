from ..channels.binary import LimitedInt16Channel
from ..mediums.rpc_v1 import RPCMedium
from .base import Phase2Negotiator, Phase2ProtocolError

LimitedChannel = LimitedInt16Channel(8192)


class Phase2ServerNegotiator(Phase2Negotiator):
    VERSION = "1.0"
    
    def __init__(self, protocol, capabilities, timeout = Phase2Negotiator.DEFAULT_HANDSHAKE_TIMEOUT):
        Phase2Negotiator.__init__(self, timeout)
        self.protocol = protocol
        self.capabilities = capabilities
    
    def handshake(self, stream):
        medium = RPCMedium(LimitedChannel(stream))
        medium.serve()


class Phase2ClientNegotiator(Phase2Negotiator):
    VERSION = "1.0"
    
    def __init__(self, protocol, capabilities, timeout = Phase2Negotiator.DEFAULT_HANDSHAKE_TIMEOUT):
        Phase2Negotiator.__init__(self, timeout)
        self.protocol = protocol
        self.capabilities = capabilities
    
    def handshake(self, stream):
        medium = RPCMedium(LimitedChannel(stream))
        medium.serve()


