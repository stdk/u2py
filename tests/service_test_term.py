from base import TestCardBase,DATE_FORMAT,TIME_FORMAT
from datetime import datetime,timedelta
import random
import sys

class TermContract(TestCardBase):
 def init(self,deposit):
  request = {'deposit': deposit}
  request.update(self.base_request)
  return self.send_command('/api/term/init',request)

 def remove(self):
  return self.send_command('/api/term/remove',self.base_request)

 def refill(self,amount,fast = False):
  request = {'amount': amount, 'fast': fast}
  request.update(self.base_request)
  return self.send_command('/api/term/refill',request)

 def available(self):
  A = self.send_command('/api/term/available',self.base_request)
  self.assertIn('available',A)
  available = A['available']
  self.assertIn('validity_begin_date',available)
  self.assertIn('validity_end_date',available)
  self.assertIn('validity_limit_date',available)
  self.assertIn('cost',available)
  return (available['validity_begin_date'],
          available['validity_end_date'],
          available['validity_limit_date'],
          available['cost'],)

 def setUp(self):
  super(TermContract,self).setUp()

  self.aspp = '1111222233334444'
  self.init_transport_card({ 'aspp': self.aspp })

  self.deposit = 234
  self.init(self.deposit)

 def test_init(self):
  now = datetime.now()

  A = self.scan()
  self.assertEqual(A['aspp'],self.aspp)
  self.assertEqual(A['deposit'],self.deposit)
  self.assertIn('term',A)

  term = A['term']
  self.assertEqual(term['status'],2) # immediately after refill contract status is 2
  self.assertEqual(term['transaction'],1)
  self.assertEqual(term['validated_date'],now.strftime(DATE_FORMAT))
  self.assertEqual(term['transport_type'],1)

 def test_refill(self):
  now = datetime.now()

  begin,end,limit,cost = self.available()

  A = self.refill(amount = cost, fast = True)
  self.assertEqual(A['amount_used'],cost)

  B = self.scan()
  self.assertEqual(B['purse_value'],0)
  self.assertIn('term',B)

  term = B['term']
  self.assertEqual(term['status'],1)
  self.assertEqual(term['transaction'],3) # 1 transactions from init + 1 from contract activation + 1 from refill
  self.assertEqual(term['validity_begin_date'],begin)
  self.assertEqual(term['validity_begin_date'],begin)
  self.assertEqual(term['validity_end_date'],end)
  self.assertEqual(term['validity_limit_date'],limit)
  self.assertEqual(term['validated_date'],now.strftime(DATE_FORMAT))

 def test_remove(self):
  self.remove()

  A = self.scan()
  self.assertEqual(A['purse_value'],0)
  self.assertEqual(A['contracts'],[])
  self.assertNotIn('term',A)
  self.assertEqual(A['deposit'],0)

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()