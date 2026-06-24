import http.server, socketserver, functools

DIRECTORY = "/Users/matiasvladilo/Desktop/MASTER/DMTech"
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIRECTORY)
with socketserver.TCPServer(("127.0.0.1", 4599), Handler) as httpd:
    httpd.serve_forever()
