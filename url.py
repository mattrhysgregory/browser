import socket
class URL:
    # Parse the URL provided into it's various components
    def __init__(self, url):
        self.scheme, url = url.split('://',1)
        assert self.scheme == "http"                            # ensure only http requests are made
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/",1)
        self.path = "/" + url

    # Make a request
    def request(self):
        s = socket.socket(                                      # define a socket
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, 80))                                # connect to that port on 80
        request = "GET {} HTTP/1.0\r\n".format(self.path)       # structure the "http 1.0" GET request {} is replaced by path
        request += "Host: {}\r\n".format(self.host)
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

def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))