from handlers_base import APIHandler
import config

from u2py import transport_card
from u2py import purse

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

