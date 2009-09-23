class RPCMedium(object):
    def __init__(self, channel):
        self.channel = channel
    def __del__(self):
        self.close()
    def close(self):
        self.channel.close()
    
    