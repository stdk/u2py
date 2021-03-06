﻿from contextlib import closing

from handlers_base import APIHandler
import config

from u2py.interface import Reader
from u2py.mfex import ReaderError
from process_reader import ProcessReader,IPCError

__all__ = ['reader_detect','reader_save','reader_load']

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

 @staticmethod
 def identify_port(port):
  try:
   with closing(Reader(port,explicit_error = True)) as reader:
    return port,reader.version(),reader.sn()
  except (ReaderError,IOError):
   return None

 @staticmethod
 def identify_port_remote(port):
  try:
   with closing(ProcessReader(path = port)) as reader:
    answer = reader.apply('webapi.version.version')
    return port,answer['version'],answer['sn']
  except (KeyError,IPCError):
   return None

 def POST(self, answer={}, **kw):
  from serial.tools import list_ports

  backup_readers = APIHandler.readers
  APIHandler.readers = []
  for reader in backup_readers:
   reader.close()

  readers_info = filter(lambda x:x,[self.identify_port_remote('\\\\.\\' + com[0])
                                    for com in list_ports.comports()])
  readers_info.sort(key = lambda (port,_1,_2): port)
  answer['readers'] = readers_info
  APIHandler.readers = [ProcessReader(path = path) for path,version,sn in readers_info]
  [reader.open() for reader in APIHandler.readers]

class reader_save(APIHandler):
 url = '/api/reader/save'

 need_server = config.read_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        "path"   : 'строка, путь к файлу, куда будет сохранено состояние считывателя'
    },
    'response': {
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader, path = None, answer={}, **kw):
  reader.save(path)

class reader_load(APIHandler):
 url = '/api/reader/load'

 need_server = config.read_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        "path"   : 'строка, путь к файлу, откуда будет загружено состояние считывателя'
    },
    'response': {
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader, path = None, answer={}, **kw):
  reader.load(path)