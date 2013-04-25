from handlers_base import APIHandler
import config

from u2py.interface import STANDARD,ULTRALIGHT
from u2py import transport_card
from u2py import term
from u2py import purse
from u2py import ultralight

def handle_unknown(card,answer,**kw):
 raise Exception('Unknown card type')

class term_refill(APIHandler):
 url = '/api/term/refill'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'amount' : 'сумма, на которую необходимо пополнить контракт, в копейках'
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

 def handle_standard(self,card,answer,amount=0,fast=False):
  transport_card.validate(card)
  answer['aspp'] = str(card.aspp)

  if not fast:
   answer['before'] = {
     'purse_value' : purse.get_value(card),
     'term'        : term.read(card)
   }

  answer['amount_used'] = term.refill(card,amount)

  if not fast:
   answer['after'] = {
    'purse_value' : purse.get_value(card),
    'term'        : term.read(card)
   }

 def handle_ultralight(self,card,answer,amount=0,fast=False):
  answer['before'] = { 'term' : ultralight.read(card) }
  answer['aspp'] = str(card.aspp)

  ultralight.activate(card,amount)

  answer['after'] = { 'term' : ultralight.read(card) }

 def POST(self, reader, amount, answer={}, fast=False, **kw):
   card = reader.scan()
   answer['sn'] = card.sn.sn7()
   answer['ultralight'] = card.type == ULTRALIGHT

   {
    STANDARD   : self.handle_standard,
    ULTRALIGHT : self.handle_ultralight
   }.get(card.type,handle_unknown)(card,answer,amount = amount,fast = fast)

class term_available(APIHandler):
 url = '/api/term/available'

 need_server = config.read_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек'
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000000000000000, строка',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API. Если возникшая ошибка принадлежит типу TimeError, это означает, что данный контракт на срок действия не подлежит пополнению, т.к. срок завершения его валидности истек.',
        "available": {
            "cost": "стоимость пополнения на указанный срок",
            "validity_begin_date": "дата начала валидности контракта после пополнения в формате %d/%m/%y",
            "validity_end_date": "дата начала валидности контракта после пополнения в формате %d/%m/%y"
        }
    }
  })

 def handle_standard(self,card,answer):
   transport_card.validate(card)
   answer['aspp'] = str(card.aspp)

   sector,static = term.read_static(card)

   cost,(begin,end) = term.available_refill(static.aid,static.pix)

   # try to refill with current available parameters to let card check itself.
   # This operation is harmless to card without corresponding write.
   static.refill(begin,end)

   begin,end,limit = static.validity()
   answer['available'] = {
    'validity_begin_date': begin,
    'validity_end_date': end,
    'validity_limit_date': limit,
    'cost': cost
   }

 def handle_ultralight(self,card,answer):
  cost,(begin,end) = ultralight.available_refill(card)
  answer['aspp'] = str(card.aspp)

  answer['available'] = {
    'validity_begin_date': begin,
    'validity_end_date': end,
    'validity_limit_date': end,
    'cost': cost
   }

 def POST(self,reader,answer={},**kw):
   card = reader.scan()
   answer['sn'] = card.sn.sn7()
   answer['ultralight'] = card.type == ULTRALIGHT

   {
    STANDARD   : self.handle_standard,
    ULTRALIGHT : self.handle_ultralight
   }.get(card.type,handle_unknown)(card,answer)
