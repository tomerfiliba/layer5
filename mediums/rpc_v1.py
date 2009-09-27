import brine
import itertools
from .base import RPCMediumBase, RemotableException, GenericRemotableException





class RPCMedium(RPCMediumBase):
    VERSION = "1.0"
    _DISPATCHERS = {}
    
    TAG_CALL = 1
    TAG_METACALL = 2
    TAG_REPLY = 3
    REP_SYNC = 1
    REP_ASYNC = 2
    
    def _register(tag, _DISPATCHERS = _DISPATCHERS):
        def deco(func):
            _DISPATCHERS[tag] = func
            return func
        return deco
    
    def __init__(self, channel, service):
        RPCMediumBase.__init__(self, channel, service)
        self._seq = itertools.counter()
        self._replies = {}
    
    def _send(self, tag, seq, *args):
        raw = brine.dump((tag, seq, args))
        self.channel.send(raw)
    
    def serve(self, timeout = None):
        try:
            tag, seq, args = brine.load(self.channel.recv(timeout))
            dispatcher = self._DISPATCHERS[tag]
        except Exception:
            pass
        try:
            dispatcher(seq, args)
        except RpcProtocolError, ex:
            pass
    
    @_register(TAG_CALL)
    def _handle_call(self, seq, args):
        try:
            funcname, args, kwargs = args
        except ValueError:
            raise InvalidCall("wrong structure")
        try:
            res = self.serve.invoke(funcname, args, kwargs)
        except Exception, ex:
            dumped = dump_exc()
            self._send(self.TAG_REPLY, seq, False, dumped)
        else:
            self._send(self.TAG_REPLY, seq, True, res)

    @_register(TAG_METACALL)
    def _handle_metacall(self, seq, args):
        try:
            funcname, args, kwargs = args
        except ValueError:
            raise InvalidMetaCall("wrong structure")
        try:
            if funcname not in self.service.META_FUNCTIONS:
                raise InvalidMetaCall("cannot access %r" % (funcname,))
            res = getattr(self.serve, funcname)(*args, **kwargs)
        except Exception, ex:
            dumped = dump_exc(sys.exc_info())
            self._send(self.TAG_REPLY, seq, False, dumped)
        else:
            self._send(self.TAG_REPLY, seq, True, res)
    
    @_register(TAG_REPLY)
    def _handle_reply(self, seq, args):
        try:
            mode, slot = self._replies[seq]
            succ, obj = args
        except Exception:
            raise InvalidReply("wrong structure")
        if mode == self.REP_SYNC:
            slot.extend((succ, obj))
        elif mode == self.REP_ASYNC:
            slot(succ, obj)
        else:
            raise InvalidReply("invalid mode")
    
    def invoke_sync(self, func, args, kwargs):
        seq = self._seq.next()
        self._send(self.TAG_CALL, seq, func, args, kwargs)
        empty = self._replies[seq] = (self.REP_SYNC, [])
        while self._replies[seq] is empty:
            self.serve()
        _, (succ, obj) = self._replies.pop(seq)
        if succ:
            return obj
        else:
            raise obj
    
    def invoke_async(self, callback, func, args, kwargs):
        seq = self._seq.next()
        self._send(self.TAG_CALL, seq, func, args, kwargs)
        self._replies[seq] = (self.REP_ASYNC, callback)
    


