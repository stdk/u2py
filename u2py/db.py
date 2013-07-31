import sqlite3
from interface_basis import ByteArray
from card_event import CardEvent
from mfex import *
import config

db_connection = sqlite3.connect(config.db_filename,detect_types=sqlite3.PARSE_DECLTYPES,check_same_thread = False)
db_connection.row_factory = sqlite3.Row

def register_type(name,type_obj):
 sqlite3.register_adapter(type_obj, type_obj.__repr__)
 sqlite3.register_converter("ASPP_TEXT", type_obj)

def executescript(script):
 with db_connection as c:
  c.executescript(script)

executescript("PRAGMA journal_mode = WAL;")
#executescript("PRAGMA synchronous = OFF;");

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

class ASPPMixin(object):
 'requires object with iterable |data| attribute at least 8 byte long'
 def __str__(self):
  return ''.join(["%02x" % (i) for i in self.data[7::-1]])

 __repr__ = __str__

 def parse(self,value):
  [self.data.__setitem__(7-i,int(value[2*i:2*i+2],16)) for i in xrange(8)]

 def __init__(self,value = None):
  if value != None: self.parse(value)

 @classmethod
 def convert(cls,value):
  return cls(value)

class ASPP10(ASPPMixin,ByteArray(10)): pass
register_type('ASPP_TEXT',ASPP10)

class Event(object):
 SAVE_QUERY = 'insert into {0}({1}) values({2})'
 LOAD_RANGE_QUERY = 'select * from {0} where id between ? and ?'
 LOAD_LAST_QUERY = 'select * from {0} order by id desc limit 0,1'

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

  # Fields of this specific class + generic id,Time,ErrorCode should be
  # assignable via constructor keyword arguments, as this is the way they'll
  # be deserialized from database.
  # Still, only ErrorCode among those fields should be listed in self.keys,
  # since id and Time should have default values specified in database.
  self.keys = ['ErrorCode'] + [field_data[0] for field_data in self._fields_]
  self.default_keys = ['id','Time']
  [setattr(self,key,kw[key]) for key in self.keys + self.default_keys if key in kw]

 def save(self,card = None):
  # only non-default fields
  fields = ['EventCode'] + self.keys
  values = [getattr(self,field) for field in fields]

  device_transaction = 0
  with db_connection as c:
   cursor = c.cursor()
   query = self.SAVE_QUERY.format(self.TABLE,','.join(fields),('?,'*len(fields))[0:-1])
   cursor.execute(query,values)
   device_transaction = cursor.lastrowid

  if card and not self.ErrorCode:
   try: CardEvent(self,device_transaction).save(card)
   except MFEx: pass

 def card_event_price(self):
  '''
  Default implementation of method to get a price for CardEvent.
  Returns Amount field from underlying structure or 0 if there is no such field.
  '''
  return getattr(self,'Amount',0)

 @classmethod
 def load_last(cls):
  with db_connection as c:
   rows = c.execute(cls.LOAD_LAST_QUERY.format(cls.TABLE))
   events = [cls.registry[row['EventCode']](**row) for row in rows]
   return events[0] if events else None

 @classmethod
 def load(cls,(a,b)):
  with db_connection as c:
   rows = c.execute(cls.LOAD_RANGE_QUERY.format(cls.TABLE),(a,b))
   return [cls.registry[row['EventCode']](**row) for row in rows]





