from multiprocessing import Process, Pipe
from gevent.threadpool import ThreadPool
import logging.config
from os import path

from sys import platform
if platform == 'win32': from time import clock as clock
if platform == 'linux2': from time import time as clock

__all__ = ['ProcessReader']

def logging_configurator(reader_path):
 title = 'reader_{0}.log'.format(path.basename(reader_path))
 def closure(config):
  basedir = path.dirname(config['handlers']['u2']['filename'])
  config['handlers']['u2']['filename'] = path.join(basedir,title)
  return logging.config.DictConfigurator(config)
 return closure

def process_worker(connection,reader_kw):
 logging.config.dictConfigClass = logging_configurator(reader_kw['path'])

 from glob import glob
 for filename in glob('config.py'):
  exec(open(filename).read())

 from handlers_base import format_exception
 from u2py.interface import Reader
 reader = Reader(**reader_kw)

 while True:
  try:
   callback,request = connection.recv()
  except KeyboardInterrupt:
   break

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

 print 'Reader',reader_kw,'process closing'
 reader.close()

class ProcessReader(object):
 @staticmethod
 def local_worker(connection,callback,request):
  connection.send([callback,request])
  return connection.recv()

 def apply(self, callback, args = None, kwds = None):
  '''
  This method emulates ThreadPool.apply behaviour by utilizing its own thread
  pool and remote worker in another process.
  Since there is no way to send arbitrary callback to another process,
  we send a name of a class with |action| method and a dictionary of arguments
  instead. This technique currently supports only APIHandler descendants.
  Classname if being guessed in such way:
    1. if |args| contains anything, we treat it as an instance of our "action-class"
       ignoring |callback| parameter (this behaviour conforms to a thread-based reader
       implementation)
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
  answer = self.thread_pool.apply(ProcessReader.local_worker,
                                  args = (self.connection, callback, kwds))
  kwds['answer'].update(answer)
  return answer

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
  self.process = Process(target = process_worker, args = (child_connection,reader_kw))
  self.started = False