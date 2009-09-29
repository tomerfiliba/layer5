"""
adds frame-level compression

parameters:
 * compression_threadhold - the minimum size above which frames are compressed
 * compression level - 1..9, 9 being highest compression
 * minimal_efficiency - 0..1, the minimal expected compression ratio. if the 
   actual ratio turns out lower than this, the compression will automatically
   be disabled to save time


"""
import zlib


class CompressedChannel(object):
    def send(self, data, timeout):
        data2 = zlib.compress(data, self.COMPRESSION_LEVEL)
        return self.channel.send(data2, timeout)
    
    def recv(self, timeout):
        data, timeout = self.channel.recv(timeout)
        data2 = zlib.decompress(data)
        return data2, timeout


class CompressionCapability(object):
    def handshake(self, medium):
        medium.channel = CompressedChannel(medium.channel)


