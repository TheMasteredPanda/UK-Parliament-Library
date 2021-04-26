import aiohttp

class HTTPSClient:
    def __init__(self, session: aiohttp.ClientSession = None):
        self.session = session if session is not None else aiohttp.ClientSession()
    
    def fetch(self, url):
        async with self.session.get(url) as resp:
            return resp

