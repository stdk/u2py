import sqlite3
from interface import ByteArray,c_uint8
from card_event import CardEvent
from mfex import *
import config

db_connection = sqlite3.connect(config.db_filename,detect_types=sqlite3.PARSE_DECLTYPES)
db_connection.row_factory = sqlite3.Row

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

MIFARE_STANDARD = 0x4
MIFARE_ULTRALIGHT = 0x44

create_query = """
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
"""

class ASPP(ByteArray(10)):
 #_fields_ = [('data',c_uint8*10)]

 def __repr__(self):
  return ''.join(["%02x" % (i) for i in self.data[0:8]][::-1])

 @classmethod
 def convert(cls,value):
  ret = cls()
  [ret.data.__setitem__(7-i,int(value[2*i:2*i+2],16)) for i in xrange(8)]
  return ret

sqlite3.register_adapter(ASPP, ASPP.__repr__)
sqlite3.register_converter("ASPP_TEXT", ASPP.convert)

with db_connection as c:
 c.executescript(create_query)

class Event(object):
 SAVE_QUERY = 'insert into events({0}) values({1})'
 LOAD_RANGE_QUERY = 'select * from events where id between ? and ?'
 LOAD_LAST_QUERY = 'select * from events order by id desc limit 0,1'

 registry = {}

 @classmethod
 def register(cls,event_class):
  cls.registry[event_class.EventCode] = event_class
  return event_class

 def set_error_code(self,ex):
  self.ErrorCode = error_by_exception.get(ex.__class__,WRITE)

 def __init__(self,**kw):
  self.id = 0
  self.Time = ''
  self.ErrorCode = 0
  self.keys = ['ErrorCode'] + [field_data[0] for field_data in self._fields_]

  #for key in self.keys + ['Time','id']:
  # if key in kw:
  #  print key,kw[key],kw[key].__class__,getattr(self,key).__class__
  #  setattr(self,key,kw[key])

  [setattr(self,key,kw[key]) for key in self.keys + ['Time','id'] if key in kw]

 def save(self,card = None):
  fields = ['EventCode'] + self.keys
  values = [getattr(self,field) for field in fields]

  device_transaction = 0
  with db_connection as c:
   cursor = c.cursor()
   query = self.SAVE_QUERY.format(','.join(fields),('?,'*len(fields))[0:-1])
   cursor.execute(query,values)
   device_transaction = cursor.lastrowid

  if card and not self.ErrorCode:
   try: CardEvent(self,device_transaction).save(card)
   except MFEx: pass

 def card_event_price(self):
  '''
  Default implementation of method to get a price for CardEvent.
  Returns Amount field from underlying structure or 0 if there is no suck field.
  '''
  return getattr(self,'Amount',0)

 @classmethod
 def load_last(cls):
  with db_connection as c:
   row = c.execute(cls.LOAD_LAST_QUERY).next()
   return cls.registry[row['EventCode']](**row)

 @classmethod
 def load(cls,(a,b)):
  with db_connection as c:
   rows = c.execute(cls.LOAD_RANGE_QUERY,(a,b))
   return [cls.registry[row['EventCode']](**row) for row in rows]