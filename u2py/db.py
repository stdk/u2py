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

 # Fields in this list should have default values in database
 # i.e. they acquire their values during insert to db.
 # Being specified in this list means those keys aren't listed in structure fields.
 DEFAULT_KEYS = []

 # Those field don't have default database values and should be explicitly
 # set some value (at least to None, as Event.__init__ does).
 # Being specified in this list means those keys aren't listed in structure fields.
 EXTRA_KEYS = []
 registry = {}

 @classmethod
 def register(cls,event_class):
  cls.registry[event_class.EventCode] = event_class
  return event_class

 def set_error_code(self,ex):
  self.ErrorCode = error_by_exception.get(ex.__class__,WRITE)

 def __init__(self,**kw):
  [setattr(self,key,None) for key in self.EXTRA_KEYS + self.DEFAULT_KEYS]

  # Fields of this specific class + EXTRA_KEYS + DEFAULT_KEYS should be
  # assignable via constructor keyword arguments, as this is the way they'll
  # be deserialized from database, but DEFAULT_KEYS should not inserted into db,
  # since there is default values for them there.
  self.keys = [field_data[0] for field_data in self._fields_] + self.EXTRA_KEYS
  [setattr(self,key,kw[key]) for key in kw if key in self.keys + self.DEFAULT_KEYS]

 def save(self,card = None):
  # only non-default fields
  # EventCode is a special case class field, that should be explicitly set in Event descendants
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





