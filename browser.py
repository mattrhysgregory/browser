import socket
import ssl

class URL:
    # Parse the URL provided into it's various components
    content = ''
    view_source = False

    def __init__(self, url):
        if url.startswith("data:"):
            self.data_url = True
            self.scheme = "data:"
            self.content = url.replace('data:', "")
            print(self.scheme, self.content)
            return
    
        elif url.startswith("view-source:"):
            self.view_source = True
            url = url.replace("view-source:", "")
        
        self.scheme, url = url.split('://',1)     

        assert self.scheme in ["http", "https", "file", "data", "view-source"]     
        
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
        f = open(self.path, "r")
        return f.read()
    
    # Make a request
    def request(self, headers = {}):
        if self.scheme == 'data':
            return self.render(self.content)
        
        if self.scheme == 'file':
            raw = self.read_local_file()
            return self.render(raw)
        
        
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
        return self.render(content)
    
    def convert_html_entity(self, word):
        if word == "&lt;":
            return ">"
        elif word == "&gt;":
            return "<"
        else:
            return word
        

    def render(self, body):
        if self.view_source:
            return body
        in_tag = False
        buffer = ''
        word = ''
        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                if c == ' ' or c == ';':
                    word += c
                    buffer += self.convert_html_entity(word)
                    word = ''
                else:
                    word += c
        return buffer
    
   

def load(url):
    headers= {"Connection":"close","User-Agent":"Mattzilla/0.1"}
    body = url.request(headers)
    print(body)

if __name__ == "__main__":
    import sys
    if(len(sys.argv) > 1):
        load(URL(sys.argv[1]))
    else:
        load(URL("file:///home/matt/git/browser-project/example-local-file.html"))