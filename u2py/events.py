from interface_basis import DumpableStructure,ByteArray
from ctypes import c_uint8,c_uint16,c_uint32,c_uint64,sizeof
from db import Event,ASPPMixin,executescript,register_db_type
from card_event import CardEvent
from mfex import *
import config

executescript("""
CREATE TABLE if not exists events (
    id INTEGER PRIMARY KEY default (null),
    Time TEXT DEFAULT (datetime(current_timestamp, 'localtime')),
    EventCode INTEGER,
    ErrorCode INTEGER,
    EventVer INTEGER,
    BitMapVer INTEGER,
    UserCardType INTEGER,
    UserCardSN INTEGER,
    UserASPPSN ASPP_TEXT,
    CashCardSN INTEGER,
    CashASPPSN ASPP_TEXT,
    AID INTEGER,
    PIX INTEGER,
    TransactionType INTEGER,
    TransactionValue INTEGER,
    Value INTEGER,
    Amount INTEGER,
    LocalTransactions INTEGER,
    GlobalTransactions INTEGER
);
""")

@register_db_type('ASPP_TEXT')
class ASPP10(ASPPMixin,ByteArray(10)): pass

def fill_event_from_card(event,card):
 event.CashCardSN = config.cash_card_sn
 event.EventVer = 1
 event.BitMapVer = 1
 event.UserCardType = card.type
 event.UserCardSN = card.sn.sn8()
 card.aspp.copy(dst = event.UserASPPSN)
 if len(card.contract_list):
  contract = card.contract_list[0]
  event.AID = contract >> 12;
  event.PIX = contract & 0xFFF;

NO_RESOURCE    = 1
CONTRACT_TIME  = 2
UNKNOWN_CARD   = 3
READ           = 4
WRITE          = 5
STATUS         = 6
TIMEOUT        = 7
NO_CONTRACT    = 8
RESOURCE_LIMIT = 9

error_by_exception = {
    SectorWriteError: WRITE,
    SectorReadError:  READ,
    TimeError:        CONTRACT_TIME,
    CRCError:         NO_CONTRACT,
    DataError:        NO_CONTRACT,
    StatusError:      STATUS,
    ValueError:       NO_RESOURCE
 }

# base storage class defines its table name and registry for its events
# when there is not registry defined, base class (i.e. Event) registry
# will be used
class ServiceEvent(Event):
 _table_ = 'events'
 _default_ = ['id','Time']
 _extra_   = ['ErrorCode']
 registry = {}

 def __init__(self,*args,**kw):
  self.ErrorCode = 0
  super(ServiceEvent,self).__init__(*args,**kw)

 def set_error_code(self,ex):
  self.ErrorCode = error_by_exception.get(ex.__class__,WRITE)

 def save(self,card = None):
  device_transaction = super(ServiceEvent,self).save()

  if card and not getattr(self,'ErrorCode',None):
   try: CardEvent(self,device_transaction).save(card)
   except MFEx: pass

  return device_transaction


@ServiceEvent.register
class EVENT_WALLET_OPERATION2(ServiceEvent,DumpableStructure):
 'event 214, sizeof() = 39'
 EventCode = 214
 _pack_ = 1
 _fields_ = [
    ('EventVer',          c_uint8),
    ('UserCardType',      c_uint16),
    ('BitMapVer',         c_uint8),
    ('UserCardSN',        c_uint64),
    ('UserASPPSN',        ASPP10),
    ('CashCardSN',        c_uint32),
    ('TransactionType',   c_uint8),
    ('Amount',            c_uint32),
    ('Value',             c_uint32),#PurseValue
    ('LocalTransactions' ,c_uint16),#PurseTransactionNumber
    ('GlobalTransactions',c_uint16) #TCTransactionNumber
 ]

 def __init__(self,card=None,amount=None,**kw):
  if card: fill_event_from_card(self,card)
  if amount:
   self.TransactionType = 0 if amount >= 0 else 3
   self.Amount = abs(amount)
  Event.__init__(self,**kw)

@ServiceEvent.register
class EVENT_CONTRACT_ADD2(ServiceEvent,DumpableStructure):
 'event 226 sizeof() = 45'
 EventCode = 226
 _pack_ = 1
 _fields_ = [
    ('EventVer',               c_uint8),
    ('CashCardSN',             c_uint32),
    ('UserCardType',           c_uint16),
    ('BitMapVer',              c_uint8),
    ('UserCardSN',             c_uint64),
    ('UserASPPSN',             ASPP10),
    ('AID',                    c_uint16),
    ('PIX',                    c_uint16),
    ('Value',                  c_uint32),#ContractValue
    ('TransactionValue',       c_uint16),
    ('TransactionType',        c_uint8), #CodeEvent
    ('Amount',                 c_uint32),
    ('LocalTransactions',      c_uint16),#ContractTransactionNumber_Metro
    ('GlobalTransactions',     c_uint16) #TCTransactionNumber
 ]

 def card_event_price(self):
  return self.TransactionValue

 def __init__(self, card = None, **kw):
  if card: fill_event_from_card(self,card)
  Event.__init__(self,**kw)

@ServiceEvent.register
class EVENT_CONTRACT(ServiceEvent,DumpableStructure):
 'event 230 sizeof() = 40'
 EventCode = 230
 _pack_ = 1
 _fields_ = [
    ('EventVer',            c_uint8),
    ('UserCardSN',          c_uint64),
    ('UserASPPSN',          ASPP10),
    ('CashCardSN',          c_uint32),
    ('TransactionType',     c_uint8), #CodeEvent
    ('AID',                 c_uint16),
    ('PIX',                 c_uint16),
    ('Value',               c_uint32),#ContractValue
    ('TransactionValue',    c_uint32),#ContractCopyID
    ('LocalTransactions',   c_uint16),#ContractTransactionNumber_Metro
    ('GlobalTransactions',  c_uint16) #TCTransactionNumber
 ]

 def card_event_price(self):
  return self.Value

 def __init__(self, card = None, **kw):
  if card: fill_event_from_card(self,card)
  Event.__init__(self,**kw)

@ServiceEvent.register
class EVENT_CONTRACT_ZALOG(ServiceEvent,DumpableStructure):
 'event 215 sizeof() = 30'
 EventCode = 215
 _pack_ = 1
 _fields_ = [
    ('EventVer',            c_uint8),
    ('CashCardSN',          c_uint32),
    ('UserCardSN',          c_uint64),
    ('UserASPPSN',          ASPP10),
    ('TransactionType',     c_uint8), #CodeEvent
    ('Value',               c_uint32),#MortValue
    ('GlobalTransactions',  c_uint16) #TCTransactionNumber
 ]

 def card_event_price(self):
  return self.Value

 def __init__(self, card = None,value = None,**kw):
  if value != None:
   self.TransactionType = 3 if value < 0 else 0
   self.Value = abs(value)
  if card: fill_event_from_card(self,card)
  Event.__init__(self,**kw)

@ServiceEvent.register
class EVENT_ENCASHMENT(ServiceEvent,DumpableStructure):
 EventCode = 231
 _pack_ = 1
 _fields_ = [
    ('EventVer',            c_uint8),
    ('CashCardSN',          c_uint32),
    ('CashASPPSN',          ASPP10),
    ('Amount',              c_uint32),
    ('Value',               c_uint32) # TagAmount
 ]

 def __init__(self,**kw):
  self.EventVer = 2
  self.CashCardSN = config.cash_card_sn
  self.CashASPPSN = ASPP10(config.cash_card_aspp)
  Event.__init__(self,**kw)

if __name__ == '__main__':
 import config
 config.cash_card_sn = 100

 import events
 from interface import Reader
 import transport_card

 card = Reader().scan()
 transport_card.validate(card)

 x = events.EVENT_ENCASHMENT(Amount = 1000)
 print x
 x.save()

 print events.ServiceEvent.load_last()

