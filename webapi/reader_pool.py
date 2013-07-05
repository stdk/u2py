from multiprocessing import Process, Pipe
from gevent.threadpool import ThreadPool
import traceback

from sys import platform
if platform == 'win32': from time import clock as clock
if platform == 'linux2': from time import time as clock

def format_exception(type,value,tb):
 return {
    'type': str(type.__name__),
    'message': str(value),
    'traceback' : [s.rstrip('\n').decode('cp1251')
                   for s in traceback.format_exception(type,value,tb)]
 } if type != None else None

def remote_worker(connection,reader_kw):
 exec(open('config.py'))

 from u2py.interface import Reader
 reader = Reader(**reader_kw)
 print reader.version()
 print reader.sn()
 
 while True:
  callback,request = connection.recv()

  if callback == 'close': break
  
  mod, cls = callback.rsplit('.', 1)
  mod = __import__(mod, None, None, [''])
  cls = getattr(mod, cls)

  clock_begin = clock()
  
  request['reader'] = reader
  
  with reader:
   cls().action(**request)
  request['answer']['error'] = format_exception(*reader.exc_info)
  request['answer']['process_time_elapsed'] = clock() - clock_begin

  connection.send(request['answer'])
 
 print 'Reader',reader,'process closing'
 reader.close()

class ReaderWrapper(object):
 @staticmethod
 def local_worker(connection,callback,request):
  connection.send([callback,request])
  return connection.recv()

 def apply(self, callback, args, kwds):
  self.open()

  kwds['reader'] = None
  cls = type(args[0])
  new_callback = '.'.join([cls.__module__,cls.__name__])
  answer = self.thread_pool.apply(ReaderWrapper.local_worker, args = (self.connection, new_callback, kwds))
  kwds['answer'].update(answer)

 def open(self):
  if not self.started:
   self.process.start()
   self.started = True

 def close(self):
  if self.started:
   self.connection.send(['close', None])
   self.process.join()
   self.started = False

 def __init__(self,**reader_kw):
  self.thread_pool = ThreadPool(1)
  self.connection,child_connection = Pipe()
  self.process = Process(target = remote_worker, args = (child_connection,reader_kw))
  self.started = False