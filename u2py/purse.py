from ctypes import c_uint8,c_uint16,c_uint32,c_uint64,BigEndianStructure,sizeof
from interface import DumpableStructure,DumpableBigEndianStructure,ByteArray,Reader
from mfex import *
from contract import CONTRACT_A
from events import EVENT_WALLET_OPERATION2

class PURSE_DYNAMIC_DATA(DumpableBigEndianStructure):
 _pack_ = 1
 _fields_ = [('transaction',c_uint16),
             ('value',c_uint32,24),
             ('status',c_uint32,8),
             ('al_status',c_uint8),
             ('reserved',c_uint8*6),
             ('mac_alg_id',c_uint8,2),
             ('mac_key_id',c_uint8,6),
             ('mac_auth',c_uint16)]


 @classmethod
 def validate(cls,data):
  if not data.crc16_check(low_endian=0): raise CRCError()
  return data.cast(cls)

 def refill(self,value):
  if self.value + value < 0:
   raise ValueError('Purse value cannot be negative')
  self.value += value
  self.transaction += 1

 def __cmp__(self,other):
  return cmp(self.transaction,other.transaction)

class PURSE_DATE(BigEndianStructure):
 _pack_ = 1
 _fields_ = [('begin_day',c_uint32,5),
             ('begin_month',c_uint32,4),
             ('begin_year',c_uint32,5),
             ('end_day',c_uint32,5),
             ('end_month',c_uint32,4),
             ('end_year',c_uint32,5),
             ('reserve',c_uint32,4),]

 @classmethod
 def from_int(value):
  date = cls()
  memmove(addressof(date),addressof(c_uint32(value)),sizeof(date))
  return date

 def expired(self):
  return date.today() > date(2000 + self.end_year,self.end_month,self.end_year)

 def __str__(self):
  return '%i/%i/%i - %i/%i/%i' % (self.begin_day,self.begin_month,self.begin_year,
                                  self.end_day,self.end_month,self.end_year)
 __repr__ = __str__

class PURSE_STATIC_DATA(DumpableStructure):
 _pack_ = 1
 _fields_ = [('identifier',c_uint8),
             ('version',c_uint8,6),
             ('bitmap',c_uint8,2),
             ('sn',c_uint32),
             ('date',PURSE_DATE),
             ('min_value',c_uint32,24),
             ('mac_alg_id',c_uint32,2),
             ('mac_key_id',c_uint32,6),
             ('mac_auth',c_uint16)]

 @classmethod
 def validate(cls,data):
  if not data.crc16_check(low_endian=0): raise CRCError()
  contract = data.cast(cls)
  if contract.identifier != 0x85: raise DataError()
  return contract

def get_value(card):
 purse_sector = card.sector(num=10,key=5,method='full')
 contract = CONTRACT_A.validate(purse_sector,PURSE_STATIC_DATA,PURSE_DYNAMIC_DATA)
 return contract.dynamic.value

def change_value(card,value):
 event = EVENT_WALLET_OPERATION2(card,value)

 purse_sector = card.sector(num=10,key=5,method='full')
 contract = CONTRACT_A.validate(purse_sector,PURSE_STATIC_DATA,PURSE_DYNAMIC_DATA)

 if not value: return contract.dynamic.value

 contract.dynamic.refill(value)

 event.LocalTransactions = contract.dynamic.transaction
 event.Value = contract.dynamic.value

 try:
  contract.commit(low_endian=0)
  purse_sector.write(blocks=(1,2))

  return contract.dynamic.value
 except Exception as e:
  event.set_error_code(e)
  raise
 finally:
  if event.Amount: event.save(card)

if __name__ == "__main__":
 import transport_card
 card = Reader('\\\\.\\COM2').scan()

 transport_card.validate(card=card)

 get_value(card)

 print card

 print change_value(card=card,value=-100)

 #print card.contract_list