import unittest
import random

import sys
sys.path.append('..')
from u2py import interface

class ReaderBase(unittest.TestCase):
 def setUp(self):
  reader_cfg = {'path': '\\\\.\\COM1', 'baud': 38400, 'impl':'asio' }
  self.reader = interface.Reader(explicit_error = True,**reader_cfg)

 def tearDown(self):
  self.reader.close()
  del self.reader

class Reader(ReaderBase):
 def test_scan(self):
  card = self.reader.scan()
  self.assertIsInstance(card,interface.Card)

class Card(ReaderBase):
 def setUp(self):
  ReaderBase.setUp(self)
  self.card = self.reader.scan()

 def tearDown(self):
  del self.card
  ReaderBase.tearDown(self)

 def test_read_write(self):
  random_data = [random.randint(0,255) for i in range(interface.BLOCK_LENGTH*3)]
  sys.stdout.write(str(random_data) + ' ')
  A = self.card.sector(num = 15,key = 0,method='full')
  A.data[:] = random_data
  A.write()

  B = self.card.sector(num = 15,key = 0,method='full')
  self.assertEqual(B.data,random_data)

  zero_data = [0]*(interface.BLOCK_LENGTH*3)
  B.data[:] = zero_data
  B.write()

  C = self.card.sector(num = 15,key = 0,method='full')
  self.assertEqual(C.data,zero_data)


if __name__ == '__main__':
 import sys
 import unittest
 sys.argv.append('-v')
 unittest.main()