'''
This test validates behaviour of /api/version depending on
presence of |reader| request key.
'''
from base import TestBase

class Version(TestBase):
 def test_reader_version(self):
  A = self.send_command('/api/version',{ 'reader': 0 })
  self.assertTrue('version' in A)
  self.assertTrue('sn' in A)

 def test_service_version(self):
  A = self.send_command('/api/version',{})
  self.assertTrue('version' in A)
  self.assertFalse('sn' in A)

 def test_service_version_reader_none(self):
  A = self.send_command('/api/version',{ 'reader': None })
  self.assertTrue('version' in A)
  self.assertFalse('sn' in A)

 def test_missing_reader_version(self):
  A = self.send_command('/api/version', { 'reader': 255 },'IndexError')

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()