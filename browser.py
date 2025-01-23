import socket
import ssl
import tkinter

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


class URL:
    # Parse the URL provided into it's various components
    content = ""
    view_source = False

    def __init__(self, url):
        if url.startswith("data:"):
            self.data_url = True
            self.scheme = "data:"
            self.content = url.replace("data:", "")
            print(self.scheme, self.content)
            return

        elif url.startswith("view-source:"):
            self.view_source = True
            url = url.replace("view-source:", "")

        self.scheme, url = url.split("://", 1)

        assert self.scheme in ["http", "https", "file", "data", "view-source"]

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
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
    def request(self, headers={}):
        if self.scheme == "data":
            return self.lex(self.content)

        if self.scheme == "file":
            raw = self.read_local_file()
            return self.lex(raw)

        s = socket.socket(  # define a socket
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        s.connect((self.host, self.port))
        request = "GET {} HTTP/1.0\r\n".format(
            self.path
        )  # structure the "http 1.0" GET request {} is replaced by path
        request += "Host: {}\r\n".format(self.host)
        if headers.values():
            request += "\r\n".join(
                ["{0}: {1}".format(key, value) for (key, value) in headers.items()]
            )
            request += "\r\n"
        request += "\r\n"
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(
            " ", 2
        )  # first line of response details how the request went
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break  # \r\n signals the end of a response
            header, value = line.split(":", 1)  # headers split by colon :
            response_headers[header.casefold()] = (
                value.strip()
            )  # lower case header name, and remove any whitespace
        assert "transfer_encoding" not in response_headers
        assert "content_encoding" not in response_headers  # compression header
        content = response.read()
        s.close()
        return self.lex(content)

    def convert_html_entity(self, word):
        if word == "&lt;":
            return ">"
        elif word == "&gt;":
            return "<"
        else:
            return word

    def lex(self, body):
        if self.view_source:
            return body
        in_tag = False
        buffer = ""
        word = ""
        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                if c == " " or c == ";":
                    word += c
                    buffer += self.convert_html_entity(word)
                    word = ""
                else:
                    word += c
        return buffer


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def load(self, url):
        headers = {"Connection": "close", "User-Agent": "Mattzilla/0.1"}
        text = url.request(headers)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:

        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP or c == "\n":
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


if __name__ == "__main__":
    import sys
    import tkinter

    page_to_load = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "file:///home/matt/git/browser-project/example-local-file.html"
    )

    Browser().load(URL(page_to_load))
    tkinter.mainloop()
