﻿# -*- coding: utf-8 -*-
#from gevent.wsgi import WSGIServer

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from wsgiref import simple_server
from SocketServer import ThreadingMixIn

class MyWSGIServer(ThreadingMixIn, simple_server.WSGIServer): pass

import os
import web
import handlers
from sys import stderr

def run(ssl=None,logger='default'):
 from config import host,port,wsgi_log
 print handlers.urls

 web.config.debug = False
 web.internalerror = web.debugerror
 app = web.application(handlers.urls, globals()).wsgifunc()

 kw = {}
 if ssl: kw.update({
    'keyfile': os.path.join(os.path.dirname(__file__),'server.key'),
    'certfile': os.path.join(os.path.dirname(__file__),'server.crt')
 })

 print 'Serving on {0}:{1}...'.format(host,port)

 #WSGIServer((host, port), app, log = logger, **kw).serve_forever()
 simple_server.make_server(host,port,app,server_class=MyWSGIServer).serve_forever()