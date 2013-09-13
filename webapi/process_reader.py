from multiprocessing import Process, Pipe
from gevent.threadpool import ThreadPool
from os import path
import logging.config
import config

__all__ = ['ProcessReader']

IPC_TIMEOUT = config.ipc_timeout

def logging_configurator(reader_path):
 title = 'reader_{0}.log'.format(path.basename(reader_path).replace(':','~'))
 def closure(config):
  basedir = path.dirname(config['handlers']['u2']['filename'])
  config['handlers']['u2']['filename'] = path.join(basedir,title)
  return logging.config.DictConfigurator(config)
 return closure

def process_request(reader,callback,request):
 from handlers_base import format_exception
 request['reader'] = reader

 with reader:
  mod, cls = callback.rsplit('.', 1)
  mod = __import__(mod, None, None, [''])
  cls = getattr(mod, cls)

  cls().action(**request)

 request['answer']['error'] = format_exception(*reader.exc_info)

class IPCError(Exception):
 def __init__(self,message):
  super(IPCError,self).__init__(message)

def remote_worker(connection,reader_kw):
 logging.config.dictConfigClass = logging_configurator(reader_kw['path'])

 from glob import glob
 for filename in glob('config.py'):
  exec(open(filename).read())

 from u2py.config import time as time_measure
 from u2py.interface import Reader
 reader = Reader(**reader_kw)

 while True:
  try:
   callback,request = connection.recv()
  except KeyboardInterrupt: break;

  #import time
  #if callback == 'webapi.scan.scan':
  # import time
  # time.sleep(10)

  if callback == 'close':
   break;

  time_begin = time_measure()
  process_request(reader,callback,request)
  request['answer']['process_time_elapsed'] = time_measure() - time_begin

  connection.send(request['answer'])

 print 'Reader',reader_kw,'process closing'
 reader.close()

from gevent import Timeout

class ProcessReader(object):
 @staticmethod
 def local_worker(connection,callback,request):
  connection.send([callback,request])
  try:
   return connection.recv()
  except EOFError:
   print 'connection.recv EOFError'
   return None
  #response_available = connection.poll(IPC_TIMEOUT)
  #if response_available:
  # return connection.recv()
  #else:
  # print 'no response available'
  # return None


 def apply(self, callback, args = None, kwds = None):
  '''
  This method emulates ThreadPool.apply behaviour by utilizing its own thread
  pool and remote worker in another process.
  Since there is no way to send arbitrary callback to another process,
  we send a name of a class with |action| method and a dictionary of arguments
  instead. This technique currently supports only APIHandler descendants.
  Classname if being guessed in such way:
    1. if |args| contains anything, we treat it as an instance of our "action-class"
       ignoring |callback| parameter (This is how API callbacks are called via
       generic ThreadPool.apply).
    2. if there is no elements in |args|, then |callback| will be used as a class name
       for remote call directly.
  When remote call executes successfully |kwds['answer']| will be updated with
  remote result(|answer| parameter of <callback class>.action).
  Remote result will also be returned as a result of this method.
  '''
  self.open()

  if kwds == None: kwds = {}
  kwds['reader'] = None
  if 'answer' not in kwds:
   kwds['answer'] = {}
  if args != None and len(args):
   cls = type(args[0])
   callback = '.'.join([cls.__module__,cls.__name__])

  answer = None
  with Timeout(IPC_TIMEOUT,False):
   answer = self.thread_pool.apply(ProcessReader.local_worker,
                                   args = (self.connection, callback, kwds))
  if answer is None:
   self.terminate()
   raise IPCError('Request to remote process timed out')

  kwds['answer'].update(answer)
  return answer

 def open(self):
  if not self.started:
  #if self.process is None or not self.process.is_alive():
   print 'Starting new reader process...',self.reader_kw
   self.connection,child_connection = Pipe()
   self.process = Process(target = remote_worker, args = (child_connection,self.reader_kw))
   self.process.start()
   self.started = True

 def terminate(self):
  print 'Terminating process',self.process
  self.process.terminate()
  self.process.join()
  self.started = False

 def close(self):
  if self.started:
   self.connection.send(['close',{}])
   self.process.join(IPC_TIMEOUT)
   if self.process.is_alive():
    self.terminate()
   self.started = False

 def __init__(self,**reader_kw):
  self.thread_pool = ThreadPool(1)
  self.reader_kw = reader_kw
  self.process = None
  self.started = False