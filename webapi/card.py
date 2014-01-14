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
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
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
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
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
  d = 'dynamic'
  sectors = [(1, 2,s),( 2,3,s),( 3,7,s),( 4,7,s),
             (5, 6,s),( 9,4,s),(10,5,s),(11,8,s),
             (6,21,s),(12,9,s),(13,27,d),(14,27,d)]
  transport_card.clear(card,sectors)

class card_plus_perso(APIHandler):
 url = '/api/card/plus/perso'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader, sn = None, answer={}, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()

  card.mfplus_personalize()

class config_edrpou(APIHandler):
 url = '/api/config/edrpou'

 def GET(self, answer={}):
  answer.update({
   'request': {
        'edrpou': 'строка, до 10 цифр, код предприятия в BCD-формате'
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

  def POST(self, edrpou, answer={}):
   edrpou = edrpou.rjust(10, '0')
   edrpou = []

   transport_card.EDRPOU = [int(edrpou[2*i:2*i+2], 16) for i in xrange(5)]

   print transport_card.EDRPOU

   assert(len(transport_cardd.EDROU), 5)