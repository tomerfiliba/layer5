import brine
import itertools
from .base import RPCMediumBase, RemotableException, GenericRemotableException


class RPCMedium(RPCMediumBase):
    VERSION = "1.0"
    _DISPATCHERS = {}
    
    TAG_CALL = 1
    TAG_METACALL = 2
    TAG_REPLY = 3
    TAG_ERROR = 4
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
    
    def _send(self, tag, *args):
        raw = brine.dump((tag, args))
        self.channel.send(raw)
    
    def serve(self, timeout = None):
        try:
            raw = self.channel.recv(timeout)
            try:
                tag, args = brine.load(raw)
            except Exception, ex:
                raise InvalidMessage(str(ex))
            try:
                dispatcher = self._DISPATCHERS[tag]
            except KeyError:
                raise InvalidTag(tag)
            dispatcher(args)
        except RpcProtocolError, ex:
            self._send(self.TAG_ERROR, dump_exc())
    
    @_register(TAG_CALL)
    def _handle_call(self, args):
        try:
            seq, funcname, args, kwargs = args
        except ValueError:
            raise InvalidCall("wrong structure")
        try:
            res = self.serve.invoke(funcname, args, kwargs)
        except Exception, ex:
            self._send(self.TAG_REPLY, seq, False, dump_exc())
        else:
            self._send(self.TAG_REPLY, seq, True, res)

    @_register(TAG_METACALL)
    def _handle_metacall(self, args):
        try:
            seq, funcname, args, kwargs = args
        except ValueError:
            raise InvalidMetaCall("wrong structure")
        try:
            if funcname not in self.service.META_FUNCTIONS:
                raise InvalidMetaCall("cannot access %r" % (funcname,))
            res = getattr(self.serve, funcname)(*args, **kwargs)
        except Exception, ex:
            self._send(self.TAG_REPLY, seq, False, dump_exc())
        else:
            self._send(self.TAG_REPLY, seq, True, res)
    
    @_register(TAG_REPLY)
    def _handle_reply(self, args):
        try:
            seq, succ, obj = args
        except Exception:
            raise InvalidReply("wrong structure")
        try:
            mode, slot = self._replies[seq]
        except KeyError:
            raise InvalidReply("invalid sequence")
        if mode == self.REP_SYNC:
            if not succ:
                obj = load_exc(obj)
            slot.extend((succ, obj))
        elif mode == self.REP_ASYNC:
            if not succ:
                obj = load_exc(obj)
            slot(succ, obj)
        else:
            raise InvalidReply("invalid mode")
    
    @_register(TAG_ERROR)
    def _handle_error(self, args):
        exc = load_exc(args[0])
        raise exc
    
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



