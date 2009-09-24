import brine
import time
import itertools
from functools import partial


class CallingNamespace(object):
    __slots__ = ["__invoker"]
    def __init__(self, invoker):
        self.__invoker = invoker
    def __getattr__(self, funcname):
        return self[name]
    def __getitem__(self, funcname):
        return lambda *a, **k: self.__invoker(funcname, a, k)

class DeferredResult(object):
    __slots__ = ["start_time", "_triggered", "_succ", "_obj"]
    def __init__(self):
        self.start_time = time.time()
        self._triggered = False
    def trigger(self, succ, obj):
        self._triggered = True
        self._succ = succ
        self._obj = obj
    def wait(self, timeout = None):
        if timeout is not None:
            tend = self.start_time + timeout
        
        

class RPCMedium(object):
    TAG_CALL = 1
    TAG_METACALL = 2
    TAG_REPLY = 3
    REP_SYNC = 4
    REP_ASYNC = 5
    
    def __init__(self, channel, service, meta_service):
        self.channel = channel
        self.meta_service = meta_service
        self.service = service
        self.call = CallingNamespace(self.invoke_sync)
        self._seq = itertools.count()
        self._replies = {}
    
    def _send(self, tag, seq, args):
        raw = brine.dump((tag, seq, args))
        self.channel.send(raw)
    def _recv(self):
        raw = self.channel.recv()
        return brine.load(raw)
    
    def serve(self):
        try:
            tag, seq, args = self.recv()
        except Exception:
            pass
        
        if tag == self.TAG_CALL:
            self._dispatch_call(seq, args)
        elif tag == self.TAG_METACALL:
            self._dispatch_metacall(seq, args)
        elif tag == self.TAG_REPLY:
            self._dispatch_reply(seq, args)
        else:
            self.meta_service.handle_invalid_request(tag, seq, args)
    
    def _dispatch_call(self, seq, args):
        funcname, pargs, kwargs = args
        try:
            func = self.service[funcname]
        except LookupError:
            self.meta_service.handle_unknown_function(seq, funcname, pargs, kwargs)
            return
        try:
            res = func(*pargs, **kwargs)
        except RemotableException, ex:
            self._send(self.TAG_REPLY, seq, (False, ex.dump()))
        except Exception, ex:
            output = self.meta_service.dump_exception(ex)
            self._send(self.TAG_REPLY, seq, (False, output))
        else:
            self._send(self.TAG_REPLY, seq, (True, res))
    
    def _dispatch_metacall(self, seq, args):
        pass
    
    def _dispatch_reply(self, seq, args):
        mode, callback = self._replies.pop(seq, (None, None))
        succ, obj = args
        if mode == self.REP_SYNC:
            self._replies[seq] = (succ, obj)
        elif mode == self.REP_ASYNC:
            callback(succ, obj)
        else:
            self.meta_service.handle_invalid_reply_sequence(seq, succ, obj)
    
    def invoke_sync(self, funcname, args, kwargs):
        seq = self._seq.next()
        self._send(self.TAG_CALL, seq, (funcname, args, tuple(kwargs.items())))
        self._replies[seq] = (self.REP_SYNC, None)
        while self._replies[seq][0] == self.REP_EMPTY:
            self.serve()
        succ, obj = self._replies.pop(seq)
        if succ:
            return obj
        else:
            raise obj

    def invoke_async(self, callback, funcname, args, kwargs):
        seq = self._seq.next()
        self._send(self.TAG_CALL, seq, (funcname, args, tuple(kwargs.items())))
        self._replies[seq] = (self.REP_ASYNC, callback)

    def invoke_deferred(self, funcname, args, kwargs):
        d = DeferredResult(self)
        self.invoke_async(d.trigger, funcname, args, kwargs)
        return d











