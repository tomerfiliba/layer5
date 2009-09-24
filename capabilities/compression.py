"""
adds frame-level compression

parameters:
 * compression_threadhold - the minimum size above which frames are compressed
 * compression level - 1..9, 9 being highest compression
 * minimal_efficiency - 0..1, the minimal expected compression ratio. if the 
   actual ratio turns out lower than this, the compression will automatically
   be disabled to save time


"""