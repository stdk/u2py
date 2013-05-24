from handlers_base import APIHandler

from u2py import transport_card
from u2py.card_event import read as read_card_events

class card_event(APIHandler):
 url = '/api/card_event'

 def GET(self,answer={}):
  answer.update({
   'request': {
    'reader' : 'число, индекс считывателя бесконтактных карточек',
    'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
   },
   'response': {
    'error': 'Информация об ошибке, возникшей при выполнении вызова API.',
    'sn': 'Серийный номер бесконтактной карточки, число',
    'aspp': 'АСПП номер транспортной карточки, строка вида 0000000000000000',
    'events': 'список событий на карточке'
   }
  })

 def POST(self, reader, sn = None, answer={}, **kw):
  card = reader.scan(sn)
  answer['sn'] = card.sn.sn7()

  transport_card.validate(card)
  answer['aspp'] = str(card.aspp)

  answer['events'] = read_card_events(card)