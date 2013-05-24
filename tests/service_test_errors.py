from base import TestBase

class Errors(TestBase):
 missing_err = 'MissingParameterError'
 json_err = 'JsonError'
 type_err = 'TypeError'
 index_err = 'IndexError'

 def test_json_error(self):
  self.send_command('/api/scan','123123131313123' , self.type_err)
  self.send_command('/api/scan','{ "reader": 0, }',self.json_err)
  self.send_command('/api/scan','{ 1231231 }'     ,self.json_err)

 def test_missing_parameter_error(self):
  self.send_command('/api/scan'     ,[1,2,3,4],self.missing_err)
  request = { 'reader': 0 }
  self.send_command('/api/scan',{},self.missing_err)
  self.send_command('/api/card/init',request,self.missing_err)
  self.send_command('/api/journey/refill',request,self.missing_err)
  self.send_command('/api/term/refill',request,self.missing_err)
  self.send_command('/api/register/cashier',request,self.missing_err)
  self.send_command('/api/register/encashment',request,self.missing_err)

 def test_missing_reader(self):
  self.send_command('/api/scan',{'reader': 2 },self.index_err)
  self.send_command('/api/scan',{'reader': -2 },self.index_err)


if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()