# -*- coding: utf-8 -*-
from gevent.wsgi import WSGIServer

import os
import web
import handlers

def make_server(ssl = None):
 from config import host,port

 web.config.debug = False
 web.internalerror = web.debugerror
 app = web.application(handlers.urls, globals()).wsgifunc()

 kw = {}
 if ssl: kw.update({
    'keyfile': os.path.join(os.path.dirname(__file__),'server.key'),
    'certfile': os.path.join(os.path.dirname(__file__),'server.crt')
 })

 print 'Serving on {0}:{1}...'.format(host,port)

 return WSGIServer((host, port), app, **kw)