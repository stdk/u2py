from ctypes import c_long,c_char,c_uint8,c_uint16,c_uint32,memmove,c_void_p
from ctypes import cdll,Structure,BigEndianStructure,cast,sizeof,byref,POINTER as P
from datetime import datetime,date
from copy import deepcopy
from gevent.threadpool import ThreadPool
from mfex import ReaderError
import config
import logging

IO_ERROR           = 0x0E000001

DEFAULT_BAUD       = 38400
DEFAULT_PARITY     = 0
DEBUG              = False

Library = cdll.LoadLibrary(config.lib_filename)

def strParams(params):
 return '( {0} )'.format(', '.join( [str(param) for param in params] ))

def load(name,args,res = c_long, time = config.time, library = Library, check_params = None):
 function = library[name]
 function.argtypes = args
 function.restype = res
 def wrapper(*params):
  begin_time = time()

  if check_params is not None:
   ret = check_params(params)
   if ret is not None:
    return ret
  
  ret = None
  try:
   ret = function(*params)
   time_elapsed = time() - begin_time

   logging.debug(' | '.join( ["%6.4f | %08X" % (time_elapsed,ret),name,strParams(params)] ))

   return ret
  except Exception:
   import sys
   import traceback
   logging.error('Exception occured when executing function: %s' % (name,))
   for line in traceback.format_exception(*sys.exc_info()):
    logging.error(line.replace('\n',': '))
  finally:

   if config.reopen_on_io_error and ret == IO_ERROR: #special case for unavailable reader
    #if some function returned IO_ERROR it means its first parameter
    #belongs to Reader class -> should be reopened
    try: params[0].reopen()
    except: pass
    #still, IOError should be raised to notify high level about error
    if config.raise_on_io_error:
     raise IOError('{0}({1}: {2}'.format(name,strParams(params),hex(ret)))

 return wrapper

class BaseReader(c_void_p):
 def __str__(self):
  return '<%X>' % (self.value if self.value else -1)
 __repr__ = __str__

 def __init__(self,path = None,baud = None,parity = None,impl = None,
              explicit_error = False):
  '''
  Reader object can be created even if required port cannot be opened.
  It will try to fix itself afterwards.
  To check current Reader status use 'is_open' method.
  '''
  self.pool = ThreadPool(1)
  self._is_open = False
  if not path:
    kw = config.reader_path[0]
    path,baud,parity,impl = (kw['path'],kw.get('baud',DEFAULT_BAUD),
                             kw.get('parity',DEFAULT_PARITY),
                             kw.get('impl',config.default_impl))
  self.path = path
  self.baud = baud if baud != None else DEFAULT_BAUD
  self.parity = parity if parity != None else DEFAULT_PARITY
  self.impl = impl if impl != None else config.default_impl

  try:
   self.open()
  except ReaderError:
   if explicit_error: raise
   print 'Cannot open Reader on {0}. Will try to fix afterwards...'.format(self.path)

 def is_open(self):
  return self._is_open

 @staticmethod
 def execute_with_context(context, callback, args, kwds):
  with context:
   return callback(*args, **kwds)

 def apply(self, callback, args = None, kwds = None):
  if args == None:
   args = ()
  if kwds == None:
   kwds = {}
  return self.pool.apply(self.execute_with_context, args = (self,callback,args,kwds))

 def __enter__(self):
  self.exc_info = (None,None,None)
  return self

 def __exit__(self, type, value, traceback):
  self.exc_info = (type,value,traceback)
  return True

 def open(self):
  'Opens reader on a given port and raises ReaderError otherwise.'
  if DEBUG: print 'Reader.open',(self.path,self.baud,self.parity,self.impl)
  if not self._is_open:
   if reader_open(self.path,self.baud,self.parity,self.impl,self): raise ReaderError()
   self._is_open = True

 def close(self):
  'Closes current reader connection if it was open before.'
  if self._is_open:
   reader_close(self)
   self._is_open = False

 def reopen(self):
  print 'reopen'
  self.close()
  self.open()

def ByteArray(obj,crc_LE = 1,cache = {},copy = False):
 '''
 >>> x = ByteArray(16)(*xrange(16))
 >>> x
 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
 >>> x.crc16_calc()
 0
 >>> x
 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d cb 78
 >>> x.crc16_check()
 1
 '''
 if not isinstance(obj,int):
  obj_bytearray = cast(byref(obj),P(ByteArray(sizeof(obj)))).contents
  if copy:
   ret = ByteArray(sizeof(obj))()
   obj_bytearray.copy(ret)
   return ret
  return obj_bytearray

 length = obj
 if (length,crc_LE) in cache: return cache[length,crc_LE]
 class ByteArrayTemplate(Structure):
  _fields_ = [('data',c_uint8 * length)]

  def __init__(self,*args):
   [self.data.__setitem__(i,value) for i,value in enumerate(args)]

  def __getitem__(self,index):
   return self.data[index]

  def __setitem__(self,index,value):
   self.data[index] = value

  def __str__(self):
   return ' '.join( '%02x' % i for i in self.data )
  __repr__ = __str__

  def __len__(self):
   return len(self.data)

  def __eq__(self,r):
   return self.data[:] == r[:]

  def __ne__(self,r):
   return not(self.__eq__(r))

  def crc16_check(self,low_endian=crc_LE,size = length):
   return crc16_check(self.data,size,low_endian)

  def crc16_calc(self,low_endian=crc_LE,size = length):
   return crc16_calc(self.data,size,low_endian)

  def xor_check(self):
   return reduce(lambda a,b: a^b,self.data[0:15]) == self.data[15]

  def xor_calc(self):
   self.data[15] = reduce(lambda a,b: a^b,self.data[0:15])

  def cast(self,dst_type):
   return cast(self.data,P(dst_type)).contents

  def copy(self,dst = None):
   if not dst: dst = type(self)()
   memmove(byref(dst),byref(self),min(sizeof(self),sizeof(dst)))
   return dst

 cache[length,crc_LE] = ByteArrayTemplate
 return ByteArrayTemplate

crc16_check             = load('crc16_check'               ,(c_void_p,c_uint32,c_uint8,))
crc16_calc              = load('crc16_calc'                ,(c_void_p,c_uint32,c_uint8,))

reader_open             = load('reader_open'               ,(P(c_char),c_uint32,c_uint8,P(c_char),P(BaseReader),))
reader_close            = load('reader_close'              ,(BaseReader,))

class Dumpable(object):
 '''
 Represents Dumpable mixin that allows classes to be represented as a json
 serialized string or json itself.
 Uses _fields_ class variable in ctypes format and _dumpable_ class variable
 as a list of fields to be serialized from class.
 to_dict method uses deepcopy by default (use deep=False to disable this).
 '''
 def __str__(self):
  return str(self.to_dict(deep=False))
 __repr__ = __str__

 def _get_attribute_value(self,name,default):
  attribute = getattr(self,name,default)
  if callable(attribute): return attribute()
  return attribute

 def to_dict(self,deep=True):
  names = [field_data[0] for field_data in self._fields_] +\
          self.__class__.__dict__.get('_dumpable_',[])
  result = dict([(name,self._get_attribute_value(name,None)) for name in names if not name.startswith('_')])
  return deepcopy(result) if deep else result

 @classmethod
 def validate(cls,data):
  return data.cast(cls)

class DumpableStructure(Structure,Dumpable):
 pass

class DumpableBigEndianStructure(BigEndianStructure,Dumpable):
 pass

class DATE(Structure):
 _pack_ = 1
 _fields_ = [
    ('year' ,c_uint16,5),
    ('month',c_uint16,4),
    ('day'  ,c_uint16,5),
    ('_'    ,c_uint16,2)
 ]

 def __init__(self,uint16 = None,date = None,**kw):
  if uint16 != None:
   value = c_uint16(uint16)
   memmove(byref(self),byref(value),sizeof(self))
  else:
   moment = datetime.now() if not date else date
   self.year,self.month,self.day = moment.year - 2000,moment.month,moment.day
  [setattr(self,key,value) for key,value in kw.iteritems()]

 def __eq__(self,o):
  return self.to_int() == o.to_int()

 def to_int(self):
  integer = c_uint16()
  memmove(byref(integer),byref(self),sizeof(integer))
  return integer.value

 def to_datetime(self):
  return datetime(year = 2000+self.year,month=self.month,day=self.day)

 def expired(self):
  return date.today() > date(2000 + self.year,self.month,self.day)

 def __str__(self):
  return '%02i/%02i/%02i' % (self.day,self.month,self.year)
 __repr__ = __str__

class TIME(Structure):
 _pack_ = 1
 _fields_ = [
    ('hour'    ,c_uint16,5),
    ('minute'  ,c_uint16,6),
    ('second'  ,c_uint16,5) # seconds are stored divided by 2 due to lack of space
 ]

 def __init__(self,uint16 = None,time = None,**kw):
  if uint16 != None:
   value = c_uint16(uint16)
   memmove(byref(self),byref(value),sizeof(self))
  else:
   moment = datetime.now() if not time else time
   self.hour,self.minute,self.second = moment.hour,moment.minute,moment.second/2
  [setattr(self,key,value) for key,value in kw.iteritems()]

 def __eq__(self,o):
  return self.to_int() == o.to_int()

 def to_int(self):
  integer = c_uint16()
  memmove(byref(integer),byref(self),sizeof(integer))
  return integer.value

 def __str__(self):
  return '%02i:%02i:%02i' % (self.hour,self.minute,self.second*2)
 __repr__ = __str__

if __name__ == '__main__':
 import doctest
 doctest.testmod()