
class ClientServiceErrorID:
    SERVICE_NOT_READY= 0x01
    CLIENT_SANITY_FAILED = 0x02

class ServiceNotReady(Exception):
    def __init__(self):
        self.value = ClientServiceErrorID.SERVICE_NOT_READY
    def __str__(self):
        return repr(self.value)

class ClientSanityFailed(Exception):
    def __init__(self):
        self.value = ClientServiceErrorID.CLIENT_SANITY_FAILED
    def __str__(self):
        return repr(self.value)