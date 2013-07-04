from handlers_base import APIHandler
import config

from socket import AF_INET,SOCK_DGRAM
from gevent import spawn,sleep,socket
#from multiprocessing.pool import ThreadPool
from gevent.threadpool import ThreadPool
from urlparse import urlparse
from urllib2 import urlopen

class UnsupportedProtocolError(Exception):
 def __str__(self):
  return 'This protocol is not supported'

class IncorrectCallbackError(Exception):
 def __str__(self):
  return 'Calback does not conform to the correct format'

class Notification(object):
 def __init__(self,callback,sn = None):
  self.sn = sn
  self.parse_callback(callback,{
    'tcp' : Notification.send_tcp,
    'udp' : Notification.send_udp,
    'http': Notification.send_http
  })

 def parse_callback(self,callback,senders):
  try:
   self.url = urlparse(callback)
   self.sender = senders[self.url.scheme]
  except IndexError: raise UnsupportedProtocolError()
  except ValueError: raise IncorrectCallbackError()

 def notify(self,pool,sn):
  if self.sn != None and self.sn != sn: return
  pool.apply_async(self.sender,args =(self.url,str(sn)))

 @staticmethod
 def send_tcp(url,sn):
  host,port = url.netloc.split(':')
  s = socket.create_connection((host,int(port)))
  s.send(str(sn))

 @staticmethod
 def send_udp(url,sn):
  host,port = url.netloc.split(':')
  s = socket.socket(AF_INET,SOCK_DGRAM)
  s.sendto(str(sn),(host,int(port)))

 @staticmethod
 def send_http(url,sn):
  urlopen(url.geturl(),data = sn)

class Notifier(object):
 def __init__(self):
  self.poll_timeout = config.notifier_poll_timeout
  self.notifications = {}
  self.pool = ThreadPool(5)

  spawn(self.run)

 def add_notification(self,reader_id,callback,**kw):
  notification = Notification(callback,**kw)
  if reader_id not in self.notifications:
   self.notifications[reader_id] = {}
  self.notifications[reader_id][callback] = notification

 def remove_notification(self,reader_id,callback):
  del self.notifications[reader_id][callback]
  if not len(self.notifications[reader_id]):
   del self.notifications[reader_id]

 def run(self):
  while True:
   for reader_id,notifications in self.notifications.iteritems():
    try:
     reader = APIHandler.readers[reader_id]
     card = reader.apply(lambda reader: reader.scan(), args = (reader,) )
     if card:
      [n.notify(self.pool,card.sn.sn7()) for n in notifications.values()]
     else:
      print reader.exc_info
    except IndexError:
     del self.notifications[reader_id]

   sleep(self.poll_timeout)


class scan_notify(APIHandler):
 url = '/api/scan/notify'

 need_server = config.read_api_requires_server

 notifier = Notifier()

 def GET(self,answer={}):
  answer.update({
   'request': {
    'reader'  : 'число, индекс считывателя бесконтактных карточек',
    'sn'      : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    'action'  : 'строка, действие над нотификацией (add/remove)',
    'callback': 'строка, адрес обратного вызова в виде URL',
   },
   'response': {
    "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
   }
  })

 def POST(self, reader, action, callback, sn = None, answer = {}, **kw):
  reader_id = self.readers.index(reader)
  if action == 'add':
   self.notifier.add_notification(reader_id, callback = callback, sn = sn)
  if action == 'remove':
   self.notifier.remove_notification(reader_id,callback = callback)