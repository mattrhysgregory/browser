import socket
import ssl
class URL:
    # Parse the URL provided into it's various components
    def __init__(self, url):
        self.scheme, url = url.split('://',1)
        assert self.scheme in ["http", "https", "file"]                            # ensure valid scheme
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/",1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        self.path = "/" + url
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

    def read_local_file(self):
        location = self.path
        f = open(self.path, "r")
        return f.read()
    
    # Make a request
    def request(self, headers = {}):
        if self.scheme == 'file':
            return self.read_local_file()
        s = socket.socket(                                      # define a socket
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        s.connect((self.host, self.port))                                
        request = "GET {} HTTP/1.0\r\n".format(self.path)       # structure the "http 1.0" GET request {} is replaced by path
        request += "Host: {}\r\n".format(self.host)
        if headers.values():
            request += '\r\n'.join(['{0}: {1}'.format(key, value) for (key, value) in headers.items()])
            request += "\r\n"
        request += "\r\n"
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2) # first line of response details how the request went
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break                            # \r\n signals the end of a response
            header, value = line.split(":", 1)                  # headers split by colon :
            response_headers[header.casefold()] = value.strip() # lower case header name, and remove any whitespace
        assert "transfer_encoding" not in response_headers
        assert "content_encoding" not in response_headers       # compression header    
        content = response.read()
        s.close()
        return content
    
def show(body): 
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url = "/home/matt/git/browser-project/example-local-file.html"):
    headers= {"Connection":"close","User-Agent":"Mattzilla/0.1"}
    body = url.request(headers)
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))