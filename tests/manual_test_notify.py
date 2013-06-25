'''
For this test we assume there is card present in reader field.
This can be achieved either by using File implementation of reader
or manually bringing card into actual reader field.
'''
from base import TestBase

from gevent.server import StreamServer

class TcpNotification(TestBase):
 MAX_RESPONSE_COUNTER = 3

 def setUp(self):
  self.host = '127.0.0.1'
  self.port = 4000
  self.callback = 'tcp://%s:%i' % (self.host,self.port)
  self.counter = 0
  self.response = []
  self.sn = self.send_command('/api/scan',{ 'reader': 0 },check = False)['sn']

  self.send_command('/api/scan/notify', {
   'reader': 0,
   'callback': self.callback,
   'action': 'add',
   'sn': self.sn
  })

  self.server = StreamServer((self.host,self.port), self.handle_callback)
  self.server.serve_forever()

 def handle_callback(self,socket,address):
  if self.counter >= self.MAX_RESPONSE_COUNTER: self.server.stop()
  print socket,address
  self.response.append(socket.recv(128))
  self.counter += 1

 def tearDown(self):
  self.send_command('/api/scan/notify', {
   'reader': 0,
   'callback': self.callback,
   'action': 'remove'
  })

 def test_tcp_notification(self):
  print self.response

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()