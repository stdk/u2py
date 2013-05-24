from base import TestCardBase,DATE_FORMAT
from datetime import datetime,timedelta

class TransportCard(TestCardBase):
 def test_init(self):
  aspp = '0123456789abcdef'
  self.init_transport_card(aspp)

  A = self.scan()

  end_date = datetime.now() + timedelta(days=365,hours=6) * 5 # + 5 years from now
  self.assertEqual(A['end_date'],end_date.strftime(DATE_FORMAT))
  self.assertEqual(A['deposit'],0)
  self.assertEqual(A['contracts'],[])
  self.assertEqual(A['purse_value'],0)
  self.assertEqual(A['purse_value'],0)
  self.assertEqual(A['aspp'],aspp)

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()