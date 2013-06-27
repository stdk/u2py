'''
For this test we assume there is card present in reader field.
This can be achieved either by using File implementation of reader
or manually bringing card into actual reader field.
'''
from base import TestBase

from gevent import Timeout
from gevent.server import StreamServer,DatagramServer
from gevent.wsgi import WSGIServer

class Notifications(TestBase):
 MAX_RESPONSE_COUNTER = 3
 TIMEOUT = 3

 def setUp(self):
  self.host = '127.0.0.1'
  self.port = 4000

 def init(self,protocol):
  self.callback = '%s://%s:%i' % (protocol,self.host,self.port)
  self.sn = self.send_command('/api/scan',{ 'reader': 0 },check = False)['sn']

  self.send_command('/api/scan/notify', {
   'reader': 0,
   'callback': self.callback,
   'action': 'add',
   'sn': self.sn
  })

 def tearDown(self):
  self.send_command('/api/scan/notify', {
   'reader': 0,
   'callback': self.callback,
   'action': 'remove'
  })

 def test_tcp_notification(self):
  self.init('tcp')

  response = []
  def handler(socket,address):
   self.assertEquals(address[0],self.host)
   response.append(socket.recv(128))

  with Timeout(self.TIMEOUT,False):
   StreamServer((self.host,self.port), handler).serve_forever()

  self.assertTrue(all(str(self.sn) == sn for sn in response))

 def test_udp_notification(self):
  self.init('udp')

  response = []
  def handler(data,address):
   self.assertEquals(address[0],self.host)
   response.append(data)

  with Timeout(self.TIMEOUT,False):
   DatagramServer((self.host,self.port), handler).serve_forever()

  self.assertGreater(len(response),0)
  self.assertTrue(all(str(self.sn) == sn for sn in response))

 def test_http_notification(self):
  self.init('http')

  response = []
  def handler(environ, start_response):
   response.append(environ['wsgi.input'].read())

   start_response('200 OK', [('Content-type', 'text/plain')])
   return ''

  with Timeout(self.TIMEOUT,False):
   WSGIServer((self.host, self.port), handler).serve_forever()

  self.assertTrue(all(str(self.sn) == sn for sn in response))

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()