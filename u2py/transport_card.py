from interface import Card,DumpableStructure,DumpableBigEndianStructure,ByteArray,DATE
from mfex import *
from ctypes import c_uint64,c_uint32,c_uint16,c_uint8,POINTER as P,pointer as p,Structure,cast
from events import EVENT_CONTRACT_ZALOG
from stoplist import Stoplist

class ASPP(ByteArray(8)):
 def __str__(self):
  return ''.join(["%02x" % (i) for i in self.data[0:8]][::-1])

 __repr__ = lambda self: '<' + str(self) + '>'

class EMIT_SECTOR_DATA(DumpableBigEndianStructure):
 _pack_ = 1
 _fields_ = [('version'              ,c_uint8),
             ('provider'             ,ByteArray(5)),
             ('aspp'                 ,ASPP),

             # 8byte block
             ('_aspp_unused'         ,c_uint64,12),
             ('end_date'             ,c_uint64,14),
             ('status'               ,c_uint64,8),
             ('pay_unit'             ,c_uint64,16), # =0x9000
             ('deposit_pay_unit'     ,c_uint64,14), # =0x800

             # two 4-byte blocks
             # note: it's important to use 4-byte base fields for bit fields
             # since ctypes cannot correctly set those bitfields inside 8-byte
             # fields.
             ('_pad'                 ,c_uint32,2),  # =0
             ('deposit'              ,c_uint32,24),
             ('event_log_version'    ,c_uint32,6),
             ('dirtk_pointer'        ,c_uint32,4),
             ('personal_pointer'     ,c_uint32,4),
             ('stoplist_version'     ,c_uint32,16),
             #... mac
 ]

 EDRPOU_KIEV_METRO = [0x00, 0x03, 0x32, 0x89, 0x13]
 VALID_STATUS = 1
 SECTOR = 1
 EXPIRED_MESSAGE = 'Transport card validity has been expired'

 def update_checksum(self):
  cast(p(self),P(ByteArray(48))).contents.crc16_calc(low_endian=0)

 @classmethod
 def validate(cls,data):
  if not data.crc16_check(low_endian=0): raise CRCError(1)

  emit_data = data.cast(cls)
  if emit_data.provider != cls.EDRPOU_KIEV_METRO: raise DataError(1)

  if emit_data.status != cls.VALID_STATUS or emit_data.version != 1: raise StatusError(1)

  # this check is currently disabled
  #if DATE(uint16 = emit_data.end_date).expired(): raise TimeError(cls.EXPIRED_MESSAGE)

  return emit_data

class AIDPIX(Structure):
 _pack_ = 1
 _fields_ = [('a',c_uint8),('b',c_uint8),('c',c_uint8)]

 def __init__(self,aid,pix):
  aidpix = (aid << 12) + pix
  self.a = aidpix >> 16
  self.b = (aidpix >> 8) & 0xFF
  self.c = aidpix & 0xFF

 def value(self):
  return (self.a << 16) + (self.b << 8) + self.c

 def __str__(self):
  return '%02X%02X%02X' % (self.a,self.b,self.c)
 __repr__ = __str__

class DIRTK(DumpableStructure):
 _pack_ = 1
 _fields_ = [('contracts',AIDPIX*15)]

 VALID_CONTRACTS = set([0xd010ff,0xd01100])
 MASK = 0xF00
 TERM = 0x300

 @classmethod
 def is_valid_contract(cls,aidpix):
  return aidpix in cls.VALID_CONTRACTS or (aidpix & cls.MASK) == cls.TERM

 def contract_list(self):
  all_contracts = [contract.value() for contract in self.contracts]
  return filter(self.is_valid_contract,all_contracts)

 def update_checksum(self):
  cast(p(self),P(ByteArray(48))).contents.crc16_calc(low_endian=0)

 @classmethod
 def validate(cls,data):
  #if not data.crc16_check(low_endian=0): raise CRCError(2)
  return data.cast(cls)

def set_deposit(card,value = 700):
 emit_sector = card.sector(num=1,key=2,method='full')
 emit_data = EMIT_SECTOR_DATA.validate(emit_sector.data)
 if emit_data.deposit == value: return

 emit_data.deposit = value
 emit_data.update_checksum()

 event = EVENT_CONTRACT_ZALOG(card,Value = value)

 try:
  emit_sector.write()
 except Exception as e: event.set_error_code(e); raise
 finally: event.save(card)

def register_contract(card,sector_num,aid,pix):
 dirtk_sector = card.sector(num=2,key=3,method='full')
 dirtk = DIRTK.validate(dirtk_sector.data)
 aidpix = AIDPIX(aid,pix)
 dirtk.contracts[sector_num - 1] = aidpix
 dirtk.update_checksum()
 dirtk_sector.write()
 card.contract_list += [aidpix.value()]

class TransportCard(Card):
 def contract(self):
  'returns tuple of aid and pix from first contract in contract_list'
  aidpix = self.contract_list[0]
  return aidpix >> 12, aidpix & 0xFFF

 def __str__(self):
  args = [
    self.type,
    self.sn,
    getattr(self,'aspp',''),
    getattr(self,'end_date',''),
    getattr(self,'deposit',''),
    [hex(i)[2:] for i in getattr(self,'contract_list','')]
  ]
  return '[{0}:{1}:{2}][{3}][{4}]{5}'.format(*args)

 def validate(self):
  emit_sector = self.sector(num=1,key=2,method='full')
  emit_data = EMIT_SECTOR_DATA.validate(emit_sector.data)

  if emit_data.aspp in Stoplist(): raise StoplistError()

  dirtk_sector = self.sector(num=2,key=3,method='full')
  dirtk = DIRTK.validate(dirtk_sector.data)

  self.aspp = emit_data.aspp.copy()
  self.contract_list = dirtk.contract_list()
  self.deposit = emit_data.deposit
  self.end_date = DATE(uint16 = emit_data.end_date)

def validate(card):
 card.__class__ = TransportCard
 card.validate()

if __name__ == "__main__":
 from interface import Reader,Sector

 card = Reader().scan()
 validate(card)
 print card

 #set_deposit(card,700)


