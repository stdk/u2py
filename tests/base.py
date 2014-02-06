import sys
import urllib2
import json
import unittest

DATE_FORMAT = '%d/%m/%y'
TIME_FORMAT = '%H:%M:%S'

HOST = '127.0.0.1'
PORT = 1000

class TestBase(unittest.TestCase):
 def send_command(self,api_url,request,error = None,check = True):
  '''
  Default behaviour checks for correct command execution.
  '''
  json_request = json.dumps(request) if not isinstance(request,str) else request
  #print >> sys.stderr, api_url, json_request

  f = urllib2.urlopen('http://%s:%i%s' % (HOST,PORT,api_url),data = json_request)

  json_response = json.loads(f.read())

  if check:
   if error != None:
    json_error = json_response['error']['type']
    self.assertTrue(json_error in error or json_error == error)
   else:
    self.assertEqual(json_response['error'],error)

  return json_response

class TestCardBase(TestBase):
 def scan(self,**kw):
  return self.send_command('/api/scan',self.base_request,**kw)

 def edrpou(self, value, check=False, **kw):
  request = {'edrpou': value, 'check': check}
  request.update(self.base_request)
  return self.send_command('/api/config/edrpou', request, **kw)

 def init_transport_card(self,request):
  request.update(self.base_request)
  return self.send_command('/api/card/init',request)

 def options(self, request, **kw):
  request.update(self.base_request)
  return self.send_command('/api/card/options', request, **kw)

 def clear_card(self):
  return self.send_command('/api/card/clear',self.base_request)

 def setUp(self):
  self.base_request = {'reader': 0}

  A = self.scan(check = False)
  if A['error'] != None:
   self.assertNotEqual(A['error']['type'],'CardError')

  self.base_request['sn'] = A['sn']

  self.clear_card()
  C = self.scan(error = ['SectorReadError', 'CRCError'])
  self.assertEqual(C['sn'],self.base_request['sn'])

 def tearDown(self):
  self.clear_card()