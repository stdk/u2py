from base import TestCardBase,DATE_FORMAT
from datetime import datetime,timedelta

class TransportCard(TestCardBase):
 def test_init(self):
  pass

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()