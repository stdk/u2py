from interface_basis import load,DumpableStructure,DATE,TIME,ByteArray
from contract import DYNAMIC_A
from events import EVENT_CONTRACT_ADD2,EVENT_CONTRACT
from config import term_full_cost,term_half_cost,hall_id
import purse

from ctypes import c_void_p,c_uint64,c_uint32,c_uint16,c_uint8,sizeof,pointer as p,POINTER as P,cast
from datetime import datetime,timedelta
from calendar import monthrange
from mfex import *

#workaround for wrong ctypes behaviour when writing bit fields
term_set_validity       = load('term_set_validity'         ,(c_void_p,c_uint16,c_uint16))
#initializes time contract based on given parameters (see u2.dll source)
term_init               = load('term_init'                 ,(c_void_p,c_void_p))

FULL_COST = term_full_cost
HALF_COST = term_half_cost
STATIC  = 13
DYNAMIC = 14
KEY = 27
ENC = 0x3

# returns an array of tuples with beforehand crafted information
# about business logic of term contract refill.
# Tuple format: (0) begin day, (1) end day, (2) arguments to refill for this case
# Special case with february is being checked here.
def get_refill_table(date,student):
  #student can refill their cards for a half cost but only for a full month
  base_cost = HALF_COST if student else FULL_COST

  #calculate break day based on current month (special case for february)
  x = 13 if date.month == 2 else 14
  #all refillable contracts can be refilled with those parameters
  base = [(  1,  x, {'cost': base_cost, 'next': False }),
          ( 22, 31, {'cost': base_cost, 'next': True} )]
  #only common refillable contracts can be refilled with this
  opt = [(x+1, 21, {'cost': HALF_COST, 'next': False })] if not student else []

  return base + opt

def dim(year,month):
 'abbr. for "days in month". Uses monthrange'
 return monthrange(year,month)[1]

def calc_refill_info(date = None, cost = FULL_COST, next = False):
 if not date: date = datetime.now()
 if next: date = date + timedelta(days = dim(date.year,date.month) - date.day + 1)

 return cost,(
    datetime(year = date.year,month = date.month, day = 1),
    datetime(year = date.year,month = date.month, day = dim(date.year,date.month)),
 )

def available_refill(aid,pix,date = None):
 if not date: date = datetime.now()

 if aid not in [0xD01,0xD21] or \
    pix not in [0x30C]: raise UnsupportedRefillContract()

 is_student = aid == 0xD21

 for a,b,kw in get_refill_table(date,is_student):
  if a <= date.day <= b:
   return calc_refill_info(date,**kw)
 #if there is no record in refill_table for this contract,
 #that satisfies today's conditions, TimeError should be raised
 raise TimeError('This contract cannot be refilled today')

class TERM_DYNAMIC(DumpableStructure):
 _pack_ = 1
 _fields_ = [
  ('validated_date'            ,c_uint32,14),
  ('validated_time'            ,c_uint32,16),
  ('_reserved'                 ,c_uint32,2),
  ('validated_aid'             ,c_uint32,12),
  ('validated_last_place'      ,c_uint32,12),
  ('journey_counter_subway'    ,c_uint32,8),
  ('journey_counter_bus'       ,c_uint8),
  ('journey_counter_tram'      ,c_uint8),
  ('journey_counter_trolleybus',c_uint8),
  ('transaction'               ,c_uint16),
  ('mac_alg_id'                ,c_uint8,2),
  ('mac_key_id'                ,c_uint8,6),
  ('mac'                       ,c_uint16),
 ]

 def __init__(self):
  self.update()

 def update_checksum(self):
  ByteArray(self).crc16_calc(low_endian = 1)

 def to_dict(self,deep = None):
  return {
   'validated_date': DATE(uint16=self.validated_date),
   'validated_time': TIME(uint16=self.validated_time),
   'transaction': self.transaction
  }

 def update(self):
  self.validated_last_place = hall_id
  self.transaction += 1
  self.validated_date = DATE().to_int()
  self.validated_time = TIME().to_int()
  self.update_checksum()
  return self.transaction

 @classmethod
 def validate(cls,data):
  if not data.crc16_check(low_endian=1): raise CRCError()
  return data.cast(cls)

 def __cmp__(self,other):
  return cmp(self.transaction,other.transaction)

class TRANSPORT_TYPE(DumpableStructure):
 _pack_ = 1
 _fields_ = [('flags',c_uint8)]

class PACK_A(DumpableStructure):
 _pack_ = 1
 _fields_ = [
  ('priority'                ,c_uint64,2),
  ('sn'                      ,c_uint64,32),
  ('sale_aid'                ,c_uint64,12),
  ('place'                   ,c_uint64,12),
  ('device_number'           ,c_uint64,6),
 ]

class PACK_B(DumpableStructure):
 _pack_ = 1
 _fields_ = [
  ('autoload_status'           ,c_uint16,2),
  ('validity_duration_unit'    ,c_uint16,4),
  ('validity_duration'         ,c_uint16,10),
 ]

class TERM_STATIC(DumpableStructure):
 _pack_ = 1
 _fields_ = [

  #block0
  ('id'                      ,c_uint8),
  ('version'                 ,c_uint8),
  ('aid'                     ,c_uint32,12),
  ('pix'                     ,c_uint32,12),
  ('status'                  ,c_uint32,8),
  ('pack_a'                  ,PACK_A),
  ('device_type'             ,c_uint8,4),
  ('data_pointer'            ,c_uint8,4),
  ('transport_type'          ,c_uint8),

  #block1
  ('restrict_dow'           ,c_uint64,8),
  ('restrict_timecode'      ,c_uint64,8),
  ('double_use_duration'     ,c_uint64,10),
  ('double_use_duration_unit',c_uint64,4),
  ('max_value'              ,c_uint64,24),
  ('period_journeys'        ,c_uint64,10),
  ('period_journeys_max'    ,c_uint64,10),
  ('validation_model'       ,c_uint64,2),
  ('validity_begin_date'     ,c_uint64,14),
  ('validity_end_date'       ,c_uint64,14),
  ('validity_limit_date'     ,c_uint64,14),
  ('_reserved1'              ,c_uint64,10),

  #block2
  ('pack_b'                     ,PACK_B),
 # ('autoload_status'           ,c_uint16,2),
 # ('validity_duration_unit'    ,c_uint16,4),
 # ('validity_duration'         ,c_uint16,10),
  ('validity_duration_last_use',c_uint64,10),
  ('min_value'                ,c_uint64,24),
  ('autoload_value'           ,c_uint64,24),
  ('_reserved2'                ,c_uint64,6),
  ('min_journey'              ,c_uint32,10),
  ('autoload_journey'         ,c_uint32,10),
  ('max_autoload_period'      ,c_uint32,4),
  ('mac_alg_id'               ,c_uint32,2),
  ('mac_key_id'               ,c_uint32,6),
  ('mac'                      ,c_uint16),
 ]

 VALID_STATUS = 1

 @classmethod
 def validate(cls,data):
  if not data.crc16_check(low_endian=1): raise CRCError(STATIC)
  contract = data.cast(cls)
  #if contract.status != cls.VALID_STATUS: raise StatusError(cls.SECTOR)
  return contract

 def active(self):
  return self.status == self.VALID_STATUS

 def expired(self):
  'takes status into account besides just date'
  return DATE(uint16 = self.validity_end_date).expired() or self.status != self.VALID_STATUS

 def refill(self,begin,end):
  '''
  Tries to change contents of current TERM_STATIC structure to represent
  contract refilled to be active during begin-end period.
  Requires `begin` and `end` parameters to be datetime objects.
  '''
  if DATE(uint16 = self.validity_limit_date).expired():
   raise TimeError('This contract has been expired')
  # if current end_date for contract is greater than proposed end date
  # then TimeError happened
  if self.status == self.VALID_STATUS and \
     DATE(uint16 = self.validity_end_date).to_datetime() >= end:
   raise TimeError('There is no need to refill this contract')

  validity = [
    DATE(date = begin).to_int() if self.expired() else self.validity_begin_date,
    DATE(date = end).to_int()
  ]
  #using native function due to bug in ctypes handling 8-byte long bit fields
  #for now, only changes begin and end dates without meddling with other parameters
  term_set_validity(p(self),*validity)

  self.status = self.VALID_STATUS

 def validity(self):
  return (
    DATE(uint16 = self.validity_begin_date),
    DATE(uint16 = self.validity_end_date),
    DATE(uint16 = self.validity_limit_date)
  )

 def to_dict(self,deep=None):
  '''
  Here we return manually crafted dictionary since most of information in
  contract structure is useless for our purpose.
  '''
  begin,end,limit = self.validity()
  return {
    #'id': self.id,
    'status': self.status,
    #'double_use': {
    #    'duration': self.double_use_duration,
    #    'unit': self.double_use_duration_unit
    #},
    'transport_type': self.transport_type,
    'validity_begin_date': begin,
    'validity_end_date'  : end,
    'validity_limit_date': limit,
  }

def read_static(card):
 sector = card.sector(num=STATIC,key=KEY,mode='dynamic',method='full',enc=ENC)
 static = TERM_STATIC.validate(sector.data)
 return sector,static

def read_dynamic(card):
 sector = card.sector(num=DYNAMIC,key=KEY,mode='dynamic',method='full')

 def restore_callback(fail_block):
  print 'term.read_dynamic.restore_callback',fail_block
  return sector.write_block(fail_block)

 dyn_proxy,dyn_data = DYNAMIC_A.validate(sector.data,TERM_DYNAMIC,
                                         callback = restore_callback)
 return sector,dyn_proxy,dyn_data

def read(card):
 static_sector,static_data = read_static(card)
 result = static_data.to_dict()

 dyn_sector,dyn_proxy,dyn_data = read_dynamic(card)
 result.update(dyn_data.to_dict())

 return result

def refill(card,amount):
 cost,(begin,end) = available_refill(*card.contract())

 if purse.change_value(card,amount) < cost: return 0
 purse.change_value(card,-cost)

 events = []
 static_sector,static_data = read_static(card)
 dyn_sector,dyn_proxy,dyn_data = read_dynamic(card)

 if not static_data.active():
  sell_event = EVENT_CONTRACT(card, Value = cost)
  sell_event.LocalTransactions = dyn_data.update()
  events.append(sell_event)

 static_data.refill(begin,end)

 term_pack = ((end.year - 2000) << 8) + end.month
 refill_event = EVENT_CONTRACT_ADD2(card,TransactionValue=term_pack,Amount=cost)
 refill_event.LocalTransactions = dyn_data.update()
 events.append(refill_event)

 try:
  dyn_proxy.commit(dyn_data,low_endian = 1)
  dyn_sector.write()

  card.auth(static_sector)
  static_sector.data.crc16_calc(low_endian = 1)
  static_sector.write()
 except Exception as e: [event.set_error_code(e) for event in events]; raise
 finally: [event.save(card) for event in events]

 return cost

class TERM_INIT(DumpableStructure):
 _fields_ = [
    ('status',c_uint16),
    ('aid'   ,c_uint16),
    ('pix'   ,c_uint16),
    ('begin' ,DATE),
    ('end'   ,DATE),
    ('limit' ,DATE),
 ]

 STATUS_INACTIVE = 2

 def __init__(self,aid,pix):
  self.status = self.STATUS_INACTIVE
  self.aid = aid
  self.pix = pix

  cost,(begin,end) = available_refill(aid,pix)
  self.begin = DATE(date = begin)
  self.end = DATE(date = end)
  # + 5 years from now
  self.limit = DATE(date = datetime.now() + timedelta(days=365,hours=6) * 5)

def init(card,aid,pix,deposit):
 from transport_card import validate,set_deposit,register_contract,clear

 validate(card)
 set_deposit(card,deposit)

 clear(card,[(STATIC,KEY,'dynamic'),(DYNAMIC,KEY,'dynamic')])

 static_sector = card.sector(num = STATIC, key = 0, enc = ENC,
                             method = 'full', read = False)
 term_init(p(static_sector.data),p(TERM_INIT(aid,pix)))
 static_sector.data.crc16_calc(low_endian = 1)

 event = EVENT_CONTRACT(card, AID = aid, PIX = pix, TransactionType = 0)
 try:
  static_sector.write()
  static_sector.set_trailer(KEY, mode = 'dynamic')

  dynamic_sector = card.sector(num = DYNAMIC, key = 0, enc = 0xFF,
                               method = 'full', read = False)
  dynamic_sector.data.cast(DYNAMIC_A).__init__(TERM_DYNAMIC)
  dynamic_sector.write()
  dynamic_sector.set_trailer(KEY, mode = 'dynamic')

  register_contract(card,STATIC,aid,pix)
 except Exception as e: event.set_error_code(e); raise
 finally: event.save(card)

def remove(card):
 from transport_card import validate,set_deposit,register_contract,clear

 validate(card)

 aidpix = card.contract_list[0] if len(card.contract_list) else 0

 event = EVENT_CONTRACT(card, AID = aidpix >> 12, PIX = aidpix & 0xFFF, TransactionType = 1)
 try:
  clear(card,[(STATIC,KEY,'dynamic'),(DYNAMIC,KEY,'dynamic')])
  register_contract(card,STATIC,0,0)
 except Exception as e: event.set_error_code(e); raise
 finally: event.save(card)

 set_deposit(card,0)

def test():
 from interface import Reader
 import transport_card
 card = Reader().scan()

 #stransport_card.validate(card=card)

 #print read(card)

 init(card,0xD01,0x30C, 700)

def test_available():
 from interface import Reader
 import transport_card

 card = Reader().scan()
 transport_card.validate(card)
 sector,static = read_static(card)

 now = datetime.now()
 days_for_test = [datetime(year = now.year,month = now.month,day = d)
                  for d in xrange(1,monthrange(now.year,now.month)[1]+1)]

 for date in days_for_test:
  ret = available_refill(static.aid,static.pix,date=date)
  if ret:
   print date.strftime("%d/%m/%y"),':',ret[0],[i.strftime("%d/%m/%y") for i in ret[1]]

if __name__ == '__main__':
 #test_available()
 test()
 #x = PACK_A()
 #x.priority = 0xFFFF
 #x.place = 0xFFFF
 #x.sn = 0xFFFF
 #x.sale_aid = 0xFFFF
 #x.device_number = 0xFFFF



