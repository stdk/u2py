from base import TestCardBase,DATE_FORMAT
from datetime import datetime,timedelta

DEFAULT_PAY_UNIT = 0x9000

class TransportCard(TestCardBase):
 def test_init(self):
  aspp = '0123456789abcdef'
  self.init_transport_card({'aspp': aspp})

  A = self.scan()

  end_date = datetime.now() + timedelta(days=365,hours=6) * 5 # + 5 years from now
  self.assertEqual(A['end_date'],end_date.strftime(DATE_FORMAT))
  self.assertEqual(A['deposit'],0)
  self.assertEqual(A['contracts'],[])
  self.assertEqual(A['purse_value'],0)
  self.assertEqual(A['aspp'],aspp)
  self.assertEqual(A['resource'], 0)
  self.assertEqual(A['pay_unit'], DEFAULT_PAY_UNIT)
  self.assertEqual(A['status'], 1)

 def test_init_with_options(self):
  request = {
    'aspp'    : 'f'*16,
    'end_date': datetime.now().strftime('%d/%m/%y'),
    'resource': 0xFFFFFFFFFFFFFFFF,
    'pay_unit': 0xFFFF,
  }
  self.init_transport_card(request)

  A = self.scan()

  self.assertEqual(A['end_date'],request['end_date'])
  self.assertEqual(A['resource'], request['resource'])
  self.assertEqual(A['pay_unit'], request['pay_unit'])
  self.assertEqual(A['status'], 1)
  self.assertEqual(A['deposit'],0)
  self.assertEqual(A['contracts'],[])
  self.assertEqual(A['purse_value'], 0)
  self.assertEqual(A['aspp'],request['aspp'])

 def test_init_with_status_option(self):
  request = {
    'aspp'    : 'f'*16,
    'status'  : 0xFF,
  }
  self.init_transport_card(request)

  A = self.scan(error='StatusError')

 def test_edrpou1(self):
  aspp = 'a' * 16
  self.init_transport_card({'aspp': aspp})
  A = self.scan()
  self.assertEqual(A['aspp'], aspp)

  edrpou = '0123456789'
  self.edrpou(edrpou, check=True, error='InequalityError')
  self.edrpou(edrpou)

  B = self.scan(error = 'DataError')
  R = self.edrpou(edrpou, check=True)

 def test_edrpou2(self):
  edrpou = '123'
  self.edrpou(edrpou, check=True, error='InequalityError')
  self.edrpou(edrpou)

  aspp = 'b' * 16
  self.init_transport_card({'aspp': aspp})

  A = self.scan()
  self.assertEqual(A['aspp'], aspp)

  self.edrpou(edrpou, check=True)

  self.edrpou('456')
  B = self.scan(error = 'DataError')
  self.edrpou(edrpou, check=True, error='InequalityError')

 def test_options(self):
  aspp = 'c' * 16
  self.init_transport_card({'aspp': aspp})

  A = self.scan()

  end_date = datetime.now() + timedelta(days=365,hours=6) * 5 # + 5 years from now
  self.assertEqual(A['end_date'],end_date.strftime(DATE_FORMAT))
  self.assertEqual(A['deposit'],0)
  self.assertEqual(A['contracts'],[])
  self.assertEqual(A['purse_value'],0)
  self.assertEqual(A['aspp'],aspp)
  self.assertEqual(A['resource'], 0)
  self.assertEqual(A['pay_unit'], DEFAULT_PAY_UNIT)
  self.assertEqual(A['status'], 1)

  request = {
    'aspp'    : 'd'*16,
    'end_date': datetime.now().strftime('%d/%m/%y'),
    'resource': 0xFFFFFFFFFFFFFFFF,
    'pay_unit': 0xFFFF,
  }
  self.options(request)

  B = self.scan()

  self.assertEqual(B['aspp'],request['aspp'])
  self.assertEqual(B['end_date'],request['end_date'])
  self.assertEqual(B['resource'], request['resource'])
  self.assertEqual(B['pay_unit'], request['pay_unit'])
  self.assertEqual(B['status'], 1)
  self.assertEqual(B['deposit'],0)
  self.assertEqual(B['contracts'],[])
  self.assertEqual(B['purse_value'], 0)

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()