from handlers_base import APIHandler
import config

from u2py.interface import Reader
from u2py.mfex import ReaderError

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
   reader = Reader(port,explicit_error = True)
   version,sn = reader.version(),reader.sn()
   return port,version,sn
  except (ReaderError,IOError):
   return None

 def POST(self, answer={}, **kw):
  from serial.tools import list_ports

  [reader.close() for reader in APIHandler.readers]
  readers = filter(lambda x:x,[self.identify_port('\\\\.\\' + com[0]) for com in list_ports.comports()])
  readers.sort(key = lambda (port,_1,_2): port)
  answer['readers'] = readers
  APIHandler.readers = [Reader(reader[0]) for reader in readers]

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