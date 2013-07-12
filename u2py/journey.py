from interface_basis import DumpableBigEndianStructure,DumpableStructure
from interface import DATE,TIME,ByteArray
from mfex import *
from ctypes import *
import purse
from contract import CONTRACT_A
from events import EVENT_CONTRACT_ADD2,EVENT_CONTRACT
import config

SECTOR = 11
KEY = 8
ENCRYPTION = (0xFF,0xA,0xA)

MAX_JOURNEYS = config.max_journeys
JOURNEY_COST = config.journey_cost

AID = 0xD01
PIX = 0x100

class CONTRACT1_DYNAMIC(DumpableStructure):
 '''
 >>> data = h2b("99 41 03 00 05 00 4d 32 f1 dc 01 ef bc 0d c3 f1")
 >>> CONTRACT1_DYNAMIC.validate(data)
 {'validated_time': 17:39:54, 'status': 1, 'transaction': 3, 'validated_date': 25/02/13, 'journeys': 5}
 '''
 _pack_ = 1
 _fields_ = [
    ('_id',              c_uint8),
    ('_version',         c_uint8,6),
    ('_bitmap',          c_uint8,2),
    ('transaction',      c_uint16),
    ('journeys',         c_uint16),
    ('validated_date',   DATE),
    ('validated_time',   TIME),
    ('status',           c_uint8),
    ('_reserved',        ByteArray(2)), #0xbc 0xef
    ('_mac_alg_id'       ,c_uint8,2),
    ('_mac_key_id'       ,c_uint8,6),
    ('_mac'              ,c_uint16),
 ]

 def __init__(self):
  self._id = self.VALID_ID
  self._version = self.VALID_VERSION
  self._bitmap = self.VALID_BITMAP
  self.transaction = 1
  self.journeys = 0
  self.validated_date = DATE()
  self.validated_time = TIME()
  self.status = self.VALID_STATUS
  self._reserved[:] = self.VALID_RESERVED
  self._mac_alg_id = self.VALID_ALG_ID
  self._mac_key_id = self.VALID_KEY_ID
  cast(pointer(self),POINTER(ByteArray(16))).contents.crc16_calc()

 def refill(self,amount):
  '''
  >>> data = h2b("99 41 03 00 05 00 4d 32 f1 dc 01 ef bc 0d c3 f1")
  >>> dynamic = CONTRACT1_DYNAMIC.validate(data)
  >>> dynamic
  {'validated_time': 17:39:54, 'status': 1, 'transaction': 3, 'validated_date': 25/02/13, 'journeys': 5}
  >>> dynamic.refill(0)
  0
  >>> dynamic.refill(500)
  400
  >>> dynamic.validated_date == DATE(),dynamic.validated_time == TIME()
  (True, True)
  >>> dynamic.journeys == 7, dynamic.transaction == 4
  (True, True)
  >>>
  '''
  if amount <= 0: return 0

  value = amount/JOURNEY_COST
  if self.journeys + value > MAX_JOURNEYS:
   value = MAX_JOURNEYS - self.journeys

  self.journeys += value
  self.transaction += 1
  self.validated_date = DATE()
  self.validated_time = TIME()

  return value * JOURNEY_COST

 VALID_ID = 0x99
 VALID_RESERVED = [0xEF,0xBC]
 VALID_VERSION = 1
 VALID_BITMAP = 1
 VALID_STATUS = 1
 VALID_ALG_ID = 1
 VALID_KEY_ID = 3

 @classmethod
 def validate(cls,data):
  if not data.crc16_check(low_endian=1): raise CRCError()
  contract = data.cast(cls)
  if contract._id != cls.VALID_ID or contract.status != cls.VALID_STATUS or\
     not contract._reserved == cls.VALID_RESERVED or\
     contract._bitmap != cls.VALID_BITMAP or \
     contract._version != cls.VALID_VERSION or \
	 contract._mac_alg_id != cls.VALID_ALG_ID or \
	 contract._mac_key_id != cls.VALID_KEY_ID: raise DataError()

  return contract

 def __cmp__(self,other):
  return cmp(self.transaction,other.transaction)

def h2b(s):
 '''
 Accepts space-separated string of hexadecimal byte values and return ByteArray
 with those bytes.
 >>> ret = h2b("99 41 03 00 05 00 4d 32 f1 dc 01 ef bc 0d c3 f1")
 >>> [i for i in ret]
 [153, 65, 3, 0, 5, 0, 77, 50, 241, 220, 1, 239, 188, 13, 195, 241]
 '''
 bytes = [int(i,16) for i in s.split()]
 return ByteArray(len(bytes))(*bytes)

class CONTRACT1_STATIC(DumpableStructure):
 _fields_ = [('data',ByteArray(16))]

 def __init__(self):
  self.data[:] = [0x87,0,0xd0,0x11,0,0x1,0x83,0xe5,0x80,0,0,0x10,0,0,0,0]

 @classmethod
 def validate(cls,data):
  if data[0] != 0x87: raise DataError()
  return data.cast(cls)

def init(card,deposit):
 from transport_card import validate,set_deposit,register_contract

 validate(card)
 set_deposit(card,deposit)

 jsector = CONTRACT_A(CONTRACT1_STATIC,CONTRACT1_DYNAMIC)
 sector = card.sector(num=SECTOR,key=0,enc=ENCRYPTION,read=False)
 sector.data = ByteArray(jsector)

 event = EVENT_CONTRACT(card,AID = AID,PIX = PIX)

 try:
  sector.write()
  sector.set_trailer(KEY)

  register_contract(card,SECTOR,AID,PIX)
 except Exception as e: event.set_error_code(e); raise
 finally: event.save(card)

def remove(card):
 from transport_card import validate,set_deposit,clear,register_contract

 validate(card)
 clear(card,sectors = [(SECTOR,KEY,'static')])
 register_contract(card,SECTOR,0,0)
 set_deposit(card,0)

def read(card):
 sector = card.sector(num=SECTOR,key=KEY,enc=ENCRYPTION)
 contract = CONTRACT_A.validate(sector,CONTRACT1_STATIC,CONTRACT1_DYNAMIC)
 return contract.dynamic.to_dict()

def refill(card,amount):
 '''
 Refills card with journey contract inside reader field.
 `card` argument should be valid card in active state with transport_card.validate
 performed on it. `amount` - summ in cents to be added to transport purse,
 converted to journeys and subsequently removed from transport purse.
 '''
 sector = card.sector(num=SECTOR,key=KEY,enc=ENCRYPTION)
 contract = CONTRACT_A.validate(sector,CONTRACT1_STATIC,CONTRACT1_DYNAMIC)

 purse_value = purse.change_value(card,amount)
 if purse_value < JOURNEY_COST: return 0

 amount_used = contract.dynamic.refill(purse_value)
 purse.change_value(card,-amount_used)
 event = EVENT_CONTRACT_ADD2(card)
 event.AID,event.PIX = AID,PIX
 event.Value = contract.dynamic.journeys
 event.TransactionValue = amount_used / JOURNEY_COST
 event.Amount = amount_used
 event.LocalTransactions = contract.dynamic.transaction

 try:
  card.auth(sector)
  contract.commit(low_endian = 1)
  sector.write(blocks=(1,2))
 except Exception as e: event.set_error_code(e); raise
 finally: event.save(card)

 return amount_used

def test():
 import doctest
 doctest.testmod()

 from interface import Reader
 import transport_card

 card = Reader().scan()

 #transport_card.validate(card=card)

 #init(card)

 #print refill(card,100)

 print read(card)

if __name__ == "__main__":
 test()







