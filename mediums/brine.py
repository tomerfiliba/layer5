from cStringIO import StringIO
from struct import Struct
from decimal import Decimal


INT1 = Struct("!B")
INT4 = Struct("!L")
INT8 = Struct("!Q")
SINT4 = Struct("!L")
SINT8 = Struct("!Q")
DOUBLE = Struct("!d")

# 0x00..0x2f
TAG_IMM_NONE        = "\x00"
TAG_IMM_TRUE        = "\x01"
TAG_IMM_FALSE       = "\x02"
TAG_IMM_EMPTY_LIST  = "\x03"
TAG_IMM_EMPTY_STR   = "\x04"

TAG_INT4            = "\x05"
TAG_INT8            = "\x06"
TAG_LONG_I1         = "\x07"
TAG_LONG_I4         = "\x08"
TAG_DOUBLE          = "\x09"
TAG_DECIMAL_I1      = "\x0a"
TAG_DECIMAL_I4      = "\x0b"
TAG_STR1            = "\x0c"
TAG_STR2            = "\x0d"
TAG_STR_I1          = "\x0e"
TAG_STR_I4          = "\x0f"
TAG_LIST1           = "\x10"
TAG_LIST2           = "\x11"
TAG_LIST3           = "\x12"
TAG_LIST4           = "\x13"
TAG_LIST_I1         = "\x14"
TAG_LIST_I4         = "\x15"
TAG_BLOB            = "\x16"

# 0x30..0x6f - immediate chars
IMM_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,"
TAG_IMM_CHAR_N = dict((c, chr(0x30 + i)) for i, c in enumerate(IMM_CHARS))

# 0x70..0xff - immediate ints
IMM_INT_BASE = 0x70
IMM_INT_MIN = -0x20
IMM_INT_MAX = 0x6f
TAG_IMM_INT_0 = IMM_INT_BASE + abs(IMM_INT_MIN)


_DUMPERS = {}
_LOADERS = {}

def register_dumper(*types):
    def deco(func):
        for t in types:
            assert t not in _DUMPERS
            _DUMPERS[t] = func
        return func
    return deco

def register_loader(tag):
    def deco(func):
        assert tag not in _LOADERS
        _LOADERS[tag] = func
        return func
    return deco

#===============================================================================
# dumpers
#===============================================================================
@register_dumper(type(None))
def _dump_none(obj, stream):
    stream.write(TAG_IMM_NONE)

@register_dumper(bool)
def _dump_bool(obj, stream):
    stream.write(TAG_IMM_TRUE if obj else TAG_IMM_FALSE)

@register_dumper(float)
def _dump_float(obj, stream):
    stream.write(TAG_DOUBLE)
    stream.write(DOUBLE.pack(obj))

@register_dumper(int, long)
def _dump_int(obj, stream):
    if IMM_INT_MIN <= obj <= IMM_INT_MAX:
        stream.write(chr(TAG_IMM_INT_0 + obj))
    elif -0x80000000 <= obj <= 0x7fffffff:
        stream.write(TAG_INT4)
        stream.write(SINT4.pack(obj))
    elif -0x8000000000000000 <= obj <= 0x7fffffffffffffff:
        stream.write(TAG_INT8)
        stream.write(SINT8.pack(obj))
    else:
        obj = str(obj)
        l = len(obj)
        if l <= 255:
            stream.write(TAG_LONG_I1)
            stream.write(INT1.pack(l))
        else:
            stream.write(TAG_LONG_I1)
            stream.write(INT4.pack(l))
        stream.write(obj)

@register_dumper(Decimal)
def _dump_decimal(obj, stream):
    obj = str(obj)
    l = len(obj)
    if l <= 255:
        stream.write(TAG_DECIMAL_I1)
        stream.write(INT1.pack(l))
    else:
        stream.write(TAG_DECIMAL_I4)
        stream.write(INT4.pack(l))
    stream.write(obj)

@register_dumper(str)
def _dump_str(obj, stream):
    l = len(obj)
    if l == 0:
        stream.write(TAG_IMM_EMPTY_STR)
    elif l == 1:
        if obj in TAG_IMM_CHAR_N:
            stream.write(TAG_IMM_CHAR_N[obj])
        else:
            stream.write(TAG_STR1)
            stream.write(obj)
    elif l == 2:
        stream.write(TAG_STR2)
        stream.write(obj)
    elif l <= 255:
        stream.write(TAG_STR_I1)
        stream.write(INT1.pack(l))
        stream.write(obj)
    else:
        stream.write(TAG_STR_I4)
        stream.write(INT4.pack(l))
        stream.write(obj)

@register_dumper(list, tuple)
def _dump_list(obj, stream):
    l = len(obj)
    if l == 0:
        stream.write(TAG_IMM_EMPTY_LIST)
    elif l == 1:
        stream.write(TAG_LIST1)
    elif l == 2:
        stream.write(TAG_LIST2)
    elif l == 3:
        stream.write(TAG_LIST3)
    elif l == 4:
        stream.write(TAG_LIST4)
    elif l <= 255:
        stream.write(TAG_LIST_I1)
        stream.write(INT1.pack(l))
    else:
        stream.write(TAG_LIST_I4)
        stream.write(INT4.pack(l))
    for item in obj:
        _dump(item, stream)

def _dump_blob(tag, value, stream):
    stream.write(TAG_BLOB)
    _dump(tag, stream)
    _dump(value, stream)

@register_dumper(dict)
def _dump_dict(obj, stream):
    _dump_blob("dict", obj.items(), stream)

@register_dumper(set, frozenset)
def _dump_dict(obj, stream):
    _dump_blob("set", list(obj), stream)

@register_dumper(unicode)
def _dump_unicode(obj, stream):
    _dump_blob("unicode", obj.encode("utf8"), stream)

def _dump(obj, stream):
    _DUMPERS[type(obj)](obj, stream)

def dump(obj):
    stream = StringIO()
    _dump(obj, stream)
    return stream.getvalue()

#===============================================================================
# loaders
#===============================================================================

register_loader(TAG_IMM_NONE)(lambda stream: None)
register_loader(TAG_IMM_TRUE)(lambda stream: True)
register_loader(TAG_IMM_FALSE)(lambda stream: False)
register_loader(TAG_IMM_EMPTY_LIST)(lambda stream: [])
register_loader(TAG_IMM_EMPTY_STR)(lambda stream: "")
for tag, value in TAG_IMM_CHAR_N.items():
    register_loader(tag)(lambda stream, value = value: value)
for value in range(IMM_INT_MIN, IMM_INT_MAX + 1):
    register_loader(TAG_IMM_INT_0 + value)(lambda stream, value = value: value)

@register_loader(TAG_INT4)
def _load_int4(stream):
    return SINT4.unpack(stream.read(SINT4.size))[0]

@register_loader(TAG_INT8)
def _load_int8(stream):
    return SINT8.unpack(stream.read(SINT8.size))[0]

@register_loader(TAG_LONG_I1)
def _load_int_i1(stream):
    length = INT1.unpack(stream.read(INT1.size))[0]
    return int(stream.read(length))

@register_loader(TAG_LONG_I4)
def _load_long_i4(stream):
    length = INT4.unpack(stream.read(INT4.size))[0]
    return int(stream.read(length))

@register_loader(TAG_DOUBLE)
def _load_double(stream):
    return DOUBLE.unpack(stream.read(DOUBLE.size))[0]

@register_loader(TAG_DECIMAL_I1)
def _load_decimal_i1(stream):
    length = INT1.unpack(stream.read(INT1.size))[0]
    return Decimal(stream.read(length))

@register_loader(TAG_DECIMAL_I4)
def _load_decimal_i4(stream):
    length = INT4.unpack(stream.read(INT4.size))[0]
    return Decimal(stream.read(length))

@register_loader(TAG_STR_I1)
def _load_str_i1(stream):
    length = INT1.unpack(stream.read(INT1.size))[0]
    return stream.read(length)

@register_loader(TAG_STR_I4)
def _load_str_i4(stream):
    length = INT4.unpack(stream.read(INT4.size))[0]
    return stream.read(length)

@register_loader(TAG_LIST_I1)
def _load_list_i1(stream):
    length = INT1.unpack(stream.read(INT1.size))[0]
    return [_load(stream) for i in range(length)]

@register_loader(TAG_LIST_I4)
def _load_list_i4(stream):
    length = INT4.unpack(stream.read(INT4.size))[0]
    return [_load(stream) for i in range(length)]


TAG_STR1            = "\x0c"
TAG_STR2            = "\x0d"
TAG_LIST1           = "\x10"
TAG_LIST2           = "\x11"
TAG_LIST3           = "\x12"
TAG_LIST4           = "\x13"
TAG_BLOB            = "\x16"

#===============================================================================
# test
#===============================================================================
if __name__ == "__main__":
    obj = [4, -11, 133, 345787893272, 893475347982387947947342743277893247024, 
        "a", "bb", "ccc", "hello world", True, False, None, 3.8, Decimal("3.8"),
        [], [1], [1,2], [1,2,3], [1,2,3,4], [1,2,3,4,5], (), {1:2, 3:4}]
    print repr(dump(obj))




