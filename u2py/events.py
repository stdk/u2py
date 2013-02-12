from interface_basis import DumpableStructure
from ctypes import c_uint8,c_uint16,c_uint32,c_uint64,sizeof
from db import Event,ASPP
import config

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

@Event.register
class T_EVENT_227(Event,DumpableStructure):
 EventCode = 227
 _pack_ = 1
 _fields_ = [
   ('EventVer',               c_uint8),
   ('UserCardType',           c_uint16),
   ('BitMapVer',              c_uint8),
   ('UserCardSN',             c_uint64),
   ('UserASPPSN',             ASPP),
   ('AID',                    c_uint16),
   ('PIX',                    c_uint16),
   ('Value',                  c_uint32),#ContractValueBegin
   ('FinalValue',             c_uint16),#ContractValueEnd
   ('LocalTransactions',      c_uint16),#ContractTransactionNumber
 ]
 
@Event.register
class T_EVENT_228(Event,DumpableStructure):
 EventCode = 228
 _pack_ = 1
 _fields_ = [
  ('EventVer',               c_uint8),
  ('AID',                    c_uint16),
  ('PIX',                    c_uint16),
  ('LocalTransactions',      c_uint32),
 ]

@Event.register
class T_EVENT_100(Event,DumpableStructure):
 EventCode = 100
 _pack_ = 1
 _fields_ = [
  ('EventVer',               c_uint8),
  ('AID',                    c_uint8),
  ('PIX',                    c_uint8),
 ]

@Event.register
class EVENT_WALLET_OPERATION2(Event,DumpableStructure):
 'event 214, sizeof() = 39'
 EventCode = 214
 _pack_ = 1
 _fields_ = [
    ('EventVer',          c_uint8),
    ('UserCardType',      c_uint16),
    ('BitMapVer',         c_uint8),
    ('UserCardSN',        c_uint64),
    ('UserASPPSN',        ASPP),
    ('CashCardSN',        c_uint32),
    ('TransactionType',   c_uint8),
    ('Amount',            c_uint32),
    ('Value',             c_uint32),#PurseValue
    ('LocalTransactions' ,c_uint16),#PurseTransactionNumber
    ('GlobalTransactions',c_uint16) #TCTransactionNumber
 ]

 def __init__(self,card=None,value=None,**kw):
  Event.__init__(self,**kw)
  self.CashCardSN = config.cash_card_sn
  if card: fill_event_from_card(self,card)
  if value:
   self.TransactionType = 0 if value >= 0 else 3
   self.Amount = abs(value)

@Event.register
class EVENT_CONTRACT_ADD2(Event,DumpableStructure):
 'event 226 sizeof() = 45'
 EventCode = 226
 _pack_ = 1
 _fields_ = [
    ('EventVer',               c_uint8),
    ('CashCardSN',             c_uint32),
    ('UserCardType',           c_uint16),
    ('BitMapVer',              c_uint8),
    ('UserCardSN',             c_uint64),
    ('UserASPPSN',             ASPP),
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
  Event.__init__(self,**kw)
  if card: fill_event_from_card(self,card)

@Event.register
class EVENT_CONTRACT(Event,DumpableStructure):
 'event 230 sizeof() = 40'
 EventCode = 230
 _pack_ = 1
 _fields_ = [
    ('EventVer',            c_uint8),
    ('UserCardSN',          c_uint64),
    ('UserASPPSN',          ASPP),
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
  Event.__init__(self,**kw)
  if card: fill_event_from_card(self,card)

@Event.register
class EVENT_CONTRACT_ZALOG(Event,DumpableStructure):
 'event 215 sizeof() = 30'
 EventCode = 215
 _pack_ = 1
 _fields_ = [
    ('EventVer',            c_uint8),
    ('CashCardSN',          c_uint32),
    ('UserCardSN',          c_uint64),
    ('UserASPPSN',          ASPP),
    ('TransactionType',     c_uint8), #CodeEvent
    ('Value',               c_uint32),#MortValue
    ('GlobalTransactions',  c_uint16) #TCTransactionNumber
 ]

 def card_event_price(self):
  return self.Value

 def __init__(self, card = None, **kw):
  Event.__init__(self,**kw)
  if card: fill_event_from_card(self,card)

if __name__ == '__main__':
 import config
 config.cash_card_sn = 100

 import events
 from interface import Reader
 import transport_card

 card = Reader().scan()
 transport_card.validate(card)

 x = events.EVENT_CONTRACT_ZALOG(card)
 print x
 x.save(card)

 print events.Event.load_last()





