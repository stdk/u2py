﻿#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')

import config
import web
from json import JSONEncoder,dumps,loads
from inspect import getargspec
from sys import platform
if platform == 'win32':
 from time import clock as clock

if platform == 'linux2':
 from time import time as clock

from u2py.config import logging,reader_path
from u2py.mfex import MFEx
from u2py.interface import Reader
from adbk.state import State

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

def prepare_request(post_data,readers,required_args=None):
 if post_data == None: return {}
 try: request =  loads(post_data)
 except Exception as e: raise JsonError("{0}: {1}".format(e.__class__.__name__,e))

 if required_args != None:
  for arg in required_args:
   if arg not in request:
    raise MissingParameterError("Missing parameter: {0}".format(arg))

 reader_id = request.get('reader',None)
 request['reader'] = None if reader_id == None else readers[reader_id]
 return request

def api_callback(self,callback,required_args=None,post_data = None):
 #currently, we allow api to be called crossdomain
 web.header('Access-Control-Allow-Origin','*')

 answer = { 'error' : None }
 try:
  answer['is_server_present'] = State.is_server_present()
  if self.need_server and not answer['is_server_present']:
   raise NoServerError('This operation requires vestibule server present')

  request = prepare_request(post_data,self.readers,required_args)

  clock_begin = clock()
  callback(self,answer=answer,**request)
  answer['time_elapsed'] = clock() - clock_begin
 except MFEx as e:
  answer['error'] = e
 except Exception as e:
  answer['error'] = { 'type': unicode(e.__class__.__name__), 'message': str(e) }
 return answer

def post_api(key,callback,name):
 argspec = getargspec(callback)
 required_args = argspec.args[1:-len(argspec.defaults)]

 def wrapper(self,*args,**kw):
  post_data = web.data()
  logging.debug('{0}[{1}]->[{2}]'.format(key,name,post_data))

  answer = api_callback(self,callback,required_args,post_data)

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
  [ attrs.__setitem__(key,api_decorators[key](key,attrs[key],name))
    for key in api_decorators.keys()
    if key in attrs ]

  return type.__new__(cls, name, bases, attrs)

class APIHandler(Handler):
 __metaclass__ = APIHandlerMetaClass

 need_server = config.read_api_requires_server

 readers = [Reader(**kw) for kw in reader_path]

class reader_detect(APIHandler):
 url = '/api/reader/detect'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {},
    'response': {
        "readers": "список последовательных портов, идентифицированных как доступные",
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self, answer={}, **kw):
  from serial.tools import list_ports
  from u2py.mfex import ReaderError

  def identify_port(port):
   try:
    reader = Reader(port,explicit_error = True)
    version,sn = reader.version(),reader.sn()
    return port,version,sn
   except ReaderError:
    return None

  [reader.close() for reader in APIHandler.readers]
  readers = filter(lambda x:x,[identify_port('\\\\.\\' + com[0]) for com in list_ports.comports()])
  readers.sort(key = lambda (port,_1,_2): port)
  answer['readers'] = readers
  APIHandler.readers = [Reader(reader[0]) for reader in readers]
