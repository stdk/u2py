'''
For this test we assume there is card present in reader field.
This can be achieved either by using File implementation of reader
or manually bringing card into actual reader field.
'''
from base import TestBase

from gevent import Timeout
from gevent.server import StreamServer,DatagramServer
from gevent.wsgi import WSGIServer
import json
from socket import gethostbyname,gethostname


class Notifications(TestBase):
 TIMEOUT = 3

 def setUp(self):
  self.host = gethostbyname(gethostname())
  self.port = 4000
  self.reader = 0

 def init(self,protocol):
  self.callback = '%s://%s:%i' % (protocol,self.host,self.port)
  self.sn = self.send_command('/api/scan',{ 'reader': 0 },check = False)['sn']

  self.send_command('/api/scan/notify', {
   'reader': self.reader,
   'callback': self.callback,
   'action': 'add',
   'sn': self.sn
  })

 def tearDown(self):
  self.send_command('/api/scan/notify', {
   'reader': self.reader,
   'callback': self.callback,
   'action': 'remove'
  })

 def test_tcp_notification(self):
  self.init('tcp')

  response = []
  def handler(socket,address):
   r = json.loads(socket.recv(128))
   self.assertEquals(r,{'reader': self.reader, 'sn' : self.sn})
   response.append(r)

  with Timeout(self.TIMEOUT,False):
   StreamServer((self.host,self.port), handler).serve_forever()

  self.assertGreater(len(response),0)

 def test_udp_notification(self):
  self.init('udp')

  response = []
  def handler(data,address):
   r = json.loads(data)
   self.assertEquals(r,{'reader': self.reader, 'sn' : self.sn})
   response.append(r)

  with Timeout(self.TIMEOUT,False):
   DatagramServer((self.host,self.port), handler).serve_forever()

  self.assertGreater(len(response),0)

 def test_http_notification(self):
  self.init('http')

  response = []
  def handler(environ, start_response):
   r = json.loads(environ['wsgi.input'].read())
   self.assertEquals(r,{'reader': self.reader, 'sn' : self.sn})
   response.append(r)

   start_response('200 OK', [('Content-type', 'text/plain')])
   return ''

  with Timeout(self.TIMEOUT,False):
   WSGIServer((self.host, self.port), handler).serve_forever()

  self.assertGreater(len(response),0)

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()