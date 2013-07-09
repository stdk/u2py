from handlers_base import APIHandler
import config
from json import dumps

from socket import AF_INET,SOCK_DGRAM
from gevent import spawn,sleep,socket
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

 def parse_callback(self, callback, senders):
  try:
   self.url = urlparse(callback)
   self.sender = senders[self.url.scheme]
  except IndexError: raise UnsupportedProtocolError()
  except ValueError: raise IncorrectCallbackError()

 def notify(self, pool, sn, **kw):
  if self.sn != None and self.sn != sn: return
  kw['sn'] = sn
  pool.apply_async(self.sender,args = (self.url,dumps(kw)) )

 @staticmethod
 def send_tcp(url, data):
  host,port = url.netloc.split(':')
  s = socket.create_connection((host,int(port)))
  s.send(data + '\n')

 @staticmethod
 def send_udp(url, data):
  host,port = url.netloc.split(':')
  s = socket.socket(AF_INET,SOCK_DGRAM)
  s.sendto(data + '\n',(host,int(port)))

 @staticmethod
 def send_http(url, data):
  urlopen(url.geturl(),data = data + '\n')

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
   #print self.notifications
   for reader_id in self.notifications.keys():
    try:
     reader = APIHandler.readers[reader_id]
     answer = reader.apply('webapi.scan.scan',kwds = {'fast': True})
     sn = answer.get('sn',None)
     if sn:
      notifiers = self.notifications.get(reader_id,{})
      [n.notify(self.pool, sn = sn, reader = reader_id)
       for n in notifiers.values()]
     else:
      print answer['error']
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
    'reader'  : [
     'опциональный параметр; число, индекс считывателя бесконтактных карточек.',
     'В случае отсутствия этого параметра, нотификация будет установлена для всех считывателей в системе'
    ],
    'sn'      : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
    'action'  : 'строка, действие над нотификацией (add/remove)',
    'callback': 'строка, адрес обратного вызова в виде URL',
   },
   'response': {
    "error": 'Информация об ошибке, возникшей при выполнении вызова API.',
   }
  })

 def POST(self, action, callback, sn = None, answer = {}, **kw):
  ids = [kw['reader']] if 'reader' in kw else range(len(APIHandler.readers))
  if action == 'add':
   [self.notifier.add_notification(r, callback = callback, sn = sn) for r in ids]
  if action == 'remove':
   [self.notifier.remove_notification(r, callback = callback) for r in ids]