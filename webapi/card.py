from handlers_base import APIHandler
import config

from u2py import transport_card

class card_init(APIHandler):
 url = '/api/card/init'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'aspp'   : 'строка, АСПП номер транспортной карточки вида 0000000000000000',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })


 def POST(self,reader, aspp, sn = None, answer={}, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()
  transport_card.init(card,aspp)

class card_clear(APIHandler):
 url = '/api/card/clear'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader, sn = None, answer={}, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()
  s = 'static'
  sectors = [(1,2,s),(2,3,s),(3,7,s),(4,7,s),(5,6,s),(9,4,s),(10,5,s),(11,8,s)]
  transport_card.clear(card,sectors)