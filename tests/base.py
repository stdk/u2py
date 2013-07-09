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
  #print >> sys.stderr, json.dumps(json_response,indent = 4)

  if check:
   if error != None:
    self.assertEqual(json_response['error']['type'],error)
   else:
    self.assertEqual(json_response['error'],error)

  return json_response

class TestCardBase(TestBase):
 def scan(self,**kw):
  return self.send_command('/api/scan',self.base_request,**kw)

 def init_transport_card(self,aspp):
  request = {'aspp': aspp}
  request.update(self.base_request)
  return self.send_command('/api/card/init',request)

 def clear_card(self):
  return self.send_command('/api/card/clear',self.base_request)

 def setUp(self):
  self.base_request = {'reader': 0}

  A = self.scan(check = False)
  if A['error'] != None:
   self.assertNotEqual(A['error']['type'],'CardError')

  self.base_request['sn'] = A['sn']

  self.clear_card()
  C = self.scan(error = 'SectorReadError')
  self.assertEqual(C['sn'],self.base_request['sn'])

 def tearDown(self):
  self.clear_card()