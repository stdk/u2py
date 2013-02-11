from handlers_base import APIHandler
import config

from u2py.interface import Reader,VERSION
from adbk.state import State

class register_contract(APIHandler):
 url = '/api/version'

 need_server = config.read_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек, присутствие этого параметра означает запрос именно его версии; без указания этого параметра результатом будет версия ПО сервиса',
    },
    'response': {
        'sn': 'строка, набор байт в шестнадцатеричном виде разделенных пробелом, серийный номер считывателя БК, версия которого опрашивается (присутствует если указан ключ reader в запросе',
        'version': 'массив чисел, версия ПО запрашиваемого объекта',
        'stoplist': 'число, версия стоплиста установленного в сервис',
        'error': 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader,answer={},**kw):
  if reader:
   answer.update({
    'sn'     : reader.sn(),
    'version': reader.version()
   })
  else:
   answer['version'] = VERSION
   answer['stoplist'] = State.get_stoplist_version()

