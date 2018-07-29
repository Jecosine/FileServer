import BaseHTTPServer as bh
from CGIHTTPServer import CGIHTTPRequestHandler
bh.test(CGIHTTPRequestHandler,bh.HTTPServer)