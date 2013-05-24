from handlers_base import APIHandler
import config

from u2py import transport_card
from u2py import journey
from u2py import purse

class journey_refill(APIHandler):
 url = '/api/journey/refill'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'amount' : 'сумма, на которую необходимо пополнить контракт, в копейках',
        'fast'   : 'опциональный параметр; hежим выполнения команды. true - не выполнять генерацию ключей before и after, false - стандартный режим',
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    },
    'response': {
        "after": 'Информация о состоянии контракта и транспортного кошелька после выполнения команды',
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000000000000000, строка',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
        "before": 'Информация о состоянии контракта и транспортного кошелька до выполнения команды',
        "amount_used": 'Сумма, использованная при пополнении кошелька, в копейках'
    }
  })

 def POST(self, reader, amount, sn = None, fast=False, answer={}, **kw):
   card = reader.scan(sn)
   answer['sn'] = card.sn.sn7()
   transport_card.validate(card)
   answer['aspp'] = str(card.aspp)

   if not fast:
    answer['before'] = {
     'purse_value': purse.get_value(card),
     'journey': journey.read(card)
    }

   answer['amount_used'] = journey.refill(card,amount)

   if not fast:
    answer['after'] = {
     'purse_value': purse.get_value(card),
     'journey': journey.read(card)
    }

class journey_init(APIHandler):
 url = '/api/journey/init'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'deposit': 'число, опциональный параметр: залоговая стоимость контракта',
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000000000000000, строка',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self, reader, deposit = None, sn = None, answer={}, fast=False, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()

  journey.init(card,deposit)

  answer['aspp'] = str(card.aspp)

class journey_remove(APIHandler):
 url = '/api/journey/remove'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000000000000000, строка',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self, reader, sn = None, answer={}, fast=False, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()

  journey.remove(card)

  answer['aspp'] = str(card.aspp)