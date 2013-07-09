# -*- coding: utf-8 -*-
from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer

import os
import web
import handlers

class Server(WSGIServer):
 def serve_forever(self,*args,**kw):
  from handlers_base import APIHandler
  from process_reader import ProcessReader
  from u2py.config import reader_path
  try:
   APIHandler.readers = [ProcessReader(**reader_kw) for reader_kw in reader_path]
   [reader.open() for reader in APIHandler.readers]
   WSGIServer.serve_forever(self,*args,**kw)
  except KeyboardInterrupt:
   pass
  finally:
   [reader.close() for reader in APIHandler.readers]


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

 return Server((host, port), app, **kw)