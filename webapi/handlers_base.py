#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')


import config
import web
import traceback
from sys import exc_info
from json import JSONEncoder,dumps,loads
from inspect import getargspec
from sys import platform

if platform == 'win32': from time import clock as clock
if platform == 'linux2': from time import time as clock

from u2py.config import logging,reader_path
from u2py.mfex import MFEx
from u2py.interface import Reader
from adbk.state import State

from reader_pool import ReaderWrapper

class APIEncoder(JSONEncoder):
 def default(self, obj):
  'uses to_dict method as runtime interface for serializing to json'
  return obj.to_dict() if hasattr(obj, 'to_dict') else str(obj)

urls = []

class HandlerMetaClass(type):
 def __init__(cls, name, bases, attrs):
  if 'url' in attrs:
   urls.append(attrs["url"])
   urls.append("%s.%s" % (cls.__module__, name))

class NoServerError(Exception):
 def __init__(self,message):
  super(NoServerError,self).__init__(message)

class Handler(object):
 __metaclass__ = HandlerMetaClass
 templates = web.template.render(config.templates_folder.encode('cp1251'))

class MissingParameterError(Exception):
 def __init__(self,message):
  super(MissingParameterError,self).__init__(message)

class JsonError(Exception):
 def __init__(self,message):
  super(JsonError,self).__init__(message)

def prepare_request(post_data, readers, args = None):
 if post_data == None:
  raise JsonError('No JSON request found')

 try:
  request = loads(post_data)
 except Exception as e:
  raise JsonError("{0}: {1}".format(e.__class__.__name__,e))

 if args != None:
  for arg in args.required:
   if arg not in request:
    raise MissingParameterError("Missing parameter: {0}".format(arg))

  if 'reader' in request:
   if 'reader' in args:
    request['reader'] = readers[request['reader']]
   else:
    del request['reader']

 return request

def format_exception(type,value,tb):
 return {
    'type': str(type.__name__),
    'message': str(value),
    'traceback' : [s.rstrip('\n').decode('cp1251')
                   for s in traceback.format_exception(type,value,tb)]
 } if type != None else None

class ReaderlessContext(object):
 def __enter__(self):
  self.exc_info = (None,None,None)
  return self

 def apply(self, callback, args, kwds):
  with self:
   return callback(*args,**kwds)

 def __exit__(self,type,value,traceback):
  self.exc_info = (type,value,traceback)

def api_callback(self,callback,args = None,post_data = None):
 #currently, we allow api to be called crossdomain
 web.header('Access-Control-Allow-Origin','*')
 web.header('Content-Type','application/json; charset=utf-8')

 answer = { 'error' : None }
 try:
  clock_begin = clock()

  answer['is_server_present'] = State.is_server_present()
  if self.need_server and not answer['is_server_present']:
   raise NoServerError('This operation requires vestibule server present')

  request = prepare_request(post_data,self.readers,args)

  request['answer'] = answer

  context = request.get('reader',ReaderlessContext())
  context.apply(callback, args = (self,), kwds = request)
  if hasattr(context,'exc_info'):
   answer['error'] = format_exception(*context.exc_info)
  
 except Exception as e:
  answer['error'] = format_exception(*exc_info())
 finally:
  answer['time_elapsed'] = clock() - clock_begin
 return answer

class Args(object):
 def __init__(self,callback):
  argspec = getargspec(callback)
  defaults = argspec.defaults or []
  self.required = argspec.args[1:-len(defaults)]
  self.defaults = argspec.args[-len(defaults):]
  #answer keyword argument can be anywhere in argument list
  self.defaults.remove('answer')

 def __contains__(self,key):
  return key in self.required or key in self.defaults

def post_api(key,callback,name):
 arguments = Args(callback)

 def wrapper(self,*args,**kw):
  post_data = web.data()
  logging.debug('{0}[{1}]->[{2}]'.format(key,name,post_data))

  answer = api_callback(self,callback,arguments,post_data)

  response = dumps(answer,cls=APIEncoder)
  logging.debug('{0}[{1}]<-[{2}]'.format(key,name,response))
  return response
 return wrapper

def get_api(key,callback,name):
 def  wrapper(self,*args,**kw):
  answer = api_callback(self,callback)
  return dumps(answer,cls=APIEncoder)
 return wrapper

class APIHandlerMetaClass(HandlerMetaClass):
 '''
 This metaclass imposes additional requirements on a GET and POST methods of a class its applied to.
 '''
 def __new__(cls,name,bases,attrs):
  api_decorators = { 'GET' : get_api, 'POST': post_api }
  attrs['action'] = attrs.get('POST',None)
  [ attrs.__setitem__(key,api_decorators[key](key,attrs[key],name))
    for key in api_decorators.keys()
    if key in attrs ]

  return type.__new__(cls, name, bases, attrs)

class APIHandler(Handler):
 __metaclass__ = APIHandlerMetaClass

 need_server = config.read_api_requires_server

 #readers = [Reader(**kw) for kw in reader_path]
 readers = [ReaderWrapper(**kw) for kw in reader_path]