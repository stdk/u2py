from handlers_base import APIHandler
import config

from u2py import transport_card
from u2py import journey
from u2py import purse
from u2py import staff
from u2py.events import EVENT_CONTRACT,EVENT_CONTRACT_ZALOG,EVENT_ENCASHMENT

class WrongPasswordError(Exception):
 def __str__(self):
  return "Given password is incorrect"

class register_contract(APIHandler):
 url = '/api/register/contract'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек'
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000000000000000, строка',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader,amount,answer={},**kw):
  card = reader.scan()
  answer['sn'] = card.sn.sn7()
  transport_card.validate(card)
  answer['aspp'] = str(card.aspp)

  transport_card.set_deposit(card)

class register_cashier(APIHandler):
 url = '/api/register/cashier'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'password': 'строка, пароль к данному киоску'
    },
    'response': {
        'sn': 'Серийный номер бесконтактной карточки, число',
        'aspp': 'АСПП номер транспортной карточки вида 0000 0000 0000 0000, строка',
        'staff': 'информация о служебном контракте',
        'personal': 'персональные данные служебного контракта',
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader,password,answer={},**kw):
  card = reader.scan()
  answer['sn'] = card.sn.sn7()
  transport_card.validate(card)
  answer['aspp'] = str(card.aspp)

  answer['staff'] = staff.read(card)
  answer['personal'] = staff.read_personal_info(card)

  from u2py import config
  if config.password != password: raise WrongPasswordError()

  config.cash_card_sn = card.sn.sn8()
  config.cash_card_aspp = str(card.aspp)

class register_encashment(APIHandler):
 url = '/api/register/encashment'

 need_server = config.write_api_requires_server

 def GET(self,answer={}):
  answer.update({
    'request': {
        'reader' : 'число, индекс считывателя бесконтактных карточек',
        'amount'     : 'общая выручка киоска на момент',
        'tag_amount' : 'выручка киоска за жетоны на момент инкассации (входит в amount)',
    },
    'response': {
        "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
    }
  })

 def POST(self,reader,amount,tag_amount,answer={},**kw):
  EVENT_ENCASHMENT(Amount = amount, Value = tag_amount).save()
