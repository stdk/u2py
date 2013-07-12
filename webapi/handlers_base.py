#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')


import config
import web
from sys import exc_info
from json import JSONEncoder,dumps,loads
from inspect import getargspec
from sys import platform

if platform == 'win32': from time import clock as clock
if platform == 'linux2': from time import time as clock

from u2py.config import logging
from adbk.state import State

urls = []

class HandlerMetaClass(type):
 def __init__(cls, name, bases, attrs):
  if 'url' in attrs:
   urls.append(attrs["url"])
   urls.append("%s.%s" % (cls.__module__, name))

class NoServerError(Exception):
 def __init__(self,message):
  super(NoServerError,self).__init__(message)

class MissingParameterError(Exception):
 def __init__(self,message):
  super(MissingParameterError,self).__init__(message)

class JsonError(Exception):
 def __init__(self,message):
  super(JsonError,self).__init__(message)

class Handler(object):
 __metaclass__ = HandlerMetaClass
 templates = web.template.render(config.templates_folder.encode('cp1251'))

def format_exception(type,value,tb):
 if type != None:
  result = {
    'type': str(type.__name__),
    'message': str(value)
  }
  if config.error_with_traceback:
   import traceback
   result['traceback'] = [s.rstrip('\n').decode('cp1251')
                          for s in traceback.format_exception(type,value,tb)]
  return result

def parse_post_data(post_data, readers, args = None):
 '''
  Return value: (context manager, request dictionary)
  Request parsing, argument presence check and context deducing are done here.
  Parsing: json.loads with JsonError when there is no data to parse or given
 data is not a json.
  Argument check: if |args| parameter is not None, then we assume it contains
 an instance of Args class with overloaded __contains__ method and 2 attributes:
 |required| and |defaults| that specify list of parameter names which are essential
 or optional for this method respectively. MissingParameterError will be raised
 when there is no essential paramter present in request.
  Context deducing. There are 2 types of context: reader and readerless.
 Reader context.
 Any api call that requires exactly one reader and doesn't interferes
 with others during its work should specify |reader| parameter as non-default
 within its argument list. Then, if |reader| key is present among request keys
 appropriate reader from |readers| should be returned as context manager for this
 request. Methods must be aware of the fact they'll be executed in another
 process should they conform to its requirements. There are methods which explicitly
 avoid being executed in another process despite accepting |reader| argument
 due to their purpose (e.g. /api/scan/notify). They do it by discarding |reader|
 from argument list and accept it from keyword arguments of its call.
 Some api calls behave differently according to the presence of |reader| key
 in request (e.g. /api/version). Specifically for them, None value of |reader| key
 is identical to the absence of |reader| key.
 Readerless context.
 When conditions of using reader context aren't met, readerless context comes to
 the rescue. As its name suggests, it doesn't belong to any specific reader
 and thus executes in the same process. "Doesn't belong to any specific reader"
 doesn't means it cannot work with any reader at all - it's just says that api call
 performs some general work that cannot be identified with only one reader and thus
 shouldn't be redirected to reader process. (notifications and reader detection
 are examples of such work).
 '''
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

  if 'reader' in request and request['reader'] != None:
   if 'reader' in args:
    return readers[request['reader']],request

 return ReaderlessContext(),request

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

  context,request = parse_post_data(post_data, self.readers, args)
  request['answer'] = answer

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

  json_default = lambda obj: obj.to_dict() if hasattr(obj, 'to_dict') else str(obj)
  response = dumps(answer,default = json_default)
  logging.debug('{0}[{1}]<-[{2}]'.format(key,name,response))
  return response
 return wrapper

def get_api(key,callback,name):
 def  wrapper(self,*args,**kw):
  answer = {}
  callback(self,answer)
  return dumps(answer)
 return wrapper

class APIHandlerMetaClass(HandlerMetaClass):
 '''
 This metaclass imposes additional requirements on a GET and POST methods of a class its applied to.
 '''
 def __new__(cls,name,bases,attrs):
  attrs['action'] = attrs.get('POST',None)

  api_decorators = { 'GET' : get_api, 'POST': post_api }
  [ attrs.__setitem__(key,api_decorators[key](key,attrs[key],name))
    for key in api_decorators.keys()
    if key in attrs ]

  return type.__new__(cls, name, bases, attrs)

class APIHandler(Handler):
 __metaclass__ = APIHandlerMetaClass

 need_server = config.read_api_requires_server

 readers = []