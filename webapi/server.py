# -*- coding: utf-8 -*-
import os
import sys
import logging

from gevent import monkey; monkey.patch_all(socket = False)
from gevent.wsgi import WSGIServer

import web
import handlers
import signal

if sys.platform == 'win32':
 # CTRL_BREAK_EVENT can only be catched with console present.
 import win32console
 try:
  win32console.AllocConsole()
 except:
  # When running from cmd.exe, console is already present
  print 'Console already allocated'
 
 reload(sys)
 sys.setdefaultencoding('cp1251')

class Server(WSGIServer):
 def serve_forever(self,*args,**kw):
  from handlers_base import APIHandler
  from process_reader import ProcessReader
  from u2py.config import reader_path

  try:
   APIHandler.readers = [ProcessReader(**reader_kw) for reader_kw in reader_path]
   [reader.open() for reader in APIHandler.readers]

   def signal_handler(sgn,frame):
    logging.debug('Stop signal catched.')
    self.stop()
  
   # signal handler installation depends on os
   if hasattr(os.sys, 'winver'):
    signal.signal(signal.SIGBREAK, signal_handler)
   else:
    signal.signal(signal.SIGTERM, signal_handler)   
   
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