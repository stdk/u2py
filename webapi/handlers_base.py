#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')

import config
import web
from json import JSONEncoder,dumps,loads
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

def prepare_request(post_data,readers):
 request = loads(post_data)
 reader_id = request.get('reader',None)
 request['reader'] = None if reader_id == None else readers[reader_id]
 return request

def api_callback(self,callback,post_data = None):
 #currently, we allow api to be called crossdomain
 web.header('Access-Control-Allow-Origin','*')

 answer = { 'error' : None }
 try:
  answer['is_server_present'] = State.is_server_present()
  if self.need_server and not answer['is_server_present']:
   raise NoServerError('This operation requires vestibule server present')

  request = {} if post_data == None else prepare_request(post_data,self.readers)

  clock_begin = clock()
  callback(self,answer=answer,**request)
  answer['time_elapsed'] = clock() - clock_begin
 except MFEx as e:
  answer['error'] = e
 except Exception as e:
  answer['error'] = { 'type': unicode(e.__class__.__name__), 'message': str(e) }
 return answer

def post_api(key,callback,name):
 def wrapper(self,*args,**kw):
  post_data = web.data()
  logging.debug('{0}[{1}]->[{2}]'.format(key,name,post_data))

  answer = api_callback(self,callback,post_data)

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
