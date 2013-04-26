from interface import Card,DumpableStructure,DumpableBigEndianStructure,ByteArray,DATE
from mfex import *
from ctypes import c_uint64,c_uint32,c_uint16,c_uint8,POINTER as P,pointer as p,Structure,cast,sizeof
from events import EVENT_CONTRACT_ZALOG
from stoplist import Stoplist
from datetime import datetime,timedelta
from mfex import CardError,SectorReadError,SectorWriteError

DEPOSIT_VALUE = 700

EMIT_SECTOR = 1
EMIT_KEY    = 2
DIRTK_SECTOR = 2
DIRTK_KEY    = 3

class ASPPMixin(object):
 'requires object with iterable data attribute with at least 8 length'
 def __str__(self):
  return ''.join(["%02x" % (i) for i in self.data[8:0:-1]])

 __repr__ = lambda self: '<' + str(self) + '>'

 def parse(self,value):
  [self.data.__setitem__(7-i,int(value[2*i:2*i+2],16)) for i in xrange(8)]

 def __init__(self,value = None):
  if value != None: self.parse(value)

 @classmethod
 def convert(cls,value):
  return cls(value)

class ASPP(ASPPMixin,ByteArray(8)): pass

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
             ('_'                    ,c_uint32,8),
             ('_unused'              ,ByteArray(18)) # mac included
 ]

 EDRPOU_KIEV_METRO = [0x00, 0x03, 0x32, 0x89, 0x13]
 VALID_STATUS = 1
 SECTOR = 1
 EXPIRED_MESSAGE = 'Transport card validity has been expired'

 def __init__(self, aspp):
  self.version = 1
  self.provider[:] = self.EDRPOU_KIEV_METRO

  self.aspp = ASPP.convert(aspp)
  self.pay_unit = 0x9000
  self.deposit_pay_unit = 0x800
  limit = datetime.now() + timedelta(days=365,hours=6) * 5 # + 5 years from now
  self.end_date = DATE(date = limit).to_int()

  self.status = 1
  self.dirtk_pointer = DIRTK_SECTOR
  self.personal_pointer = 6
  self.event_log_version = 0

  self.update_checksum()

 def update_checksum(self):
  ByteArray(self).crc16_calc(low_endian=0)

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
 _fields_ = [
    ('contracts',AIDPIX*15),
    ('mac',ByteArray(3))
 ]

 VALID_CONTRACTS = set([0xd010ff,0xd01100])
 MASK = 0xF00
 TERM = 0x300

 def __init__(self):
  pass

 @classmethod
 def is_valid_contract(cls,aidpix):
  return aidpix in cls.VALID_CONTRACTS or (aidpix & cls.MASK) == cls.TERM

 def contract_list(self):
  all_contracts = [contract.value() for contract in self.contracts]
  return filter(self.is_valid_contract,all_contracts)

 def update_checksum(self):
  ByteArray(self).crc16_calc(low_endian=0)

 @classmethod
 def validate(cls,data):
  #if not data.crc16_check(low_endian=0): raise CRCError(2)
  return data.cast(cls)

class DepositError(Exception):
 def __init__(self,message):
  super(DepositError,self).__init__(message)

def set_deposit(card,value = None):
 if value == None: value = DEPOSIT_VALUE
 emit_sector = card.sector(num=1,key=2,method='full')
 emit_data = EMIT_SECTOR_DATA.validate(emit_sector.data)

 if emit_data.deposit == value: return

 if value > 0 and emit_data.deposit > 0:
  raise DepositError('Deposit for this transport card already exists')

 if value == 0 and emit_data.deposit != 0:
  value = -emit_data.deposit

 emit_data.deposit += value
 emit_data.update_checksum()

 event = EVENT_CONTRACT_ZALOG(card,value = value)

 try:
  emit_sector.write()
 except Exception as e: event.set_error_code(e); raise
 finally: event.save(card)

def register_contract(card,sector_num,aid,pix):
 dirtk_sector = card.sector(num=DIRTK_SECTOR,key=DIRTK_KEY,method='full')
 dirtk = DIRTK.validate(dirtk_sector.data)
 aidpix = AIDPIX(aid,pix)
 dirtk.contracts[sector_num - 1] = aidpix
 dirtk.update_checksum()
 dirtk_sector.write()
 if aid and pix: card.contract_list += [aidpix.value()]

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
  emit_sector = self.sector(num=EMIT_SECTOR,key=EMIT_KEY,method='full')
  emit_data = EMIT_SECTOR_DATA.validate(emit_sector.data)

  if emit_data.aspp in Stoplist(): raise StoplistError()

  dirtk_sector = self.sector(num=DIRTK_SECTOR,key=DIRTK_KEY,method='full')
  dirtk = DIRTK.validate(dirtk_sector.data)

  self.aspp = emit_data.aspp.copy()
  self.contract_list = dirtk.contract_list()
  self.deposit = emit_data.deposit
  self.end_date = DATE(uint16 = emit_data.end_date)

def init(card,aspp):
 from purse import init as purse_init
 from card_event import init as card_event_init

 emit_sector = card.sector(num=EMIT_SECTOR,key=0,method='full',read=False)
 emit_sector.data.cast(EMIT_SECTOR_DATA).__init__(aspp)
 emit_sector.write()
 emit_sector.set_trailer(EMIT_KEY)

 dirtk = DIRTK()
 dirtk_sector = card.sector(num=DIRTK_SECTOR,key=0,method='full',read=False)
 dirtk_sector.data = ByteArray(dirtk)
 dirtk_sector.write()
 dirtk_sector.set_trailer(DIRTK_KEY)

 purse_init(card)
 card_event_init(card)

def clear(card,sectors):
 def clear_sector(num,key,mode):
  try:
   sector = card.sector(num=num,key=key,mode=mode,method='full',read = False)
   sector.write()
   if key: sector.set_trailer(0,mode='static')
   return True
  except (SectorReadError,SectorWriteError):
   card.reset()
   if key: return clear_sector(num,0,'static')
   else: raise
 [clear_sector(*args) for args in sectors]

def validate(card):
 card.__class__ = TransportCard
 card.validate()

if __name__ == "__main__":
 from interface import Reader

 card = Reader().scan()
 #validate(card)
 #print card

 #print clear(card)
 init(card,'0123456789ABCDEF',DEPOSIT_VALUE)

 #set_deposit(card,700)


