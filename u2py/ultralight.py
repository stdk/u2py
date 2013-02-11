from interface import load,lib,Reader
from interface_basis import DumpableStructure,DATE,TIME
from ctypes import c_uint32,c_uint16,c_uint8,POINTER as P,sizeof
from transport_card import ASPP
from datetime import datetime
from calendar import monthrange
from mfex import TimeError,UnsupportedRefillContract
import config

class ULightError(Exception):
 def __init__(self,message):
  super(ULightError,self).__init__(message)

class AIDPIX(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('aid', c_uint16),
    ('pix', c_uint16)
 ]

 def value(self):
  return (self.aid << 12) + self.pix

 def __str__(self):
  return '%X' % (self.value())

 def __init__(self,aid,pix):
  self.aid = aid
  self.pix = pix

class IN_TCULIGHTREAD(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('version'             ,c_uint8),
    ('bitmap'              ,c_uint8),
    ('aidpix'              ,AIDPIX),
    ('aspp'                ,ASPP),
    ('aspp_extra'          ,c_uint16),
    ('sn'                  ,c_uint32),
    ('double_use_status'   ,c_uint8),
    ('transport_type'      ,c_uint8),
    ('year'                ,c_uint8),
    ('month'               ,c_uint8),
    #('period_journeys'     ,c_uint8),
    ('validated_date'      ,DATE),
    ('validated_time'      ,TIME),
    ('place'               ,c_uint16),
    ('device_type'         ,c_uint8),
    ('device_number'       ,c_uint8),
    ('transaction'         ,c_uint16),
    ('active'              ,c_uint8),
 ]

class IN_TCULIGHTACTIV(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('aidpix'              ,AIDPIX),
    ('validated_date'      ,DATE),
    ('validated_time'      ,TIME),
    ('hall_id'             ,c_uint16),
    ('device_type'         ,c_uint16),
    ('device_number'       ,c_uint16),
 ]

 def __init__(self):
  self.aidpix = AIDPIX(0xD01,0x300)
  self.validated_date = DATE()
  self.validated_time = TIME()
  self.hall_id = config.hall_id
  self.device_type = config.device_type
  self.device_number = config.hall_device_id

card_read_ulight         = load(lib,'card_read_ulight'          ,(Reader,P(AIDPIX),P(IN_TCULIGHTREAD),))
card_activate_ulight     = load(lib,'card_activate_ulight'      ,(Reader,P(IN_TCULIGHTACTIV),))

def read(card):
 u = IN_TCULIGHTREAD()
 ret = card_read_ulight(card.reader,AIDPIX(0xD01,0x300),u)

 if ret: raise ULightError('Cannot read Mifare Ultralight contract')

 card.contract_list = [ u.aidpix.value() ]
 card.aspp = u.aspp.copy()

 begin = DATE(date = datetime(year = u.year + 2000,month = u.month,day = 1))
 end = DATE(date = datetime(year = u.year + 2000,month = u.month,day = monthrange(u.year,u.month)[1]))

 return {
    "status": u.active,
    "transaction": u.transaction,
    "validity_limit_date": end,
    "validity_end_date": end,
    "validity_begin_date": begin,
    "validated_time": u.validated_time,
    "validated_date": u.validated_date,
    "transport_type": u.transport_type,
 }

CONTRACT_COST = {
    'D0130B' : (9500 , 4800),
    'D0331B' : (15000, 7500),
    'D0332B' : (15000, 7500),
    'D0334B' : (15000, 7500),
    'D0337B' : (23000,11500),
}

def available_refill(card):
 ulight = read(card)

 if ulight['status']: raise TimeError('There is no need to refill this contract')

 end = ulight['validity_end_date']
 if end.expired(): raise TimeError('This contract has been expired')

 aidpix = '%X' % (card.contract_list[0])
 if aidpix not in CONTRACT_COST: raise UnsupportedRefillContract()

 is_second_half = datetime.now().day >= 15
 cost = CONTRACT_COST[aidpix][is_second_half]
 return cost,(ulight['validity_begin_date'],ulight['validity_end_date'])

def activate(card,amount):
 cost,begin,end = available_refill(card)
 if amount != cost: raise ULightError('Amount received not equals to required')

 aidpix = card.contract_list[0]

 event = EVENT_CONTRACT_ADD2(card)
 event.Amount = cost
 event.TransactionValue = ( end.year << 8 ) + end.month
 event.AID,event.PIX = aidpix >> 12,aidpix & 0xFFF

 u = IN_TCULIGHTACTIV()
 try:
  ret = card_activate_ulight(card.reader,u)
  if ret: raise ULightError('Cannot activate Mifare Ultralight Contract')
 except Exception as e: event.set_error_code(e); raise
 finally: event.save()

if __name__ == '__main__':
 from interface import Reader
 card = Reader().scan()

 print read(card)
 print card

