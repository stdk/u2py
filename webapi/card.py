from handlers_base import APIHandler
import config

from u2py import transport_card
from u2py import purse

class card_init(APIHandler):
 url = '/api/card/init'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader'  : 'число, индекс считывателя бесконтактных карточек',
        'sn'      : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
        'aspp'    : 'строка, АСПП номер транспортной карточки вида 0000000000000000',
        'end_date': 'опциональный параметр; дата завершения валидности транспортной карточки, строка в формате DD/MM/YY',
        'resource': 'опциональный параметр; ресурс транспортной карточки, число, 8 байт',
        'pay_unit': 'опциональный параметр; код валюты, число, 2 байта',
        'status'  : 'опциональный параметр; статус карточки, число, 1 байт',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })


 def POST(self,reader, aspp, sn = None, answer={}, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()
  transport_card.init(card,aspp=aspp, **kw)

class card_options(APIHandler):
 url = '/api/card/options'

 need_server = config.write_api_requires_server

 def GET(self, answer={}):
  answer.update({
    'request': {
        'reader'  : 'число, индекс считывателя бесконтактных карточек',
        'sn'      : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
        'aspp'    : 'опциональный параметр; строка, АСПП номер транспортной карточки вида 0000000000000000',
        'end_date': 'опциональный параметр; дата завершения валидности транспортной карточки, строка в формате DD/MM/YY',
        'resource': 'опциональный параметр; ресурс транспортной карточки, число, 8 байт',
        'pay_unit': 'опциональный параметр; код валюты, число, 2 байта',
        'status'  : 'опциональный параметр; статус карточки, число, 1 байт',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader, sn = None, answer={}, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()
  transport_card.edit(card,**kw)

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

class InequalityError(Exception):
 def __init__(self, message):
  super(InequalityError,self).__init__(message)

class config_edrpou(APIHandler):
 url = '/api/config/edrpou'

 def GET(self, answer={}):
  answer.update({
   'request': {
        'reader': 'число, индекс считывателя бесконтактных карточек, настройка ЕДРПОУ будет применена только к процессу этого считывателя',
        'edrpou': 'строка, до 10 цифр, код предприятия в BCD-формате',
		'check': 'опциональный параметр, логическое значение указывающее режим работы команды'
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self, reader, edrpou, check=False, answer={}, **kw):
  edrpou = edrpou.rjust(10, '0')
  edrpou = [int(edrpou[2*i:2*i+2], 16) for i in xrange(5)]

  if check and edrpou != transport_card.EDRPOU:
   raise InequalityError('EDRPOU values are not equal')
  else:
   transport_card.EDRPOU = edrpou

class purse_refill(APIHandler):
 url = '/api/purse/refill'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'amount' : 'сумма, на которую необходимо пополнить кошелек, в копейках',
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000000000000000, строка',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self, reader, amount, sn = None, answer={}, **kw):
   card = reader.scan(sn)
   answer['sn'] = card.sn.sn7()
   transport_card.validate(card)
   answer['aspp'] = str(card.aspp)

   purse.change_value(card, int(amount))
