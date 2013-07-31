from interface_basis import DumpableBigEndianStructure,DumpableStructure
from interface import DATE,ByteArray
from mfex import *
from ctypes import *
from transport_card import AIDPIX
from contract import CONTRACT_A

SECTOR = 12
KEY    = 9

class STAFF_VALIDATION_INFO(BigEndianStructure):
 _pack_ = 1
 _fields_ = [
    ('validation_model',c_uint32,2),
    ('validation_status',c_uint32,2),
    ('begin_day',c_uint32,5),
    ('begin_month',c_uint32,4),
    ('begin_year',c_uint32,5),
    ('end_day',c_uint32,5),
    ('end_month',c_uint32,4),
    ('end_year',c_uint32,5)
 ]

 def expired(self):
  return self.end().expired()

 def begin(self):
  return DATE(year = self.begin_year,month = self.begin_month, day = self.begin_day)

 def end(self):
  return DATE(year = self.end_year,month = self.end_month, day = self.end_day)

class CONTRACT0_STATIC(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('identifier',c_uint8),
    ('version',c_uint8,6),
    ('bitmap',c_uint8,2),
    ('aidpix',AIDPIX),
    ('status',c_uint8),
    ('date',STAFF_VALIDATION_INFO),
    ('double_use',c_uint16),
    ('user_status',c_uint8)
 ]

 VALID_ID = 0x87
 VALID_VERSION = 0
 VALID_BITMAP = 0
 VALID_AIDPIX = 0xD010FF

 def to_dict(self,deep = False):
  return {
   'status'              : self.status,
   'user_status'         : self.user_status,
   'validity_begin_date' : self.date.begin(),
   'validity_end_date'   : self.date.end()
  }

 @classmethod
 def validate(cls,data):
  contract = data.cast(cls)
  if contract.identifier != cls.VALID_ID or\
     contract.version != cls.VALID_VERSION or\
     contract.bitmap != cls.VALID_BITMAP or\
     contract.aidpix.value() != cls.VALID_AIDPIX: raise DataError()
  if contract.status != 1: raise StatusError()
  return contract

class CONTRACT0_DYNAMIC(DumpableBigEndianStructure):
 _pack_ = 1
 _fields_ = [
    ('identifier',      c_uint8),
    ('version',         c_uint8,6),
    ('bitmap',          c_uint8,2),
    ('transaction',     c_uint16),
    ('counter',         c_uint64,10),
    ('validation_model',c_uint64,2),
    ('second',          c_uint64,5),
    ('minute',          c_uint64,6),
    ('hour',            c_uint64,5),
    ('day',             c_uint64,5),
    ('month',           c_uint64,4),
    ('year',            c_uint64,5),
    ('_',               c_uint64,22),
    ('__',               c_uint8)
 ]

 def update_checksum(self):
  ByteArray(self).xor_calc()

 def __cmp__(self,other):
  return cmp(self.transaction,other.transaction)

 @classmethod
 def validate(cls,data):
  if not data.xor_check(): raise CRCError()
  return data.cast(cls)

class PROPRIETOR_ASPP_SECTOR1_DATA(DumpableBigEndianStructure):
 _pack_ = 1
 _fields_ = [
    ('identifier',       c_uint64,8),
    ('version',          c_uint64,6),
    ('bitmap',           c_uint64,2),
    ('status',          c_uint64,2),
    ('sector2',         c_uint64,4),
    ('customer_profile',c_uint64,6),
    ('passenger_class', c_uint64,2),
    ('passenger_group', c_uint64,8),
    ('birthday',        c_uint64,14),
    ('language',        c_uint64,4),
    ('doc_type',         c_uint64,8),
    ('doc_series',       ByteArray(3)),
    ('doc_number',       ByteArray(4)),
    ('doc_number_last', c_uint32,8),
    ('sname_len',       c_uint32,6),
    ('name_len',        c_uint32,6),
    ('fname_len',       c_uint32,6),
    ('_',                c_uint32,6),
    ('fio',             c_char*26)
 ]

 def to_dict(self,deep = False):
  return { 'fio': self.format_fio() }

 def format_fio(self):
  a,b = 0,self.sname_len
  c = b + self.name_len
  d = c + self.fname_len
  return '{0} {1} {2}'.format(self.fio[a:b],self.fio[b:c],self.fio[c:d]).decode('cp1251')

 @classmethod
 def validate(cls,data):
  'currently, there is no crc for this data on actual cards'
  return data.cast(cls)

def read(card):
 sector = card.sector(num = SECTOR, key = KEY, method = 'full')
 contract = CONTRACT_A.validate(sector, CONTRACT0_STATIC, CONTRACT0_DYNAMIC)
 return contract.static.to_dict()

def read_personal_info(card):
 personal_sector1 = card.sector(num = 6, key = 21, method = 'full')
 return PROPRIETOR_ASPP_SECTOR1_DATA.validate(personal_sector1.data)
 return result.to_dict()

if __name__ == "__main__":
 from interface import Reader
 import transport_card

 card = Reader().scan()

 transport_card.validate(card=card)

 print read(card)

 print read_personal_info(card)