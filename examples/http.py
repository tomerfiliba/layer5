import layer5


############## server ########################################################
class HttpService(layer5.SimpleService):
    def exposed_get(self, page, host, agent = None, encoding = None, charset = "utf8"):
        pass
    def exposed_put(self, page, host, data, agent = None, encoding = None, charset = "utf8"):
        pass

s = layer5.Server(HttpService, port = 80, 
    capabilities = [layer5.caps.TLS, layer5.caps.zlib])
s.start()


############## client ########################################################
medium = layer5.connect_tcp(layer5.VoidService, "localhost", 80, 
    capabilities = [layer5.caps.TLS, layer5.caps.zlib])

data = medium.call.get("/foo", "www.spam.eggs/foo", agent = "mozilla")


