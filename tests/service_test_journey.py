from base import TestCardBase,DATE_FORMAT,TIME_FORMAT
from datetime import datetime,timedelta
import random
import sys

JOURNEY_COST = 200
MAX_JOURNEYS = 50

class JourneyContract(TestCardBase):
 def init(self,deposit):
  request = {'deposit': deposit}
  request.update(self.base_request)
  return self.send_command('/api/journey/init',request)

 def remove(self):
  return self.send_command('/api/journey/remove',self.base_request)

 def refill(self,amount,fast = False):
  request = {'amount': amount, 'fast': fast}
  request.update(self.base_request)
  return self.send_command('/api/journey/refill',request)

 def setUp(self):
  super(JourneyContract,self).setUp()

  self.aspp = '1111222233334444'
  self.init_transport_card(aspp = '1111222233334444')

  self.deposit = 123
  self.init(self.deposit)

 def test_init(self):
  now = datetime.now()

  A = self.scan()
  self.assertEqual(A['aspp'],self.aspp)
  self.assertEqual(A['deposit'],self.deposit)
  self.assertEqual('journey' in A,True)

  journey = A['journey']
  self.assertEqual(journey['status'],1)
  self.assertEqual(journey['transaction'],1)
  self.assertEqual(journey['journeys'],0)
  self.assertEqual(journey['validated_date'],now.strftime(DATE_FORMAT))

 def test_refill(self):
  now = datetime.now()

  amount = 500
  A = self.refill(amount,fast = True)
  self.assertEqual(A['amount_used'],(amount / JOURNEY_COST) * JOURNEY_COST)

  B = self.scan()
  self.assertEqual(B['purse_value'],amount % JOURNEY_COST)
  self.assertEqual('journey' in B,True)

  journey = B['journey']
  self.assertEqual(journey['status'],1)
  self.assertEqual(journey['transaction'],2)
  self.assertEqual(journey['journeys'],amount / JOURNEY_COST)
  self.assertEqual(journey['validated_date'],now.strftime(DATE_FORMAT))

 def test_remove(self):
  self.remove()

  A = self.scan()
  self.assertEqual(A['purse_value'],0)
  self.assertEqual(A['contracts'],[])
  self.assertEqual('journey' in A,False)
  self.assertEqual(A['deposit'],0)

 def test_multiple_refill(self):
  amounts = [100]*4 + [200,500,1000,2000]
  random.shuffle(amounts)
  sys.stdout.write(str(amounts) + ' ')

  class R(object):
   def __init__(self,test,excess = 0):
    self.test = test
    self.excess = excess
   def refill(self,amount):
    A = self.test.refill(amount = amount,fast = True)
    actual_amount = self.excess + amount
    self.test.assertEqual(A['amount_used'],(actual_amount / JOURNEY_COST) * JOURNEY_COST)
    self.excess = actual_amount % JOURNEY_COST
    return 1 if A['amount_used'] > 0 else 0

  r = R(self)
  transactions = sum([r.refill(amount) for amount in amounts]) + 1
  total = sum(amounts)
  self.assertEqual(r.excess,total % JOURNEY_COST)

  B = self.scan()
  self.assertEqual(B['purse_value'],total % JOURNEY_COST)
  self.assertEqual('journey' in B,True)

  journey = B['journey']
  self.assertEqual(journey['status'],1)
  self.assertEqual(journey['transaction'],transactions)
  self.assertEqual(journey['journeys'],total / JOURNEY_COST)
  self.assertEqual(journey['validated_date'],datetime.now().strftime(DATE_FORMAT))

if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()