import sys
import time
import weakref
from functools import partial


#===============================================================================
# Exceptions
#===============================================================================
class RPCError(Exception):
    pass

class DeferredResultTimeout(RPCError):
    pass

class RemotableException(RPCError):
    def __init__(self, *args):
        RPCError.__init__(self, *args)
        self._tb = None
    def __str__(self):
        s = RPCError.__str__(self)
        if self._tb:
            s += "\nOriginal exception traceback:\n\n" + self._tb
        return s
    def dump(self, excinfo = None):
        if not excinfo:
            excinfo = sys.exc_info()
            if not excinfo[0]:
                excinfo = None
        tb = "".join(traceback.format_exception(*excinfo)) if excinfo else None
        if self._tb:
            tb = self._tb + (("\n" + "-" * 78 + "\n" + tb) if tb else "")
        return (self.__class__.__module__, self.__class__.__name__, self.args, tb)
    @classmethod
    def load(cls, modname, clsname, args, tb):
        for subcls in iter_subclasses(cls):
            if subcls.__module__ == modname and subcls.__name__ == clsname:
                inst = subcls(*args)
                break
        else:
            inst = GenericRemotableException(*args)
            #inst.name = clsname
        inst._tb = tb
        return inst

class GenericRemotableException(RemotableException):
    pass

class RpcProtocolError(RemotableException):
    pass


#===============================================================================
# Deferred
#===============================================================================
class DeferredResult(object):
    __slots__ = ["medium", "_succ", "_obj", "_triggered", "start_time"]
    def __init__(self, medium):
        self.medium = medium
        self.start_time = time.time()
        self._triggered = False
    def trigger(self, succ, obj):
        if self._triggered:
            raise ValueError("already triggered")
        self._triggered = True
        self._succ = succ
        self._obj = obj
    def wait(self, timeout = None):
        if self._triggered:
            return
        if timeout is None:
            remaining = None
        else:
            tend = self.start_time + timeout
            remaining = max(0, tend - time.time())
        while True:
            self.medium.serve(remaining)
            if self._triggered:
                break
            if timeout is not None:
                remaining = tend - time.time()
                if timeout < 0:
                    raise DeferredResultTimeout(timeout)
    def get(self, timeout):
        self.wait(timeout)
        return self.value
    @property
    def ready(self):
        return self._triggered
    @property
    def value(self):
        self.wait()
        if self._succ:
            return self._obj
        else:
            raise self._obj

#===============================================================================
# Services
#===============================================================================
class ServiceBase(object):
    META_FUNCTIONS = ["query_name", "query_functions"]
    
    def __init__(self):
        self.medium = None
    def _attached(self, medium):
        assert self.medium is None
        self.medium = medium
    def _detached(self):
        self.medium = None
    def invoke(self, funcname, args, kwargs):
        raise NotImplementedError()
    def query_name(self):
        name = self.__class__.__name__.upper()
        if name.endswith("SERVICE"):
            name = name[7:]
        return name
    def query_functions(self):
        raise NotImplementedError()

class SimpleServiceBase(ServiceBase):
    def invoke(self, funcname, args, kwargs):
        if funcname.startswith("exposed_"):
            funcname = funcname[8:]
        func = getattr(self, "exposed_%s" % (funcname,))
        return func(*args, **kwargs)

    def query_functions(self):
        methods = {}
        for name in dir(self):
            if not name.startswith("exposed_"):
                continue
            obj = getattr(self.__class__, name)
            methods[name] = inspect.getdoc(obj)
        return methods

class StatefulServiceBase(ServiceBase):
    STATES = {}
    INITIAL = None
    
    def __init__(self):
        self.state = self.INITIAL
    def query_functions(self):
        methods = {}
        for name in self.STATES[self.state].keys():
            obj = getattr(self.__class__, name)
            methods[name] = inspect.getdoc(obj)
        return methods
    def invoke(self, funcname, args, kwargs):
        transitions = self.STATES[self.state]
        try:
            next_state = transitions[funcname]
        except KeyError:
            raise AttributeError("%r unavailable" % (funcname,))
        func = getattr(self, "exposed_%s" % (funcname,))
        res = func(*args, **kwargs)
        self.state = next_state
        return res

#===============================================================================
# RPC Medium
#===============================================================================
class CallingNamespace(object):
    __slots__ = ["__invoker"]
    def __init__(self, invoker):
        self.__invoker = invoker
    def __getattr__(self, funcname):
        return self[name]
    def __getitem__(self, funcname):
        return lambda *a, **k: self.__invoker(funcname, a, k)


class RPCMediumBase(object):
    VERSION = None
    
    def __init__(self, channel, service):
        self.channel = channel
        self.service = service
        self.call = CallingNamespace(partial(self.invoke_sync.im_func, weakref.proxy(self)))
        self.dcall = CallingNamespace(partial(self.invoke_deferred.im_func, weakref.proxy(self)))
    
    def _attach(self):
        self.service.attached(weakref.proxy(self))
    
    #
    # APIs
    #
    def disconnect(self):
        raise NotImplementedError()
    def serve(self, timeout = None):
        raise NotImplementedError()
    def invoke_sync(self, funcname, args, kwargs):
        raise NotImplementedError()
    def invoke_async(self, callback, funcname, args, kwargs):
        raise NotImplementedError()
    def invoke_deferred(self, funcname, args, kwargs):
        dfr = DeferredResult(self) # weakref.proxy ???
        self.invoke_async(dfr.trigger, funcname, args, kwargs)
        return dfr


#===============================================================================
# Utilities
#===============================================================================
def iter_subclasses(cls):
    yield cls
    for subcls in cls.__subclasses__():
        for subcls2 in iter_subclasses(subcls):
            yield subcls2








